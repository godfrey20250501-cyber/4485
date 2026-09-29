import os
import sys
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View
from dotenv import load_dotenv

from core import (
    keep_alive, init_usage_db, check_and_update_dual_usage, get_quota_status,
    is_safety_valve_triggered, update_user_affection_and_get_action, feed_cat_canned,
    get_user_affection_score, get_channel_lock, ask_hybrid_ai, OFFICIAL_GUILD_ID, 
    DB_FILE, GLOBAL_DAILY_LIMIT
)

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

class AIChatBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        try:
            target_guild = discord.Object(id=OFFICIAL_GUILD_ID)
            
            # 🌟 核心清洗大絕招：強制清空全伺服器後台所有卡住的舊釣魚、舊航海垃圾指令！
            self.tree.clear_commands(guild=target_guild)
            await self.tree.sync(guild=target_guild)
            
            # 🌟 重新寫入乾淨的貓貓專屬指令：/help, /設定, /查看當前額度, /餵食
            self.tree.copy_global_to(guild=target_guild)
            await self.tree.sync(guild=target_guild)
            print("【💥 終極排毒成功】舊航海指令已全數清空！乾淨的貓貓斜線指令上線喵！")
        except Exception as e:
            print(f"【系統提示】指令同步失敗: {e}", file=sys.stderr)

bot = AIChatBot()

# ==================== 🎛️ 互動選單：/help 邏輯 ====================
class HelpSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="貓貓對話模式", description="了解標記與回覆對話方法", emoji="🐱", value="basic"),
            discord.SelectOption(label="雙重限額與安全閥", description="查看個人、全服額度與自動安全閥", emoji="📊", value="quota"),
            discord.SelectOption(label="管理員功能鎖", description="查看管理員文字頻道鎖定", emoji="🛠️", value="admin")
        ]
        super().__init__(placeholder="請選擇你想查看的說明指南...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(color=0x5865F2)
        
        if self.values == "basic":
            embed.title = "🐱 貓貓助理 - 對話與功能限制"
            embed.description = (
                "想要跟本喵說話，必須使用以下兩種方法喵嗚❤：\n\n"
                "**1. 直接標記（@標記）對話**\n"
                "在頻道輸入 `@貓貓AI [訊息]`。\n\n"
                "**2. 直接回覆（Reply）對話**\n"
                "使用 Discord 的「回覆」功能直接打字發送喵！\n\n"
                "*⚠️ 提示：如果今天個人 40 次或全服大額度用完了，本喵會直接秒回大寫的 `MEOW` 敷衍你！*"
            )
        elif self.values == "quota":
            embed.title = "📊 雙重配額與動態安全閥機制"
            embed.description = (
                f"本伺服器採用極高規格的自動配額安全閥偵測機制：\n\n"
                "• **玩家個人限制**：每人每天上限 **40** 次。\n"
                f"• **伺服器全服限制**：全服上限高達 **{GLOBAL_DAILY_LIMIT}** 次（體感無限）。\n"
                "• **⚡ 全自動安全閥控管**：\n"
                "當偵測到全服大池子緊繃（您的剩餘次數 ≥ 全服剩餘總次數）時，系統會**自動關閉【好感度動作進化】與【/餵食罐罐】功能**，對話中只會單純吐出 `MEOW` 或進入極簡省流量對話！"
            )
        elif self.values == "admin":
            embed.title = "🛠️ 伺服器管理員限制功能"
            embed.description = (
                "• **/設定 [文字頻道]** :\n"
                "限定本喵只能在該文字頻道內聊天。鎖定後本喵在其他頻道被觸發時會完全裝死不回應，防爆安全性最高喵！"
            )
            
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=self.view)

class HelpView(View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpSelect())

# ==================== 💬 斜線指令：/help ====================
@bot.tree.command(name="help", description="彈出下拉選單，引導查看貓貓雙重額度與安全閥指南")
async def help_command(interaction: discord.Interaction):
    if interaction.guild_id != OFFICIAL_GUILD_ID: return
    embed = discord.Embed(
        title="🐾 智慧貓貓 AI 助理 - 幫助中心",
        description="本貓智慧安全閥版本已安全部署！請點擊下方的**下拉選單**查看規則喵呜❤：",
        color=0x5865F2
    )
    await interaction.response.send_message(embed=embed, view=HelpView(), ephemeral=True)

# ==================== ⚙️ 斜線指令：/設定 (僅限管理員) ====================
@bot.tree.command(name="設定", description="【管理員專用】設定限制貓貓只能在哪個頻道講話")
@app_commands.describe(頻道="選擇允許貓貓說話的文字頻道")
@commands.has_permissions(administrator=True)
async def set_channel(interaction: discord.Interaction, 頻道: discord.TextChannel):
    if interaction.guild_id != OFFICIAL_GUILD_ID: return
    import sqlite3
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO channel_lock (guild_id, channel_id) VALUES (?, ?)
                 ON CONFLICT(guild_id) DO UPDATE SET channel_id=?''', (OFFICIAL_GUILD_ID, 頻道.id, 頻道.id))
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"🔒 設定成功喵！本喵現在被限制只能在 {頻道.mention} 說話了喵！", ephemeral=True)

# ==================== 📊 斜線指令：/查看當前額度 ====================
@bot.tree.command(name="查看當前額度", description="查詢個人剩餘額度、全服剩餘額度與安全閥狀態")
async def check_quota(interaction: discord.Interaction):
    if interaction.guild_id != OFFICIAL_GUILD_ID: return
    
    g_remain, u_remain, _, _ = get_quota_status(interaction.user.id)
    user_aff = get_user_affection_score(interaction.user.id)
    valve_triggered = is_safety_valve_triggered(interaction.user.id)
    
    valve_status = "🔴 警報已自動觸發（罐罐與好感度系統已安全關閉）" if valve_triggered else "🟢 正常運作中（罐罐與好感度功能全部開啟中）"
    status_text = "高冷傲嬌 🧊" if user_aff < 40 else "溫柔親近 🌸" if user_aff < 100 else "超級黏人 💗"
    
    embed = discord.Embed(title="📊 貓貓雙重額度與智能安全閥狀態面板", color=0x2ECC71)
    embed.add_field(name="👤 您個人的今日剩餘額度", value=f"`{u_remain} / 40` 次", inline=True)
    embed.add_field(name="🌐 伺服器全服當前總剩餘", value=f"`{g_remain} / {GLOBAL_DAILY_LIMIT}` 次", inline=True)
    embed.add_field(name="🔒 自動安全閥監測狀態", value=f"**{valve_status}**", inline=False)
    embed.add_field(name="🐾 您的個人好感度", value=f"`{user_aff}` 點（目前進化：{status_text}）", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==================== 🥫 斜線指令：/餵食 罐罐 ====================
@bot.tree.command(name="餵食", description="餵食貓貓美味罐罐，提升親密度並修復全服額度（安全閥觸發時會自動回覆 MEOW）")
async def feed_cat(interaction: discord.Interaction):
    if interaction.guild_id != OFFICIAL_GUILD_ID: return
    
    success, reply_msg = feed_cat_canned(interaction.user.id)
    if not success and reply_msg == "MEOW":
        await interaction.response.send_message("MEOW")
    else:
        await interaction.response.send_message(reply_msg, ephemeral=not success)

# ==================== 💬 核心事件：對話與回覆偵測 ====================
@bot.event
async def on_message(message):
    if message.author == bot.user: return
    if message.guild is None or message.guild.id != OFFICIAL_GUILD_ID: return

    is_mentioned = bot.user in message.mentions
    is_reply_to_bot = (message.reference and message.reference.cached_message and message.reference.cached_message.author == bot.user)

    if is_mentioned or is_reply_to_bot:
        locked_channel_id = get_channel_lock()
        if locked_channel_id and message.channel.id != locked_channel_id:
            return

        clean_content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        user_id = message.author.id
        
        if is_mentioned and not clean_content and not is_reply_to_bot:
            await message.reply("👀 找本喵嗎？直接 `@我` 或「直接回覆本喵的訊息」來聊天喵！可以使用 `/查看當前額度` 檢查剩餘次數！")
            return

        allowed, g_rem, u_rem = check_and_update_dual_usage(user_id)
        if not allowed:
            await message.reply("MEOW")
            return

        if is_safety_valve_triggered(user_id):
            action_prompt = None
        else:
            action_prompt = update_user_affection_and_get_action(user_id)

        async with message.channel.typing():
            ai_reply = ask_hybrid_ai(clean_content if clean_content else message.content, action_prompt)
        
        await message.reply(ai_reply)

    await bot.process_commands(message)

# ==================== 🚀 系統啟動 ====================
@bot.event
async def on_ready():
    init_usage_db()
    print(f"✨ 雙重安全閥與四核心極致防爆貓貓已成功上線：{bot.user.name}")
    print(f"🔒 伺服器 ID 安全鎖定中：{OFFICIAL_GUILD_ID}")

if __name__ == "__main__":
    keep_alive()
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
