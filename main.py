import logging
import os
import re

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View
from dotenv import load_dotenv

from core import (
    GLOBAL_DAILY_LIMIT,
    OFFICIAL_GUILD_ID,
    ask_hybrid_ai,
    check_and_update_dual_usage,
    feed_cat_canned,
    get_channel_lock,
    get_quota_status,
    get_user_affection_score,
    init_usage_db,
    is_safety_valve_triggered,
    keep_alive,
    set_channel_lock,
    update_user_affection_and_get_action,
)

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("discord_cat_bot")

GUILD_OBJECT = discord.Object(id=OFFICIAL_GUILD_ID)

intents = discord.Intents.default()
intents.message_content = True


class AIChatBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        try:
            # 先確保新伺服器指令成功註冊，再移除舊全域指令；若 guild sync
            # 失敗，舊指令仍保留，不會因啟動失敗而讓整個指令清單消失。
            synced_guild = await self.tree.sync(guild=GUILD_OBJECT)
            logger.info("伺服器指令同步完成：%s", [command.name for command in synced_guild])

            # 所有目前指令皆為 guild-scoped；在 guild sync 成功後，清除同一個
            # Discord Application 過去留下的全域指令，不影響其他 App。
            self.tree.clear_commands(guild=None)
            removed_global = await self.tree.sync()
            logger.info("全域舊指令清除／同步完成，目前全域指令數：%s", len(removed_global))
        except Exception:
            logger.exception("斜線指令同步失敗")


bot = AIChatBot()


async def _reply_targets_bot(message: discord.Message) -> bool:
    """回覆訊息不一定在 discord.py 快取中；必要時從頻道抓取原訊息。"""
    reference = message.reference
    if reference is None or reference.message_id is None:
        return False

    resolved = reference.resolved
    if isinstance(resolved, discord.Message):
        return bot.user is not None and resolved.author.id == bot.user.id

    try:
        original = await message.channel.fetch_message(reference.message_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return False
    return bot.user is not None and original.author.id == bot.user.id


def _split_discord_message(text: str, limit: int = 1900) -> list[str]:
    """保守分割訊息，讓回覆留在 Discord 2000 字元限制內。"""
    remaining = str(text).strip()
    chunks = []
    while len(remaining) > limit:
        split_at = remaining.rfind("\n", 0, limit)
        if split_at < limit // 2:
            split_at = remaining.rfind(" ", 0, limit)
        if split_at < limit // 2:
            split_at = limit
        chunk = remaining[:split_at].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks or ["本喵暫時沒有可顯示的回覆喵。"]


async def _send_reply(message: discord.Message, text: str):
    for chunk in _split_discord_message(text):
        await message.reply(chunk, mention_author=False)


# ==================== Help 下拉選單 ====================
class HelpSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="貓貓對話模式", description="了解標記與回覆對話方法", emoji="🐱", value="basic"),
            discord.SelectOption(label="雙重限額與安全閥", description="查看個人、全服額度與自動安全閥", emoji="📊", value="quota"),
            discord.SelectOption(label="管理員功能鎖", description="查看管理員文字頻道鎖定", emoji="🛠️", value="admin"),
        ]
        super().__init__(placeholder="請選擇你想查看的說明指南...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        embed = discord.Embed(color=0x5865F2)

        if selected == "basic":
            embed.title = "🐱 貓貓助理 - 對話與功能限制"
            embed.description = (
                "想要跟本喵說話，必須使用以下兩種方法喵嗚❤：\n\n"
                "**1. 直接標記（@標記）對話**\n在頻道輸入 `@貓貓AI [訊息]`。\n\n"
                "**2. 直接回覆（Reply）對話**\n使用 Discord 的「回覆」功能直接打字發送喵！\n\n"
                "*提示：每日個人或全服額度用完時，本喵會回覆 `MEOW`。*"
            )
        elif selected == "quota":
            embed.title = "📊 雙重配額與動態安全閥機制"
            embed.description = (
                "• **個人限制**：每人每天 40 次。\n"
                f"• **全服限制**：每天 {GLOBAL_DAILY_LIMIT:,} 次。\n"
                "• **安全閥**：全服剩餘額度低於或等於個人剩餘額度時，暫停好感度動作與餵食功能。"
            )
        else:
            embed.title = "🛠️ 伺服器管理員限制功能"
            embed.description = "使用 `/設定` 選擇允許本喵聊天的文字頻道；限制啟用後，本喵只在該頻道回覆。"

        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpSelect())


# ==================== 斜線指令：僅註冊於官方伺服器 ====================
@bot.tree.command(
    name="help",
    description="查看貓貓對話、額度與管理員設定說明",
    guild=GUILD_OBJECT,
)
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🐾 智慧貓貓 AI 助理 - 幫助中心",
        description="請點擊下方的下拉選單查看說明喵嗚❤：",
        color=0x5865F2,
    )
    await interaction.response.send_message(embed=embed, view=HelpView(), ephemeral=True)


@bot.tree.command(
    name="設定",
    description="【管理員專用】設定貓貓只能在哪個頻道說話",
    guild=GUILD_OBJECT,
)
@app_commands.describe(頻道="選擇允許貓貓說話的文字頻道")
@app_commands.checks.has_permissions(administrator=True)
async def set_channel(interaction: discord.Interaction, 頻道: discord.TextChannel):
    set_channel_lock(頻道.id)
    await interaction.response.send_message(
        f"設定成功喵！本喵現在只能在 {頻道.mention} 說話了喵！",
        ephemeral=True,
    )


@bot.tree.command(
    name="查看當前額度",
    description="查詢個人與全服剩餘額度及安全閥狀態",
    guild=GUILD_OBJECT,
)
async def check_quota(interaction: discord.Interaction):
    global_remaining, user_remaining, _, _ = get_quota_status(interaction.user.id)
    affection = get_user_affection_score(interaction.user.id)
    valve_triggered = is_safety_valve_triggered(interaction.user.id)

    valve_status = (
        "🔴 已觸發（罐罐與好感度動作暫停）"
        if valve_triggered
        else "🟢 正常運作"
    )
    affection_status = "高冷傲嬌 🧊" if affection < 40 else "溫柔親近 🌸" if affection < 100 else "超級黏人 💗"

    embed = discord.Embed(title="📊 貓貓額度與安全閥狀態", color=0x2ECC71)
    embed.add_field(name="👤 個人今日剩餘額度", value=f"`{user_remaining} / 40` 次", inline=True)
    embed.add_field(
        name="🌐 全服今日剩餘額度",
        value=f"`{global_remaining:,} / {GLOBAL_DAILY_LIMIT:,}` 次",
        inline=True,
    )
    embed.add_field(name="🔒 安全閥", value=valve_status, inline=False)
    embed.add_field(name="🐾 個人好感度", value=f"`{affection}` 點（{affection_status}）", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
    name="餵食",
    description="餵食貓貓罐罐，提升好感度並補充全服額度",
    guild=GUILD_OBJECT,
)
async def feed_cat(interaction: discord.Interaction):
    success, reply_text = feed_cat_canned(interaction.user.id)
    await interaction.response.send_message(reply_text, ephemeral=not success)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        message = "這個指令只有伺服器管理員可以使用喵。"
    else:
        logger.error("斜線指令錯誤", exc_info=(type(error), error, error.__traceback__))
        message = "指令執行時發生錯誤，請通知管理員查看 Render log 喵。"

    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except discord.HTTPException:
        logger.exception("無法向使用者回報斜線指令錯誤")


# ==================== @提及與直接回覆 ====================
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    try:
        if message.guild is None:
            return
        if message.guild.id != OFFICIAL_GUILD_ID:
            logger.debug(
                "忽略非目標伺服器訊息：收到 guild_id=%s，預期=%s",
                message.guild.id,
                OFFICIAL_GUILD_ID,
            )
            return

        is_mentioned = bot.user is not None and bot.user in message.mentions
        is_reply = await _reply_targets_bot(message)
        if not is_mentioned and not is_reply:
            return

        locked_channel_id = get_channel_lock()
        if locked_channel_id is not None and message.channel.id != locked_channel_id:
            logger.info(
                "忽略觸發訊息：頻道 %s 不符合已設定的鎖定頻道 %s",
                message.channel.id,
                locked_channel_id,
            )
            return

        user_id = message.author.id
        clean_content = message.content
        if bot.user is not None:
            clean_content = re.sub(rf"<@!?{bot.user.id}>", "", clean_content)
        clean_content = clean_content.strip()

        if is_mentioned and not clean_content and not is_reply:
            await message.reply(
                "👀 找本喵嗎？直接 `@我` 或回覆本喵的訊息來聊天喵！可以使用 `/查看當前額度` 檢查剩餘次數！",
                mention_author=False,
            )
            return

        allowed, _, _ = check_and_update_dual_usage(user_id)
        if not allowed:
            await message.reply("MEOW", mention_author=False)
            return

        if is_safety_valve_triggered(user_id):
            action_prompt = None
        else:
            action_prompt = update_user_affection_and_get_action(user_id)

        user_text = clean_content or message.content
        async with message.channel.typing():
            ai_reply = await ask_hybrid_ai(user_text, action_prompt)
        await _send_reply(message, ai_reply)

    except Exception:
        logger.exception("處理 Discord 訊息失敗；guild=%s channel=%s", getattr(message.guild, "id", None), message.channel.id)
        try:
            await message.reply("本喵剛剛遇到內部錯誤，請稍後再試或通知管理員查看 Render log 喵。", mention_author=False)
        except discord.HTTPException:
            logger.exception("無法傳送錯誤提示訊息")
    finally:
        # 保留傳統 ! 前綴指令的處理能力。
        await bot.process_commands(message)


@bot.event
async def on_ready():
    logger.info("機器人已上線：%s (ID: %s)", bot.user, bot.user.id if bot.user else "unknown")
    logger.info("伺服器 ID 安全鎖定中：%s", OFFICIAL_GUILD_ID)
    logger.info("機器人目前加入的伺服器 ID：%s", [guild.id for guild in bot.guilds])
    logger.info(
        "免費 AI 路徑狀態：Groq Free key=%s, OpenRouter Free=%s",
        bool(os.getenv("GROQ_API_KEY", "").strip()),
        bool(os.getenv("OPENROUTER_API_KEY", "").strip()),
    )


if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("環境變數 DISCORD_TOKEN 未設定，機器人無法啟動。")

    init_usage_db()
    keep_alive()
    bot.run(token)
