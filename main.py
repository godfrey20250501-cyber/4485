import asyncio
import logging
import os
import re
import base64
import mimetypes

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View
from dotenv import load_dotenv

from core import (
    CHANNEL_HISTORY_LIMIT,
    GLOBAL_DAILY_LIMIT,
    OFFICIAL_GUILD_ID,
    ask_hybrid_ai,
    check_and_update_dual_usage,
    clear_conversation_memory,
    delete_channel_message,
    feed_cat_canned,
    get_channel_lock,
    get_history_storage_backend,
    is_memory_enabled,
    load_recent_channel_messages,
    load_conversation_memory,
    get_quota_status,
    get_user_affection_score,
    init_usage_db,
    is_safety_valve_triggered,
    keep_alive,
    record_channel_message,
    record_channel_messages,
    save_conversation_turn,
    set_memory_enabled,
    set_channel_lock,
    update_user_affection_and_get_action,
)

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("discord_cat_bot")
MAX_IMAGES_PER_MESSAGE = 2
MAX_IMAGE_BYTES = 4 * 1024 * 1024
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_HISTORY_SCAN_MESSAGES = CHANNEL_HISTORY_LIMIT
MAX_HISTORY_CONTEXT_MESSAGES = 15
MAX_HISTORY_CONTEXT_CHARS = 6000
DISCORD_MESSAGE_LINK_RE = re.compile(
    r"https?://(?:canary\.|ptb\.)?discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)"
)
HISTORY_REQUEST_WORDS = ("看一下", "看看", "回顧", "剛才", "剛剛", "前面", "之前聊", "聊天記錄", "對話記錄", "最近討論")

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


async def _prepare_image_payloads(attachments):
    candidates = []
    for attachment in attachments:
        mime_type = (
            attachment.content_type
            or mimetypes.guess_type(attachment.filename)[0]
            or ""
        ).split(";")[0].lower()
        if mime_type.startswith("image/"):
            candidates.append((attachment, mime_type))

    if len(candidates) > MAX_IMAGES_PER_MESSAGE:
        raise ValueError(f"一次最多分析 {MAX_IMAGES_PER_MESSAGE} 張圖片喵。")

    image_payloads = []
    for attachment, mime_type in candidates:
        if mime_type not in SUPPORTED_IMAGE_TYPES:
            raise ValueError("目前只支援 PNG、JPEG/JPG 或 WebP 圖片喵。")
        if attachment.size > MAX_IMAGE_BYTES:
            raise ValueError("單張圖片請小於 4 MiB，這樣免費模型比較容易處理喵。")
        raw = await attachment.read()
        if len(raw) > MAX_IMAGE_BYTES:
            raise ValueError("單張圖片請小於 4 MiB，這樣免費模型比較容易處理喵。")
        image_payloads.append(
            {
                "mime_type": mime_type,
                "data": base64.b64encode(raw).decode("ascii"),
                "filename": attachment.filename[:100],
            }
        )
    return image_payloads


def _history_record_from_message(guild_id, channel, item):
    author = getattr(item.author, "display_name", getattr(item.author, "name", "使用者"))
    body = (getattr(item, "clean_content", "") or getattr(item, "content", "") or "").strip()
    attachment_names = [attachment.filename[:80] for attachment in getattr(item, "attachments", [])]
    if attachment_names:
        body = (body + " " if body else "") + "[附件：" + ", ".join(attachment_names) + "]"
    if not body:
        body = "[沒有文字內容]"
    return {
        "guild_id": guild_id,
        "channel_id": channel.id,
        "message_id": item.id,
        "author_id": item.author.id,
        "author_name": author,
        "content": body[:2000],
        "created_at": getattr(item, "created_at", None).isoformat()
        if getattr(item, "created_at", None) else None,
    }


def _format_history_record(channel, record):
    body = (record.get("content") or "[沒有文字內容]").replace("@", "@\u200b")[:450]
    channel_name = getattr(channel, "name", "頻道")
    return f"[#{channel_name}｜{record.get('author_name', '使用者')}] {body}"


def _format_history_message(channel, item, guild_id=None):
    guild_id = guild_id or getattr(getattr(channel, "guild", None), "id", 0)
    return _format_history_record(channel, _history_record_from_message(guild_id, channel, item))


async def _collect_requested_history(message: discord.Message, clean_content: str):
    """只在使用者明確指定對象/頻道/訊息連結時，從每頻道最近訊息緩衝提供摘錄。"""
    guild = message.guild
    if guild is None:
        return None, None

    link_match = DISCORD_MESSAGE_LINK_RE.search(message.content or "")
    target_users = [
        member
        for member in message.mentions
        if bot.user is None or member.id != bot.user.id
    ]
    target_user_ids = {member.id for member in target_users}
    channels = []
    specific_message = None

    if link_match:
        link_guild_id, channel_id, message_id = map(int, link_match.groups())
        if link_guild_id != guild.id:
            return None, "本喵只能讀取目前這個伺服器的訊息連結喵。"
        channel = guild.get_channel(channel_id)
        if channel is None:
            return None, "本喵找不到連結中的頻道，或該頻道不在目前伺服器喵。"
        channels = [channel]
        specific_message = message_id
    elif message.channel_mentions:
        channels = list(message.channel_mentions[:3])
    elif target_user_ids or any(word in clean_content for word in HISTORY_REQUEST_WORDS):
        channels = [message.channel]
    else:
        return None, None

    bot_member = getattr(guild, "me", None)
    if bot_member is None and bot.user is not None:
        bot_member = guild.get_member(bot.user.id)
    if bot_member is None:
        return None, "本喵暫時無法確認自己在伺服器中的權限喵。"

    gathered = []
    for channel in channels:
        if not callable(getattr(channel, "history", None)):
            return None, "目前只支援查閱文字頻道或討論串喵。"
        requester_permissions = channel.permissions_for(message.author)
        if not requester_permissions.view_channel or not requester_permissions.read_message_history:
            return None, (
                f"你在 #{getattr(channel, 'name', '指定頻道')} 沒有檢視頻道與讀取訊息歷史權限，"
                "為保護其他頻道隱私，本喵不會代為讀取喵。"
            )
        permissions = channel.permissions_for(bot_member)
        if not permissions.view_channel or not permissions.read_message_history:
            return None, (
                f"本喵在 #{getattr(channel, 'name', '指定頻道')} 缺少「檢視頻道」或「讀取訊息歷史」權限喵。"
            )

        try:
            if specific_message is not None:
                item = await channel.fetch_message(specific_message)
                await asyncio.to_thread(
                    record_channel_message,
                    _history_record_from_message(guild.id, channel, item),
                )
                if not target_user_ids or item.author.id in target_user_ids:
                    gathered.append(_format_history_message(channel, item, guild.id))
                continue

            records = await asyncio.to_thread(
                load_recent_channel_messages,
                guild.id,
                channel.id,
                MAX_HISTORY_SCAN_MESSAGES,
            )
            if len(records) < MAX_HISTORY_SCAN_MESSAGES:
                backfill = []
                async for item in channel.history(limit=MAX_HISTORY_SCAN_MESSAGES, oldest_first=False):
                    if item.id != message.id:
                        backfill.append(_history_record_from_message(guild.id, channel, item))
                if backfill:
                    await asyncio.to_thread(record_channel_messages, backfill)
                    records = await asyncio.to_thread(
                        load_recent_channel_messages,
                        guild.id,
                        channel.id,
                        MAX_HISTORY_SCAN_MESSAGES,
                    )

            matches = [
                record for record in records
                if int(record["message_id"]) != message.id
                and (not target_user_ids or int(record["author_id"]) in target_user_ids)
            ]
            for record in matches[-MAX_HISTORY_CONTEXT_MESSAGES:]:
                gathered.append(_format_history_record(channel, record))
        except discord.NotFound:
            return None, "本喵找不到指定的訊息，可能已被刪除喵。"
        except discord.Forbidden:
            return None, "Discord 拒絕本喵讀取該頻道；請確認 bot 有檢視頻道與讀取訊息歷史權限喵。"
        except discord.HTTPException:
            logger.exception("讀取 Discord 頻道歷史失敗：guild=%s channel=%s", guild.id, channel.id)
            return None, "Discord 暫時無法提供該頻道歷史訊息，請稍後再試喵。"

    if not gathered:
        target = f"@{target_users[0].display_name} 在" if target_users else ""
        return f"最近 {MAX_HISTORY_SCAN_MESSAGES} 則訊息中找不到 {target}相關內容。", None
    return "\n".join(gathered)[:MAX_HISTORY_CONTEXT_CHARS], None


# ==================== Help 下拉選單 ====================
class HelpSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="貓貓對話模式", description="了解標記與回覆對話方法", emoji="🐱", value="basic"),
            discord.SelectOption(label="雙重限額與安全閥", description="查看個人、全服額度與自動安全閥", emoji="📊", value="quota"),
            discord.SelectOption(label="對話記憶與圖片", description="設定個人/群組記憶並傳圖提問", emoji="🧠", value="memory"),
            discord.SelectOption(label="查閱頻道訊息", description="明確指定頻道、成員或訊息連結查閱近期對話", emoji="🔎", value="history"),
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
                "• **罐罐獎勵**：只恢復餵食者自己的個人額度，不會增加或恢復全服額度。\n"
                "• **上限**：全服預設 1,200 次/日，程式最多允許設定至 1,500 次/日。\n"
                "• **安全閥**：全服剩餘額度低於或等於個人剩餘額度時，暫停好感度動作。"
            )
        elif selected == "memory":
            embed.title = "🧠 對話記憶與圖片分析"
            embed.description = (
                "每位使用者的個人記憶預設開啟；用 `/個人記憶` 可關閉或重新開啟。群組共享記憶預設關閉，管理員可用 `/群組記憶` 設定目前頻道。"
                "個人/群組對話記憶只保存 @本喵或回覆本喵的互動。另有最近對話緩衝：每個文字頻道最近 100 則真人訊息會自動保存，超過時淘汰最舊訊息；不會自動送給 AI。\n\n"
                "用 `/清除記憶` 刪除自己的記憶；管理員也可清除目前頻道共享記憶。群組記憶啟用時，該頻道內大家的互動會成為共同上下文。\n\n"
                "傳送 PNG、JPEG 或 WebP 圖片並 @本喵或回覆本喵即可分析；每次最多 2 張、每張 4 MiB。"
                "圖片只走 Gemini Free Tier 或 OpenRouter 免費視覺路由；不可用時不會改用 Groq 文字模型或其他付費模型。"
            )
        elif selected == "history":
            embed.title = "🔎 最近訊息保存與按需查閱"
            embed.description = (
                f"本喵會在目標伺服器每個文字頻道保存最近 {MAX_HISTORY_SCAN_MESSAGES} 則真人訊息；新訊息到達時加入緩衝並淘汰最舊訊息。設定了 MongoDB 時會跨 Render 重啟保存。\n\n"
                "@本喵時指定 `#頻道`、@成員，或貼上 Discord 訊息連結，就能要求本喵查閱；模型最多取得 15 則相關摘錄。超過最近 100 則的舊訊息不會保留。\n\n"
                "你與 bot 都必須有該頻道的「檢視頻道」及「讀取訊息歷史」權限。保存的原文只在你明確要求查閱時傳給 AI 服務商，不會每則訊息都送給 AI。"
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


@bot.tree.command(name="個人記憶", description="開啟或關閉你在本伺服器的私人對話記憶", guild=GUILD_OBJECT)
@app_commands.choices(狀態=[
    app_commands.Choice(name="開啟", value="on"),
    app_commands.Choice(name="關閉", value="off"),
])
async def personal_memory(interaction: discord.Interaction, 狀態: app_commands.Choice[str]):
    enabled = 狀態.value == "on"
    set_memory_enabled(interaction.guild_id, "personal", interaction.user.id, enabled)
    status_text = "已開啟" if enabled else "已關閉"
    await interaction.response.send_message(
        f"你的個人記憶{status_text}喵。只儲存你 @本喵或回覆本喵的對話；若此頻道開啟群組記憶，會優先使用群組記憶。",
        ephemeral=True,
    )


@bot.tree.command(name="群組記憶", description="管理員開啟或關閉目前頻道的共享對話記憶", guild=GUILD_OBJECT)
@app_commands.choices(狀態=[
    app_commands.Choice(name="開啟", value="on"),
    app_commands.Choice(name="關閉", value="off"),
])
@app_commands.checks.has_permissions(administrator=True)
async def group_memory(interaction: discord.Interaction, 狀態: app_commands.Choice[str]):
    if interaction.channel_id is None or interaction.guild_id is None:
        await interaction.response.send_message("請在伺服器文字頻道使用此指令喵。", ephemeral=True)
        return
    enabled = 狀態.value == "on"
    set_memory_enabled(interaction.guild_id, "group", interaction.channel_id, enabled)
    status_text = "已開啟" if enabled else "已關閉"
    await interaction.response.send_message(
        f"本頻道共享記憶{status_text}喵。只記錄 @本喵或回覆本喵的訊息與本喵回覆；此頻道使用者都可能共享這些內容。",
        ephemeral=True,
    )


@bot.tree.command(name="清除記憶", description="清除自己的記憶；管理員可清除目前頻道共享記憶", guild=GUILD_OBJECT)
@app_commands.choices(範圍=[
    app_commands.Choice(name="我的個人記憶", value="personal"),
    app_commands.Choice(name="目前頻道群組記憶（管理員）", value="group"),
])
async def clear_memory(interaction: discord.Interaction, 範圍: app_commands.Choice[str]):
    if interaction.guild_id is None:
        await interaction.response.send_message("請在伺服器中使用此指令喵。", ephemeral=True)
        return
    if 範圍.value == "personal":
        deleted = clear_conversation_memory(interaction.guild_id, "personal", interaction.user.id)
        reply = f"已清除你的個人記憶（刪除 {deleted} 則內容）喵。若個人記憶仍開啟，之後的對話會重新儲存。"
    else:
        permissions = getattr(interaction.user, "guild_permissions", None)
        if permissions is None or not permissions.administrator:
            await interaction.response.send_message("清除頻道共享記憶需要伺服器管理員權限喵。", ephemeral=True)
            return
        deleted = clear_conversation_memory(interaction.guild_id, "group", interaction.channel_id)
        reply = f"已清除本頻道共享記憶（刪除 {deleted} 則內容）喵。若群組記憶仍開啟，之後的對話會重新儲存。"
    await interaction.response.send_message(reply, ephemeral=True)


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
        "🔴 已觸發（好感度動作暫停）"
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
    description="餵食貓貓罐罐，提升好感度並恢復自己的個人額度",
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

        if callable(getattr(message.channel, "history", None)) and (
            (message.content or "").strip() or message.attachments
        ):
            try:
                await asyncio.to_thread(
                    record_channel_message,
                    _history_record_from_message(message.guild.id, message.channel, message),
                )
            except Exception:
                # 儲存服務暫時故障不應讓機器人漏掉一般聊天或停止回覆。
                logger.exception(
                    "寫入最近頻道訊息失敗：guild=%s channel=%s",
                    message.guild.id,
                    message.channel.id,
                )

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

        has_image_attachment = any(
            ((attachment.content_type or mimetypes.guess_type(attachment.filename)[0] or "").startswith("image/"))
            for attachment in message.attachments
        )
        if is_mentioned and not clean_content and not is_reply and not has_image_attachment:
            await message.reply(
                "👀 找本喵嗎？直接 `@我` 或回覆本喵的訊息來聊天喵！可以使用 `/查看當前額度` 檢查剩餘次數！",
                mention_author=False,
            )
            return

        history_context, history_error = await _collect_requested_history(message, clean_content)
        if history_error:
            await message.reply(history_error, mention_author=False)
            return

        allowed, _, _ = check_and_update_dual_usage(user_id)
        if not allowed:
            await message.reply("MEOW", mention_author=False)
            return

        if is_safety_valve_triggered(user_id):
            action_prompt = None
        else:
            action_prompt = update_user_affection_and_get_action(user_id)

        try:
            image_payloads = await _prepare_image_payloads(message.attachments)
        except ValueError as exc:
            await message.reply(str(exc), mention_author=False)
            return

        user_text = clean_content or ("請描述並分析我附上的圖片。" if image_payloads else message.content)
        conversation_history = load_conversation_memory(message.guild.id, user_id, message.channel.id)
        async with message.channel.typing():
            ai_reply = await ask_hybrid_ai(
                user_text,
                action_prompt,
                conversation_history=conversation_history,
                image_payloads=image_payloads,
                reference_context=history_context,
            )
        await _send_reply(message, ai_reply)
        memory_user_text = user_text
        if image_payloads:
            memory_user_text += " [附圖：" + ", ".join(image["filename"] for image in image_payloads) + "]"
        save_conversation_turn(
            message.guild.id,
            user_id,
            message.channel.id,
            message.author.display_name,
            memory_user_text,
            ai_reply,
        )

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
async def on_message_edit(before: discord.Message, after: discord.Message):
    if after.author.bot or after.guild is None or after.guild.id != OFFICIAL_GUILD_ID:
        return
    try:
        if (after.content or "").strip() or after.attachments:
            await asyncio.to_thread(
                record_channel_message,
                _history_record_from_message(after.guild.id, after.channel, after),
            )
        else:
            await asyncio.to_thread(
                delete_channel_message,
                after.guild.id,
                after.channel.id,
                after.id,
            )
    except Exception:
        logger.exception("更新編輯後的訊息緩衝失敗：guild=%s channel=%s", after.guild.id, after.channel.id)


@bot.event
async def on_raw_message_delete(payload: discord.RawMessageDeleteEvent):
    if payload.guild_id != OFFICIAL_GUILD_ID:
        return
    try:
        await asyncio.to_thread(
            delete_channel_message,
            payload.guild_id,
            payload.channel_id,
            payload.message_id,
        )
    except Exception:
        logger.exception("刪除訊息緩衝失敗：guild=%s channel=%s", payload.guild_id, payload.channel_id)


@bot.event
async def on_ready():
    logger.info("機器人已上線：%s (ID: %s)", bot.user, bot.user.id if bot.user else "unknown")
    logger.info("伺服器 ID 安全鎖定中：%s", OFFICIAL_GUILD_ID)
    logger.info("機器人目前加入的伺服器 ID：%s", [guild.id for guild in bot.guilds])
    history_backend = await asyncio.to_thread(get_history_storage_backend)
    logger.info(
        "每頻道最近訊息緩衝：最多 %s 則；儲存後端：%s",
        MAX_HISTORY_SCAN_MESSAGES,
        history_backend,
    )
    logger.info(
        "免費 AI 路徑狀態：Groq key=%s, Gemini key=%s, OpenRouter key=%s",
        bool(os.getenv("GROQ_API_KEY", "").strip()),
        bool(os.getenv("GEMINI_API_KEY", "").strip()),
        bool(os.getenv("OPENROUTER_API_KEY", "").strip()),
    )


if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("環境變數 DISCORD_TOKEN 未設定，機器人無法啟動。")

    init_usage_db()
    keep_alive()
    bot.run(token)
