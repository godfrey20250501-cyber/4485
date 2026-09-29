import os
import sys
import datetime
import sqlite3
import random
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import requests

load_dotenv()

# ==================== 🌐 Flask 24h 不休息監聽 ====================
app = Flask('')

@app.route('/')
def home():
    return "極致調教貓貓 AI 正在穩定運作中喵！"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ==================== 🛠️ Discord 基礎與意圖設定 ====================
intents = discord.Intents.default()
intents.message_content = True

class AIChatBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        try:
            # 斜線指令綁定您的專屬伺服器 ID
            target_guild = discord.Object(id=1546517053719060642)
            self.tree.copy_global_to(guild=target_guild)
            await self.tree.sync(guild=target_guild)
            print("【系統提示】最新進階斜線指令已成功同步至指定伺服器！")
        except Exception as e:
            print(f"【系統提示】指令同步失敗: {e}", file=sys.stderr)

bot = AIChatBot()
DB_FILE = "user_usage.db"
OFFICIAL_GUILD_ID = 1546517053719060642

# ==================== 💾 升級版資料庫核心 ====================
def init_usage_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 建立用量紀錄表：包含剩餘額度
    c.execute('''CREATE TABLE IF NOT EXISTS usage_stats (
        user_id INTEGER, log_date TEXT, allowed_count INTEGER DEFAULT 0, used_count INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, log_date)
    )''')
    # 建立鎖定頻道表
    c.execute('''CREATE TABLE IF NOT EXISTS channel_lock (
        guild_id INTEGER PRIMARY KEY, channel_id INTEGER
    )''')
    conn.commit()
    conn.close()

def check_and_update_usage(user_id):
    """檢查奴才是否還有額度，有的話使用次數 +1"""
    today = datetime.date.today().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT allowed_count, used_count FROM usage_stats WHERE user_id=? AND log_date=?", (user_id, today))
    res = c.fetchone()
    
    if not res:
        # 新使用者或當天沒簽到，預設沒有免費額度（必須透過簽到獲得 40 次）
        conn.close()
        return False, 0, 0
        
    allowed_count, used_count = res
    if used_count >= allowed_count:
        conn.close()
        return False, allowed_count, used_count
        
    new_used = used_count + 1
    c.execute("UPDATE usage_stats SET used_count=? WHERE user_id=? AND log_date=?", (new_used, user_id, today))
    conn.commit()
    conn.close()
    return True, allowed_count, new_used

def get_channel_lock():
    """獲取目前鎖定的頻道 ID"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT channel_id FROM channel_lock WHERE guild_id=?", (OFFICIAL_GUILD_ID,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

# ==================== 🧠 跨公司 AI 智能分流與調教引擎 ====================
def ask_hybrid_ai(user_message):
    api_pool = []

    # 1. Groq 金鑰
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and groq_key.strip():
        api_pool.append({
            "url": "https://groq.com",
            "key": groq_key.strip(),
            "model": "llama-3.3-70b-versatile"
        })

    # 2. OpenRouter 金鑰 (使用 2026 最新官方自動免費大腦輪替池)
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key and openrouter_key.strip():
        api_pool.append({
            "url": "https://openrouter.ai",
            "key": openrouter_key.strip(),
            "model": "openrouter/auto"  # ⭐ 自動免費大腦輪替池
        })

    if not api_pool:
        return "MEOW"

    provider = random.choice(api_pool)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {provider['key']}"
    }
    
    cat_system_prompt = (
        "進階調教規則：你是一隻住在 Discord 伺服器裡的智慧聊天小貓咪助理。\n"
        "1. 請完全以一隻傲嬌、可愛、有活力的貓咪視角 and 語氣來說話。\n"
        "2. 你的自我稱呼必須是「本喵」或「本貓」，稱呼使用者為「人類」或「奴才」。\n"
        "3. 你的每句話（或是多數句子）的結尾，都必須加上「喵」、「～喵」或「喵嗚❤」。\n"
        "4. 請使用繁體中文（台灣習慣用語）回答。回答時可以多加入一些貓咪的日常動作描述，"
        "例如：(搖尾巴)、(伸懶腰)、(舔毛)、(傲嬌轉頭)。"
    )

    payload = {
        "model": provider["model"],
        "messages": [
            {"role": "system", "content": cat_system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.85
    }

    try:
        response = requests.post(provider["url"], json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()["choices"]["message"]["content"]
        return "MEOW"
    except Exception:
        return "MEOW"

# ==================== ⚙️ 指令一：/設定 聊天頻道 (僅限管理員) ====================
@bot.tree.command(name="設定", description="【管理員專用】設定限制貓貓只能在哪個頻道講話")
@app_commands.describe(頻道="選擇允許貓貓說話的文字頻道")
@commands.has_permissions(administrator=True)
async def set_channel(interaction: discord.Interaction, 頻道: discord.TextChannel):
    if interaction.guild_id != OFFICIAL_GUILD_ID:
        await interaction.response.send_message("❌ 綁定鎖定：無法在此伺服器使用功能！", ephemeral=True)
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO channel_lock (guild_id, channel_id) VALUES (?, ?)
                 ON CONFLICT(guild_id) DO UPDATE SET channel_id=?''', (OFFICIAL_GUILD_ID, 頻道.id, 頻道.id))
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"🔒 設定成功喵！本喵現在被限制只能在 {頻道.mention} 說話了喵！", ephemeral=True)

# ==================== 📅 指令二：/簽到 領取 40 次機會 ====================
@bot.tree.command(name="簽到", description="每日簽到：獲得 40 次當天與貓貓對話的免費機會")
async def daily_sign(interaction: discord.Interaction):
    if interaction.guild_id != OFFICIAL_GUILD_ID:
        return

    user_id = interaction.user.id
    today = datetime.date.today().isoformat()
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT allowed_count FROM usage_stats WHERE user_id=? AND log_date=?", (user_id, today))
    res = c.fetchone()
    
    if res:
        await interaction.response.send_message("❌ 奴才太貪心了喵！你今天已經簽到過了，明天再來拿喵！", ephemeral=True)
        conn.close()
        return
        
    # 給予當天 40 次額度
    c.execute("INSERT INTO usage_stats (user_id, log_date, allowed_count, used_count) VALUES (?, ?, 40, 0)", (user_id, today))
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"🎁 簽到成功！**{interaction.user.display_name}** 獲得了本喵恩賜的 **40** 次當日對話機會喵嗚❤！")

# ==================== 📊 指令三：/查看當前額度 ====================
@bot.tree.command(name="查看當前額度", description="查詢自己今天還剩下多少次與貓貓對話的額度")
async def check_quota(interaction: discord.Interaction):
    if interaction.guild_id != OFFICIAL_GUILD_ID:
        return

    user_id = interaction.user.id
    today = datetime.date.today().isoformat()
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT allowed_count, used_count FROM usage_stats WHERE user_id=? AND log_date=?", (user_id, today))
    res = c.fetchone()
    conn.close()
    
    if not res:
        await interaction.response.send_message("📊 您今天還沒使用過 `/簽到` 指令喵！目前剩餘額度：`0 / 0`。快去簽到領取 40 次機會喵！", ephemeral=True)
    else:
        allowed, used = res
        remaining = allowed - used
        await interaction.response.send_message(f"📊 奴才 **{interaction.user.display_name}** 的當日額度報告：\n• 已用次數：`{used}` 次\n• 剩餘可用：`{remaining}` 次\n*（當天沒用完的額度午夜會自動歸零消失喵～）*", ephemeral=True)

# ==================== 💬 核心事件：1. @標記 2. 直接回覆功能 ====================
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 🛡️ 安全防盜鎖：不是指定伺服器直接拒絕
    if message.guild is None or message.guild.id != OFFICIAL_GUILD_ID:
        return

    # 🤖 觸發條件判定：1. 被標記 OR 2. 被回覆（回覆的訊息是機器人發的）
    is_mentioned = bot.user in message.mentions
    is_reply_to_bot = (message.reference and message.reference.cached_message and message.reference.cached_message.author == bot.user)

    if is_mentioned or is_reply_to_bot:
        # 🔒 檢查頻道鎖定機制
        locked_channel_id = get_channel_lock()
        if locked_channel_id and message.channel.id != locked_channel_id:
            # 如果不是指定頻道，完全不理會（不回覆，防止在其他頻道刷屏）
            return

        # 乾淨地清洗內文，拿掉 @標記
        clean_content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        user_id = message.author.id
        
        if is_mentioned and not clean_content and not is_reply_to_bot:
            await message.reply("👀 找本喵嗎？記得今天先用 `/簽到` 領 40 次額度，再 `@我` 或「直接回覆本喵的訊息」來聊天喵！")
            return

        # 📊 檢查並扣除用量額度
        allowed, max_quota, current_used = check_and_update_usage(user_id)
        
        # 額度已用盡或根本沒簽到：高冷模式啟動，單純在對話框秒回 MEOW
        if not allowed:
            await message.reply("MEOW")
            return

        # 額度充足：正常叫醒 AI 進行傲嬌貓咪對話
        async with message.channel.typing():
            ai_reply = ask_hybrid_ai(clean_content if clean_content else message.content)
        
        await message.reply(f"{ai_reply}\n\n*📊 今日已用額度：{current_used}/{max_quota}*")

    await bot.process_commands(message)

# ==================== 🚀 系統啟動 ====================
@bot.event
async def on_ready():
    init_usage_db()
    print(f"✨ 萬能進階貓貓 AI 機器人已成功上線：{bot.user.name}")
    print(f"🔒 伺服器 ID 安全鎖定中：{OFFICIAL_GUILD_ID}")

if __name__ == "__main__":
    keep_alive()
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("❌ 錯誤：找不到環境變數 DISCORD_TOKEN！", file=sys.stderr)
