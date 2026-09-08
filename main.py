from dotenv import load_dotenv
load_dotenv()  # 自動打開 .env 檔案讀取 Token
import os
import time
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
from discord import app_commands
import random
import sqlite3
from datetime import datetime

# 🌐 Flask 網頁製造機（保持 24h 不休息）
app = Flask('')

@app.route('/')
def home():
    return "歡樂釣魚場 3.9 深海與熔岩大世紀完美連線！"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 1. 基礎設定與意圖 (Intents)
intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        try:
            await self.tree.sync()
            print("連線成功：歡樂釣魚場 3.9 全新指令已完全同步！")
        except Exception as e:
            print(f"指令同步提示: {e}")

bot = MyBot()
DB_FILE = "fishing_game.db"

# 🌟 官方支援群 ID 設定（已完美綁定老哥的 Discord 伺服器！）
SUPPORT_GUILD_ID = 1546517053719060642



# ======= 🧭 指令：四大海域地理隔離旅遊大百科 (4 空格精準縮排) =======
@bot.tree.command(name="地圖說明", description="單純詢問與查詢特定海域的解鎖等級、所需載具與限定產物圖鑑")
@app_commands.describe(海域名稱="請選擇你想單純查詢的海域：一海、二海、三海、地幔")
async def map_guide(interaction: discord.Interaction, 海域名稱: str):
    # 🌟 1. 核心大數據：將四個海域的所有「解鎖、載具、產物」全部攤平，單純提供玩家詢問！
    guides = {
        "一海": {
            "title": "🚢 一海・新手小池塘 (0 LV 起航點)", "cost": "免費傳送 🪙", "vehicle": "🦴 徒手即可進入 (素釣起步)", "npc": "👴 隔壁張老頭 (初級/高級魚竿)",
            "fish": "• 普通：🐟 吳郭魚、🐠 小丑魚、🐡 氣噗噗河豚\n• 稀有：🐡 黃金河豚\n• 傳奇：👑 黃金鯉魚 (解鎖二海的核心材料！)", "color": 0x3498DB
        },
        "二海": {
            "title": "🤿 二海・黃金珊瑚礁 (80 LV 珊瑚島)", "cost": "500 金幣 / 次 🪙", "vehicle": "🤿 科技耐壓潛水服 (需上交 5 隻黃金鯉魚解鎖)", "npc": "🦈 魚人阿龍 (深海魚竿/珊瑚礁共振竿)",
            "fish": "• 普通：🐚 珊瑚礁小蝦、🐠 七彩霓虹魚、👟 舊鞋子\n• 稀有： Squid 大王烏賊、🦈 藍色鯊魚、🦀 帝王蟹\n• 傳奇：🔱 海神三叉戟\n• 神話：🧜‍♀️ 美人魚的眼淚\n• 秘密：🏐 一顆...排球?", "color": 0x1ABC9C
        }
    }

# 🌟 3.9 終極防線：開機自動補齊 fish_encyclopedia 與 guilds 核心表，徹底砸碎保底吳郭魚魔咒！
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 1. 使用者主表
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 100, rod TEXT DEFAULT '新手魚竿', bait_count INTEGER DEFAULT 5,
        level INTEGER DEFAULT 0, xp INTEGER DEFAULT 0, current_map TEXT DEFAULT '一海・新手小池塘', pet TEXT DEFAULT '無',
        last_daily TEXT DEFAULT '2000-01-01', enchant TEXT DEFAULT '無', bait_type TEXT DEFAULT '普通魚餌',
        quest_type TEXT DEFAULT '無', quest_target INTEGER DEFAULT 0, quest_progress INTEGER DEFAULT 0, quest_reward INTEGER DEFAULT 0
    )''')
    # 2. 背包物資表
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER, item_name TEXT, item_count INTEGER DEFAULT 0, PRIMARY KEY(user_id, item_name)
    )''')
    # 3. 官方兌換碼表
    c.execute('''CREATE TABLE IF NOT EXISTS redeem_codes (
        code_name TEXT PRIMARY KEY, prize_money INTEGER, prize_bait INTEGER
    )''')
    # 4. 🌟 進化版補齊：物種百科圖鑑表（徹底封死 no such table 報錯！）
    c.execute('''CREATE TABLE IF NOT EXISTS fish_encyclopedia (
        user_id INTEGER, fish_name TEXT, PRIMARY KEY(user_id, fish_name)
    )''')
    # 5. 🌟 進化版補齊：大航海公會表
    c.execute('''CREATE TABLE IF NOT EXISTS guilds (
        guild_name TEXT PRIMARY KEY, leader_id INTEGER, vault INTEGER DEFAULT 0, current_boss TEXT DEFAULT '無', boss_hp INTEGER DEFAULT 0
    )''')
    # 6. 🌟 進化版補齊：公會成員對照表
    c.execute('''CREATE TABLE IF NOT EXISTS guild_members (
        user_id INTEGER PRIMARY KEY, guild_name TEXT
    )''')
    conn.commit()
    
    # 🛠️ 舊資料庫欄位熱修補
    alter_columns = [
        ("last_daily", "TEXT DEFAULT '2000-01-01'"), ("enchant", "TEXT DEFAULT '無'"),
        ("bait_type", "TEXT DEFAULT '普通魚餌'"), ("quest_type", "TEXT DEFAULT '無'"),
        ("quest_target", "INTEGER DEFAULT 0"), ("quest_progress", "INTEGER DEFAULT 0"), ("quest_reward", "INTEGER DEFAULT 0")
    ]
    for col_name, col_type in alter_columns:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            conn.commit()
        except sqlite3.OperationalError: pass
        
    try:
        c.execute("INSERT OR IGNORE INTO redeem_codes VALUES ('NEWUPDATE', 1500, 10)")
        c.execute("INSERT OR IGNORE INTO redeem_codes VALUES ('1UPDATE', 3000, 20)")
        c.execute("INSERT OR IGNORE INTO redeem_codes VALUES ('SORRY2026', 8000, 50)") 
        conn.commit()
    except: pass
    conn.close()

# 3. 🏪 全球聯網普通商店物資
BAITS_SHOP = {
    "普通魚餌": 15, "高級魚餌": 60, "海藻餌": 25, "磁鐵重餌": 45, "🔋 彈性奈米反覆餌": 4999,
    "🥳神祕黃金寶箱": 500, "🟢普通運氣藥水": 100, "🔵高級運氣藥水": 400, "⚡閃電速度藥水": 250, "💗性慾藥水": 150, "🌌轉生神仙水": 99999
}
# 🌟 全球統一天氣池
WEATHER_POOL = {
    "☀️ 晴空萬里": {"desc": "風平浪靜，陽光灑落海面，非常適合出海。", "luck_bonus": 1.0, "speed_mod": 0.0},
    "🌧️ 狂風暴雨": {"desc": "大雨傾盆，海浪洶湧，魚群紛紛浮上水面呼吸！", "luck_bonus": 1.6, "speed_mod": -1.0},
    "🌫️ 濃霧密佈": {"desc": "海上大霧遮蔽視線，魚兒容易受驚，收竿需格外小心。", "luck_bonus": 0.8, "speed_mod": 1.0},
    "🌌 天降異象": {"desc": "星海與遠古神光撕裂天空！各地湧現傳奇特產潮汐！", "luck_bonus": 2.5, "speed_mod": 2.0}
}

def get_global_weather():
    time_seed = int(time.time() / 300)
    random.seed(time_seed)
    w_name = random.choice(list(WEATHER_POOL.keys()))
    w_info = WEATHER_POOL[w_name]
    random.seed()
    return w_name, w_info

# 🖼️ 3.9 航海核心：四大海域、解鎖等級、傳送過路費與駐島專屬 NPC 漁具店
MAPS = {
    "一海・新手小池塘": {"req_lvl": 0, "cost": 0, "npc": "👴 隔壁張老頭", "desc": "新手起步的溫馨池塘，平靜安全。", "image": "https://imgur.com", "shop": {"初級魚竿": 200, "高級魚竿": 1000}},
    "二海・黃金珊瑚礁": {"req_lvl": 80, "cost": 500, "npc": "🦈 魚人阿龍", "desc": "高壓的水下珊瑚礁世界，魚獲斑斕色彩。", "image": "https://imgur.com", "shop": {"深海魚竿": 3500, "珊瑚礁共振竿": 6000}},
    "三海_馬里亞娜海溝深淵": {"req_lvl": 160, "cost": 2500, "npc": "🔱 大祭司波賽頓", "desc": "漆黑萬丈的馬里亞娜海溝底部，充斥未知巨獸與零件。", "image": "https://imgur.com", "shop": {"量子魚竿": 8000, "ADMIN魚桿": 500000}}
}

ROD_STATS = {
    "新手魚竿": {"luck": 1.0, "speed_bonus": 0.0, "mutation": 0.05}, "初級魚竿": {"luck": 1.3, "speed_bonus": 0.5, "mutation": 0.10},
    "高級魚竿": {"luck": 2.0, "speed_bonus": 1.5, "mutation": 0.20}, "深海魚竿": {"luck": 3.5, "speed_bonus": 3.0, "mutation": 0.35},
    "珊瑚礁共振竿": {"luck": 5.0, "speed_bonus": 4.5, "mutation": 0.45}, "量子魚竿": {"luck": 7.0, "speed_bonus": 5.5, "mutation": 0.60},
    "ADMIN魚桿": {"luck": 999.0, "speed_bonus": 8.5, "mutation": 1.00}, "🏆 任務大師榮譽紀念竿": {"luck": 8.8, "speed_bonus": 6.5, "mutation": 0.75}
}

ENCHANT_POOL = {
    "⚡ 迅捷": {"desc": "收竿冷卻時間永久縮減 1.5 秒", "luck_mod": 1.0, "speed_mod": 1.5, "mutate_mod": 0.0},
    "🍀 豐收": {"desc": "氣運爆發，大魚爆率永久提升 1.5 倍", "luck_mod": 1.5, "speed_mod": 0.0, "mutate_mod": 0.0},
    "🧬 異變": {"desc": "特殊輻射共振，魚隻突變機率激增 +25%", "luck_mod": 1.0, "speed_mod": 0.0, "mutate_mod": 0.25},
    "🌌  sigma": {"desc": "全屬性終極洗鍊：運氣x2.5、冷卻-2秒、變異+40%", "luck_mod": 2.5, "speed_mod": 2.0, "mutate_mod": 0.40}
}

BOBBER_POOL = {
    "⚪ 常規軟木浮標": {"success_rate": 0, "mutate_bonus": 0.0}, "🟢 綠光電子浮標": {"success_rate": 15, "mutate_bonus": 0.05},
    "🔵 藍海震盪浮標": {"success_rate": 25, "mutate_bonus": 0.12}, "🔴 狂暴重力浮標": {"success_rate": 45, "mutate_bonus": 0.25}
}

FISH_POOL = {
    "普通": [("🐟 吳郭魚", 15), ("🐠 小丑魚", 20), ("👟 舊鞋子", 2)], "稀有": [("🐡 黃金河豚", 200)]
}

# 🌟 3.9 核心隔離魚池：一海絕對釣不到二海，地幔只有熔岩！
MAP_EXCLUSIVE_FISH = {
    "一海・新手小池塘": {
        "普通": [("🐟 吳郭魚", 15), ("🐠 小丑魚", 20), ("🐡 氣噗噗河豚", 25)],
        "稀有": [("🐡 黃金河豚", 200)], "傳奇": [("👑 黃金鯉魚", 800)]
    },
    "二海・黃金珊瑚礁": {
        "普通": [("🐚 珊瑚礁小蝦", 10), ("🐠 七彩霓虹魚", 45)],
        "稀有": [("🦑 大王烏賊", 60), ("🦈 藍色鯊魚", 120), ("🦀 帝王蟹", 150)],
        "傳奇": [("🔱 海神三叉戟", 1200)], "神話": [("🧜‍♀️ 美人魚的眼淚", 7500)], "秘密": [("🏐一顆...排球?", 27000)]
    },
    "三海_馬里亞娜海溝深淵": {
        "普通": [("🐟 發光鮟鱇魚", 75), ("🧪 輻射基因流體", 110)],
        "稀有": [("🐙 深淵巨型章魚", 280), ("🦈 遠古惡魔巨齒鯊", 650)],
        "傳奇": [("🐳 藍鯨", 1500)], "秘密": [("🛸 外星科技零件", 25000)],
        "神話": [("🐉 東方青龍", 35000)], "作者級": [("💻 作者的未編譯源代碼", 100000), ("🤨神秘的SIGMAFACE", 300000)]
    },
    "四海・地幔熔岩禁地": {
        "傳奇": [("🌋 熔岩火靈魚", 3500)],
        "神話": [("🔥 煉獄不死鳥之眼", 12000), ("💎 熔岩核心巨鑽", 25000)],
        "秘密": [("🌋 古星核熱熔高壓液體", 55000)],
        "作者級": [("🌌 SIGMA的熔岩超燃雪茄", 333333)]
    }
}
def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT balance, rod, bait_count, level, xp, current_map, pet, last_daily, enchant, bait_type, quest_type, quest_target, quest_progress, quest_reward FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    if not res:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        c.execute("SELECT balance, rod, bait_count, level, xp, current_map, pet, last_daily, enchant, bait_type, quest_type, quest_target, quest_progress, quest_reward FROM users WHERE user_id=?", (user_id,))
        res = c.fetchone()
    conn.close()
    return {
        "balance": int(res[0]), "rod": str(res[1]), "bait_count": int(res[2]), "level": int(res[3]), "xp": int(res[4]),
        "current_map": str(res[5]), "pet": str(res[6]), "last_daily": str(res[7]), "enchant": str(res[8]), "bait_type": str(res[9]),
        "quest_type": str(res[10]), "quest_target": int(res[11]), "quest_progress": int(res[12]), "quest_reward": int(res[13])
    }

def update_user(user_id, **kwargs):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for k, v in kwargs.items():
        c.execute(f"UPDATE users SET {k}=? WHERE user_id=?", (v, user_id))
    conn.commit()
    conn.close()

def add_inventory(user_id, item_name, amount=1):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO inventory (user_id, item_name, item_count) VALUES (?, ?, ?) ON CONFLICT(user_id, item_name) DO UPDATE SET item_count=item_count+?", (user_id, item_name, amount, amount))
    conn.commit()
    conn.close()

# ======= 📖 指令一：使用教學 =======
@bot.tree.command(name="釣魚說明", description="查看歡樂釣魚場 3.9 的大師指南")
async def guide(interaction: discord.Interaction):
    embed = discord.Embed(title="🎣 歡樂釣魚場 3.9 ── 航海大世紀指南", description="`──────────────────────────`", color=0x5865F2)
    embed.add_field(name="🎮 冒險核心指令", value="`/釣魚` : 拋竿出海挑戰(具備真實等待)\n`/背包` : 查看大倉庫與載具裝備\n`/傳送地圖` : 金幣跨越海域傳送(需對應載具)", inline=False)
    embed.add_field(name="🏰 公會與圖鑑", value="`/公會背包` : 查詢公會金庫與召喚魔王\n`/公會遠征` : 集體圍剿世界BOSS\n`/查看圖鑑` : 開闢四大海域生物進度", inline=False)
    embed.set_footer(text="💡 提示：在官方支援群內拋竿，金幣經驗永久激增 1.2 倍！")
    await interaction.response.send_message(embed=embed)

# ======= 🌤️ 指令二：觀測天氣 =======
@bot.tree.command(name="天氣", description="觀測當前全服統一的大氣觀測站與各地圖海域共振影響")
async def current_weather_cmd(interaction: discord.Interaction):
    w_name, w_info = get_global_weather()
    embed = discord.Embed(title=f"🌤️ 全服統一氣象觀測站 ── 當前全球：【{w_name}】", description=f"*{w_info['desc']}*", color=0x3498DB)
    for m_name in MAPS.keys():
        embed.add_field(name=f"🚢 【{m_name}】海域影響", value=f"氣運倍率：`x{w_info['luck_bonus']}`\n收竿冷卻：`{w_info['speed_mod']} 秒`", inline=True)
    await interaction.response.send_message(embed=embed)

# ======= 📅 指令三：每日簽到時間鎖 =======
@bot.tree.command(name="簽到", description="每日領取 200 金幣與 3 個普通魚餌補給！")
async def daily(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    today_str = datetime.now().strftime("%Y-%m-%d")
    if user["last_daily"] == today_str:
        await interaction.response.send_message("❌ 老哥，你今天已經簽到過了，明天再來吧！", ephemeral=True)
        return
    update_user(user_id, balance=user["balance"]+200, bait_count=user["bait_count"]+3, last_daily=today_str)
    await interaction.response.send_message(f"🎁 **{interaction.user.display_name}** 簽到成功！獲得 `200` 金幣 與 `3` 個普通魚餌！")
# ======= 📅 指令四：日常任務委託系統 =======
@bot.tree.command(name="任務", description="查看今日公會接取的日常冒險進度與懸賞金幣")
async def check_quest(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    embed = discord.Embed(title=f"📋 {interaction.user.display_name} 的今日公會懸賞任務", color=0xF39C12)
    if user["quest_type"] == "無":
        embed.description = "🔍 你目前身上空空如也！請輸入 `/接取任務` 來刷新今日公會日常！"
    else:
        status = "✅ 可回報" if user["quest_progress"] >= user["quest_target"] else "⏳ 進行中"
        embed.add_field(name=f"🎯 委託目標：【{user['quest_type']}】 ({status})", value=f"• 目前進度：`{user['quest_progress']} / {user['quest_target']}`\n• 達成賞金：`{user['quest_reward']} 🪙`", inline=False)
    await interaction.response.send_message(embed=embed)



@bot.tree.command(name="接取任務", description="向航海公會刷新並接取今日隨機日常任務（全宇宙擴充 20 大趣味懸賞！）")
async def accept_quest(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    if user["quest_type"] != "無":
        await interaction.response.send_message("❌ 你身上已經有任務進行中了！請先完成或回報。", ephemeral=True)
        return
        
    # 🌟 3.9.9 終極大改版：20 大隨機趣味任務池（格式：任務名稱, 目標次數, 賞金金幣）
    q_pool = [
        # 🎣 基礎垂釣類
        ("🎣 出海大豐收", 5, 450),       # 釣魚 5 次
        ("🪙 財氣東來", 3, 300),         # 釣到稀有以上 3 次
        ("🔮 附魔大師", 1, 200),         # 進行 1 次附魔洗鍊
        ("👟 垃圾清除計畫", 2, 250),     # 釣到舊鞋子 2 次
        ("🛍️ 揮金如土", 2, 250),          # 在商店購買任意道具 2 次
        # 🚢 載具與海域探險類
        ("🦀 珊瑚礁採集", 3, 400),       # 在二海成功拉竿 3 次
        ("🦈 捕鯊終結者", 1, 600),       # 在二海釣到藍色鯊魚 1 次
        ("⚙️ 深海科技回收", 1, 800),     # 在三海釣到外星科技零件 1 次
        ("🐋 尋找莫比迪克", 2, 700),     # 在三海成功拉竿 2 次
        ("🔥 地幔熔岩煉獄", 1, 1200),    # 在地幔熔岩禁地成功拉竿 1 次
        # ⚔️ 公會副本類
        ("🦁 魔王討伐軍", 3, 500),       # 參與公會遠征進攻 BOSS 達 3 次
        ("👑 會長的認可", 1, 400),       # 公會金庫獲得一次你全賣的抽稅貢獻
        ("🔨 公會奠基者", 1, 300),       # 查詢一次 /公會背包 面板
        ("📦 補給箱快遞", 1, 350),       # 使用 /開箱 指令打開一個黃金寶箱
        ("💸 船長互助會", 1, 200),       # 使用 /匯款 指令轉帳給其他玩家一次
        # 💎 極致歐皇類
        ("🧬 驚天異變紀元", 1, 850),     # 釣到任意一款 [✨突變首綴] 魚獲 1 次
        ("🟡 傳奇垂釣家", 1, 750),       # 成功釣到「傳奇」或以上稀有度的魚獲 1 次
        ("🔴 諸神黃昏淚", 1, 1500),      # 成功釣到「神話」或以上稀有度的至高產物 1 次
        ("🌌 終極星空共振", 1, 2000),    # 運氣爆發！釣到帶有 [🌌星空突變] 的終極魚獲 1 次
        ("🪝 頂級浮標大師", 1, 500)       # 拋竿時裝配到「綠光/藍海/狂暴」高階浮標 1 次
    ]
    
    q_name, q_tar, q_rew = random.choice(q_pool)
    update_user(user_id, quest_type=q_name, quest_target=q_tar, quest_progress=0, quest_reward=q_rew)
    
    embed = discord.Embed(title="📋 航海公會 ── 今日日常懸賞令", description=f"船長 **{interaction.user.display_name}**，你已成功接取今日公會委託！", color=0xF39C12)
    embed.add_field(name=f"🎯 委託目標：【{q_name}】", value=f"• 需要數量/次數：`{q_tar}` 次\n• 達成賞金獎勵：`{q_rew} 🪙` 金幣", inline=False)
    embed.set_footer(text="💡 提示：達成進度後，手動輸入 /回報任務 即可提領金幣與抽取神竿！")
    await interaction.response.send_message(embed=embed)

# ======= 💸 指令五：玩家金幣轉帳 =======
@bot.tree.command(name="匯款", description="將金幣轉帳給伺服器內的其他玩家")
@app_commands.describe(target="你想匯款給誰？", amount="你想轉帳的金幣數量")
async def transfer(interaction: discord.Interaction, target: discord.Member, amount: int):
    if amount <= 0 or target.id == interaction.user.id:
        await interaction.response.send_message("❌ 轉帳金額或目標錯誤！", ephemeral=True)
        return
    sender = get_user(interaction.user.id)
    if sender["balance"] < amount:
        await interaction.response.send_message("❌ 錢包餘額不足！", ephemeral=True)
        return
    receiver = get_user(target.id)
    update_user(interaction.user.id, balance=sender["balance"] - amount)
    update_user(target.id, balance=receiver["balance"] + amount)
    await interaction.response.send_message(f"💸 **{interaction.user.display_name}** 成功轉帳 **{amount}** 金幣給 **{target.display_name}**！")

# ======= 🧰 指令六：開啟黃金寶箱 =======
@bot.tree.command(name="開箱", description="開啟背包內的神祕黃金寶箱，隨機獲得高級藥水、大筆金幣 or 神獸寵物！")
async def open_box(interaction: discord.Interaction):
    await interaction.response.defer()
    user_id = interaction.user.id
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT item_count FROM inventory WHERE user_id=? AND item_name='🥳神祕黃金寶箱'", (user_id,))
    res = c.fetchone()
    box_count = res[0] if res else 0
    if box_count <= 0:
        await interaction.followup.send("❌ 背包倉庫裡沒有黃金寶箱！", ephemeral=True)
        conn.close()
        return
    c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🥳神祕黃金寶箱'", (user_id,))
    conn.commit()
    conn.close()
    roll = random.random()
    user = get_user(user_id)
    if roll < 0.05:
        chosen_pet = random.choice(["🐱 招財貓(金幣+10%)", "🦅 尋寶獵鷹(XP+30%)", "🐉 迷你小青龍(XP+50%)"])
        update_user(user_id, pet=chosen_pet)
        await interaction.followup.send(f"🌌 ✨ **【不世奇蹟】** **{interaction.user.display_name}** 成功孵化出神獸：**{chosen_pet}**！！")
    elif roll < 0.25:
        add_inventory(user_id, "🔵高級運氣藥水", 1)
        await interaction.followup.send(f"🧰 成功開箱獲得：`🔵高級運氣藥水` x1！")
    elif roll < 0.55:
        add_inventory(user_id, "🟢普通運氣藥水", 1)
        await interaction.followup.send(f"🧰 成功開箱獲得：`🟢普通運氣藥水` x1！")
    else:
        bonus_money = random.randint(150, 400)
        update_user(user_id, balance=user["balance"]+bonus_money, bait_count=user["bait_count"]+5)
        await interaction.followup.send(f"🧰 成功開箱獲得：`🪙 {bonus_money} 金幣` 與 `🐛 高級魚餌` x5！")

# ======= 🏆 指令七：伺服器排行榜 =======
@bot.tree.command(name="排行榜", description="查看當前伺服器中最強的遠航大師")
async def leaderboard(interaction: discord.Interaction):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, level, balance FROM users ORDER BY level DESC, balance DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    embed = discord.Embed(title="🏆 歡樂釣魚場 - 遠航天梯榜", color=0xF1C40F)
    if not rows: embed.description = "天梯榜上空空如也..."
    else:
        rank_str = ""
        for i, row in enumerate(rows):
            u_id, lvl, bal = row
            member = interaction.guild.get_member(u_id) if interaction.guild else None
            name = member.display_name if member else f"遠航大師({u_id})"
            medal = "🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else f"第 {i+1} 名"
            rank_str += f"{medal} **{name}** ── `LV.{lvl}` | `錢包: {bal} 金幣`\n"
        embed.description = rank_str
    await interaction.response.send_message(embed=embed)
# ======= 🗺️ 指令八：3.9 載具防禦金幣傳送海域系統 =======
@bot.tree.command(name="傳送地圖", description="支付金幣揚帆啟航傳送至全新海域（需裝備對應下海載具，地幔需 LV.220）")
@app_commands.describe(map_name="目的地海域名稱")
async def teleport_map(interaction: discord.Interaction, map_name: str):
    if map_name not in MAPS and map_name != "四海・地幔熔岩禁地":
        await interaction.response.send_message(f"❌ 找不到這片海域！可用目的地：{', '.join(MAPS.keys())}、四海・地幔熔岩禁地", ephemeral=True)
        return
    user_id = interaction.user.id
    user = get_user(user_id)
    
    # 針對動態地幔地圖做特殊費用判定
    req_lvl = MAPS[map_name]["req_lvl"] if map_name in MAPS else 220
    cost = MAPS[map_name]["cost"] if map_name in MAPS else 5000
    npc = MAPS[map_name]["npc"] if map_name in MAPS else "👁️ 覺醒老哥本人"
    desc = MAPS[map_name]["desc"] if map_name in MAPS else "鑽破地殼的終極地底世界！高溫高壓，此處出產地底極致高溫突變流體生物！"
    image = MAPS[map_name]["image"] if map_name in MAPS else "https://imgur.com"

    if user["level"] < req_lvl:
        await interaction.response.send_message(f"🔒 等級實力不足！前往【{map_name}】需要達到 `LV.{req_lvl}`，你目前只有 `LV.{user['level']}`。", ephemeral=True)
        return
    if user["balance"] < cost:
        await interaction.response.send_message(f"❌ 傳送費用不足！前往【{map_name}】需要 `{cost}` 金幣，你目前只有 `{user['balance']}` 🪙。", ephemeral=True)
        return

    # 🤿 3.9 核心防線：檢查玩家倉庫內是否真正購置並解鎖對應下海載具，沒載具 100% 絕對拒絕傳送！
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if map_name == "二海・黃金珊瑚礁":
        c.execute("SELECT item_count FROM inventory WHERE user_id=? AND item_name='🤿 科技耐壓潛水服'", (user_id,))
        has_suit = c.fetchone()
        if not has_suit or has_suit[0] < 1:
            await interaction.response.send_message("❌ 傳送失敗！二海完全位於高壓海中，你必須先輸入 `/購買載具 潛水服` 才能成功下海！", ephemeral=True)
            conn.close()
            return
            
    elif map_name == "三海_馬里亞娜海溝深淵":
        c.execute("SELECT item_count FROM inventory WHERE user_id=? AND item_name='🚢 量子核能潛水艇'", (user_id,))
        has_sub = c.fetchone()
        if not has_sub or has_sub[0] < 1:
            await interaction.response.send_message("❌ 傳送失敗！三海位於極其恐怖的馬里亞娜海溝底部，你必須先輸入 `/購買載具 潛水艇` 才能沉入深海！", ephemeral=True)
            conn.close()
            return
            
    elif map_name == "四海・地幔熔岩禁地":
        c.execute("SELECT item_count FROM inventory WHERE user_id=? AND item_name='🔥 地心重型鑽探機'", (user_id,))
        has_drill = c.fetchone()
        if not has_drill or has_drill[0] < 1:
            await interaction.response.send_message("❌ 傳送失敗！地幔充斥著高溫岩漿，你必須先輸入 `/購買載具 鑽探機` 駕駛重型機甲破殼！", ephemeral=True)
            conn.close()
            return
            
    conn.close()
    update_user(user_id, current_map=map_name, balance=user["balance"]-cost)
    embed = discord.Embed(title=f"🚢 船隻載具傳送成功 ── 抵達【{map_name}】", description=f"• 駐島島嶼 NPC：`{npc}`\n• 傳送過路費：`-{cost} 🪙`\n\n*{desc}*", color=0x1ABC9C)
    embed.set_image(url=image)
    await interaction.response.send_message(embed=embed)

# ======= 🎣 指令九：3.9.5 航海世紀終極釣魚（🌟 浮標全面改版為：商店購買與背包單次消耗制度！） =======
cooldowns = {}
@bot.tree.command(name="釣魚", description="拋出釣竿！引進真實時間等待咬竿，自動裝配背包中最高階的浮標進行消耗加成！")
async def fish(interaction: discord.Interaction):
    await interaction.response.defer()
    import asyncio
    
    try:
        user_id = interaction.user.id
        user = get_user(user_id)
        current_map = user.get("current_map", "一海・新手小池塘")
        current_rod = user.get("rod", "新手魚竿")
        current_enchant = user.get("enchant", "無")
        
        if not current_map or current_map == "None": current_map = "一海・新手小池塘"
        if not current_rod or current_rod == "None": current_rod = "新手魚竿"
        if not current_enchant or current_enchant == "None": current_enchant = "無"
        
        weather_name, weather_info = get_global_weather()
        weather_stat = weather_info.get("加成", {}).get(current_map, {"luck": 1.0, "speed": 0.0})
        rod_stat = ROD_STATS.get(current_rod, {"luck": 1.0, "speed_bonus": 0.0, "mutation": 0.05})
        enc_stat = ENCHANT_POOL.get(current_enchant, {"luck_mod": 1.0, "speed_mod": 0.0, "mutate_mod": 0.0})
        
        enc_speed = enc_stat.get("speed_mod", 0.0) if enc_stat else 0.0
        enc_luck = enc_stat.get("luck_mod", 1.0) if enc_stat else 1.0
        enc_mutate = enc_stat.get("mutate_mod", 0.0) if enc_stat else 0.0
        
        # 冷卻計時器結算
        current_time = time.time()
        base_cooldown = 10.0 - float(rod_stat.get("speed_bonus", 0.0)) - float(enc_speed)
        w_speed = weather_stat.get("speed", 0.0)
        base_cooldown += float(w_speed)
        if base_cooldown < 1.5: base_cooldown = 1.5
        
        if user_id in cooldowns and current_time - cooldowns[user_id] < base_cooldown:
            remaining = round(base_cooldown - (current_time - cooldowns[user_id]), 1)
            await interaction.followup.send(f"🚨 拋竿速度太快了！手拉得好酸...再等 {remaining} 秒。(當前冷卻: {round(base_cooldown, 1)}秒)", ephemeral=True)
            return
        cooldowns[user_id] = current_time

        # 🌟 3.9.5 智慧浮標加載：從背包讀取玩家購買的浮標儲備
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT item_name, item_count FROM inventory WHERE user_id=? AND item_name IN ('🔴 狂暴重力浮標', '🔵 藍海震盪浮標', '🟢 綠光電子浮標') AND item_count > 0", (user_id,))
        player_bobbers = dict(c.fetchall())
        
        # 依照強度權限，自動挑選玩家背包裡最高階的浮標使用
        if player_bobbers.get('🔴 狂暴重力浮標', 0) > 0:
            bobber_name = '🔴 狂暴重力浮標'
        elif player_bobbers.get('🔵 藍海震盪浮標', 0) > 0:
            bobber_name = '🔵 藍海震盪浮標'
        elif player_bobbers.get('🟢 綠光電子浮標', 0) > 0:
            bobber_name = '🟢 綠光電子浮標'
        else:
            bobber_name = '⚪ 常規軟木浮標' # 沒購買的玩家，一律強制保底素釣軟木標
            
        bobber_stat = BOBBER_POOL[bobber_name]
        
        await interaction.edit_original_response(content=f"🪝 **{interaction.user.display_name}** 裝配著背包裡的【**{bobber_name}**】在【{current_map}】拋出釣竿...\n⏳ 正在波浪中靜靜等待魚兒咬竿，請保持潛心觀測... 🌊")
        
        wait_seconds = random.randint(2, 3)
        await asyncio.sleep(wait_seconds)
        
        # 資料庫物資與消耗品加載
        c.execute("SELECT item_name, item_count FROM inventory WHERE user_id=? AND item_name IN ('💗性慾藥水', '🌌轉生神仙水', '🟢普通運氣藥水', '🔵高級運氣藥水', '⚡閃電速度藥水', '高級魚餌', '海藻餌', '磁鐵重餌', '🔋 彈性奈米反覆餌')", (user_id,))
        inv_data = dict(c.fetchall())
        
        has_potion = inv_data.get('💗性慾藥水', 0) > 0
        has_god_water = inv_data.get('🌌轉生神仙水', 0) > 0
        has_normal_pot = inv_data.get('🟢普通運氣藥水', 0) > 0
        has_high_pot = inv_data.get('🔵高級運氣藥水', 0) > 0
        has_speed_pot = inv_data.get('⚡閃電速度藥水', 0) > 0
        has_high_bait = inv_data.get('高級魚餌', 0) > 0
        has_seaweed = inv_data.get('海藻餌', 0) > 0
        has_magnet = inv_data.get('磁鐵重餌', 0) > 0
        has_nano_bait = inv_data.get('🔋 彈性奈米反覆餌', 0) > 0
        
        is_supported = interaction.guild_id == SUPPORT_GUILD_ID if interaction.guild_id else False
        guild_bonus = 1.2 if is_supported else 1.0
        
        luck_multiplier = float(rod_stat.get("luck", 1.0)) * float(weather_info.get("luck_bonus", 1.0)) * float(enc_luck) * guild_bonus
        bait_msg = f"🌍 **全球統一天氣：【{weather_name}】** (*{weather_info['desc']}*)\n"
        if is_supported: bait_msg = "🤝 **【官方群共振】檢測到你在支援伺服器拋竿，全收益提升 1.2 倍！**\n" + bait_msg
        if current_enchant != "無": bait_msg += f"🔮 漁具灌注附魔：**【{current_enchant}】** 加持中\n"
        
        # 扣除魚餌邏輯
        if has_nano_bait:
            luck_multiplier *= 2.0
            bait_msg += "🔋 **[神級奈米反覆餌] 裝備了彈性反覆餌，本竿不消耗任何材料，且幸運值x2.0！**\n"
        elif has_god_water:
            luck_multiplier *= 100.0
            c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🌌轉生神仙水'", (user_id,))
        elif has_magnet:
            luck_multiplier *= 1.5
            c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='磁鐵重餌'", (user_id,))
            bait_msg += "🧲 **[磁力共振] 你使用了磁鐵重餌，碎片零件爆率提升！**\n"
        elif has_high_bait:
            luck_multiplier *= 3.0
            c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='高級魚餌'", (user_id,))
            bait_msg += "✨ 你使用了 **高級魚餌**！\n"
        elif has_seaweed:
            luck_multiplier *= 1.3
            c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='海藻餌'", (user_id,))
            bait_msg += "🌿 你使用了 **海藻餌**！\n"
        elif user.get("bait_count", 0) > 0:
            luck_multiplier *= 1.5
            update_user(user_id, bait_count=int(user["bait_count"])-1)
            bait_msg += "🐛 你消耗了 1 個 **普通魚餌**！\n"
        else: bait_msg += "🪝 無魚餌素釣，全憑直覺！\n"
        
        if has_high_pot: c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🔵高級運氣藥水'", (user_id,)); luck_multiplier *= 2.0
        elif has_normal_pot: c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🟢普通運氣藥水'", (user_id,)); luck_multiplier *= 1.3
        if has_speed_pot: c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='⚡閃電速度藥水'", (user_id,))
        if has_potion: c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='💗性慾藥水'", (user_id,)); bait_msg = "🔥 **[速度狂暴]** 速度大增！\n" + bait_msg
        
        # 🌟 3.9.5 核心扣除點：如果使用的是高階購買浮標，在確定收竿扣款時，精準扣除背包數量 1 個！
        if bobber_name != '⚪ 常規軟木浮標':
            c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name=?", (user_id, bobber_name))
            bait_msg += f"🚨 本竿自動消耗了 1 個 **{bobber_name}**！\n"
            
        conn.commit()
        conn.close()

        roll = random.uniform(0, 100)
        luck_score = 10.0 * luck_multiplier
        if luck_score >= 500000: chosen_rarity = "作者級" if roll < 40 else "秘密" if roll < 80 else "神話"
        elif luck_score >= 150: chosen_rarity = "作者級" if roll < 1 else "秘密" if roll < 5 else "神話" if roll < 20 else "傳奇" if roll < 60 else "稀有"
        elif luck_score >= 50: chosen_rarity = "神話" if roll < 2 else "傳奇" if roll < 15 else "稀有" if roll < 50 else "普通"
        else: chosen_rarity = "傳奇" if roll < 1 else "稀有" if roll < 20 else "普通"

        base_success = 95 - bobber_stat["success_rate"]
        if chosen_rarity == "作者級": base_success = 15 + bobber_stat["success_rate"]
        elif chosen_rarity == "秘密": base_success = 30 + bobber_stat["success_rate"]
        elif chosen_rarity == "神話": base_success = 45 + bobber_stat["success_rate"]
        elif chosen_rarity == "傳奇": base_success = 65 + bobber_stat["success_rate"]
        
        if random.uniform(0, 100) > base_success:
            await interaction.followup.send(f"🦈 **{interaction.user.display_name} 拉扯失敗！** 一隻極其巨大的 **【{chosen_rarity}】** 級生物猛烈咬線，扯斷了你的 【{bobber_name}】 吐信逃跑了...（拉竿成功率：`{int(base_success)}%`）")
            return

        available_fish = []
        if current_map in MAP_EXCLUSIVE_FISH and chosen_rarity in MAP_EXCLUSIVE_FISH[current_map]:
            available_fish = MAP_EXCLUSIVE_FISH[current_map][chosen_rarity]
        if not available_fish: available_fish = FISH_POOL.get(chosen_rarity, FISH_POOL["普通"])
        if not available_fish: available_fish = [("🐟 吳郭魚", 15)]
        
        fish_item = random.choice(available_fish)
        fish_name, _ = fish_item
        
        final_mutation_chance = float(rod_stat.get("mutation", 0.05)) + float(enc_mutate) + float(bobber_stat.get("mutate_bonus", 0.0))
        if random.random() < final_mutation_chance:
            fish_name = f"{random.choice(['[🟢毒性突變]', '[🔵晶螢閃耀]', '[👑極致黃金]', '[🔴血色異變]', '[🌌星空突變]'])} {fish_name}"
            
        add_inventory(user_id, fish_name, 1)
                # 🌟 3.9.9 智慧追蹤：在拉竿成功的瞬間，自動過濾並累加 8 大垂釣與海域探險任務進度！
        q_type = user.get("quest_type", "無")
        q_prog = user.get("quest_progress", 0)
        
        if q_type != "無":
            if q_type == "🎣 出海大豐收":
                update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🪙 財氣東來" and chosen_rarity in ["稀有", "傳奇", "神話", "秘密", "作者級"]:
                update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "👟 垃圾清除計畫" and "舊鞋子" in fish_name:
                update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🧬 驚天異變紀元" and any(p in fish_name for p in ["[🟢毒性]", "[🔵晶螢]", "[👑極致]", "[🔴血色]", "[🌌星空]"]):
                update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🟡 傳奇垂釣家" and chosen_rarity in ["傳奇", "神話", "秘密", "作者級"]:
                update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🔴 諸神黃昏淚" and chosen_rarity in ["神話", "秘密", "作者級"]:
                update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🌌 終極星空共振" and "[🌌星空突變]" in fish_name:
                update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🪝 頂級浮標大師" and bobber_name != '⚪ 常規軟木浮標':
                update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🦀 珊瑚礁採集" and current_map == "二海・黃金珊瑚礁":
                update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🦈 捕鯊終結者" and "藍色鯊魚" in fish_name:
                update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "⚙️ 深海科技回收" and "外星科技零件" in fish_name:
                update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🐋 尋找莫比迪克" and current_map == "三海_馬里亞娜海溝深淵":
                update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🔥 地幔熔岩煉獄" and current_map == "四海・地幔熔岩禁地":
                update_user(user_id, quest_progress=q_prog + 1)
        xp_gained = int(random.randint(15, 30) * guild_bonus)
        new_xp = int(user.get("xp", 0)) + xp_gained
        current_lvl = int(user.get("level", 0))
        xp_needed = (current_lvl + 1) * 50
        lvl_up_msg = ""
        while new_xp >= xp_needed:
            new_xp -= xp_needed; current_lvl += 1; xp_needed = (current_lvl + 1) * 50
            lvl_up_msg = f"\n⚡ **【LEVEL UP！】恭喜你升級到了 🌟 LV.{current_lvl} 🌟！！**"
        update_user(user_id, level=current_lvl, xp=new_xp)
        
        conn = sqlite3.connect(DB_FILE); c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO fish_encyclopedia VALUES (?, ?)", (user_id, fish_name))
        conn.commit(); conn.close()

        icons = {"普通":"⚪", "稀有":"🔵", "傳奇":"🟡", "神話":"🔴", "秘密":"🟣", "作者級":"🌌"}
               # 🌟 第一部分：4 空格縮排，精準將大魚的 Embed 結算卡片發送回頻道！
        embed = discord.Embed(
            title=f"🎣 拉竿成功！ ── 【{icons[chosen_rarity]} {chosen_rarity}】", 
            description=f"{bait_msg}🧬 順利捕捉：**{fish_name}**！ (成功率: `{int(base_success)}%`)\n🏆 獲得經驗：`+{xp_gained}xp` | 當前進度：`🧬 {new_xp}/{xp_needed} XP`{lvl_up_msg}", 
            color=0x27AE60
        )
        await interaction.followup.send(embed=embed)
        
    except Exception as error:
        print(f"釣魚背景報錯日誌: {error}")
                # 🌟 第三部分：8 空格與 12 空格精準巢狀縮排，徹底為釣魚指令完美收尾！
        try:
            add_inventory(interaction.user.id, "🐟 吳郭魚", 1)
            await interaction.followup.send(f"🎣 系統提示：海流產生輕微波盪，**{interaction.user.display_name}** 順利收竿，釣到了一隻 **🐟 吳郭魚**！(報錯類型: {error})")
        except:
            pass
# ======= 🏪 指令十：全球普通商店 =======
@bot.tree.command(name="普通商店", description="顯示豐收漁具物資與神奇藥水")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🏪 3.9 全球聯網普通商店", description="`──────────────────────────`", color=0x2ECC71)
    embed.add_field(name="🐛 全套物資與神奇藥水", value="\n".join([f"• {k}: `{v} 🪙`" for k, v in BAITS_SHOP.items()]), inline=False)
    embed.set_footer(text="💡 提示：每個海域的專屬限定魚竿，必須前往該海域並向當地的駐島 NPC 購買！")
    await interaction.response.send_message(embed=embed)

# ======= 🏝️ 指令十一：海域限定商店 =======
@bot.tree.command(name="海域商店", description="向目前所在的島嶼駐島 NPC 採購限定高階漁具與神竿")
async def island_shop(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    current_map = user["current_map"]
    if current_map not in MAPS:
        await interaction.response.send_message("❌ 當前所處海域島嶼沒有登記的 NPC 商店商販！", ephemeral=True)
        return
    m_data = MAPS[current_map]
    embed = discord.Embed(title=f"🏝️ 【{current_map}】 ── 限定專屬店", description=f"駐島 NPC 商販：**{m_data['npc']}**\n`──────────────────────────`", color=0x1ABC9C)
    embed.add_field(name="🎣 限定魚竿清單 (具備海域幸運共振加成)", value="\n".join([f"• {k}: `{v} 🪙`" for k, v in m_data["shop"].items()]), inline=False)
    await interaction.response.send_message(embed=embed)

# ======= 🛍️ 指令十二：通用採購系統 =======
@app_commands.describe(item_name="物品或限定魚竿名稱", quantity="數量")
@bot.tree.command(name="購買", description="採購普通商店的物資，或者採購當前海域島嶼 NPC 的限定魚竿")
async def buy(interaction: discord.Interaction, item_name: str, quantity: int = 1):
    if quantity <= 0: return
    user_id = interaction.user.id
    user = get_user(user_id)
    current_map = user["current_map"]
    price, is_rod = None, False
    if item_name in BAITS_SHOP: price = BAITS_SHOP[item_name]
    elif current_map in MAPS and item_name in MAPS[current_map]["shop"]: price = MAPS[current_map]["shop"][item_name]; is_rod = True
    if not price:
        await interaction.response.send_message("❌ 找不到該商品！請確認名稱正確，且特定海域限定竿要在該海域才能購得。", ephemeral=True)
        return
    total_cost = price * quantity
    if user["balance"] < total_cost:
        await interaction.response.send_message("❌ 你的錢包金幣不足！", ephemeral=True)
        return
    if is_rod:
        update_user(user_id, balance=user["balance"]-total_cost, rod=item_name)
        await interaction.response.send_message(f"🛍️ 購買成功！你跟 **{MAPS[current_map]['npc']}** 購買並裝備了限定竿：**{item_name}**！")
    else:
        update_user(user_id, balance=user["balance"]-total_cost)
        add_inventory(user_id, item_name, quantity)
        await interaction.response.send_message(f"🛍️ 購買成功！你將 {quantity} 個 **{item_name}** 收進背包倉庫！")

# ======= 🔮 指令十三：遠古附魔台 =======
@bot.tree.command(name="附魔", description="對你的魚竿洗鍊永久詞條")
async def enchant_rod(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    if user["balance"] < 500:
        await interaction.response.send_message("❌ 金幣不足 500！", ephemeral=True)
        return
    chosen_enchant = random.choice(list(ENCHANT_POOL.keys()))
    if user["quest_type"] == "🔮 附魔大師": update_user(user_id, quest_progress=user["quest_progress"]+1)
    update_user(user_id, balance=user["balance"]-500, enchant=chosen_enchant)
    await interaction.response.send_message(f"🔮 遠古附魔台共振成功！魚竿獲得永久屬性：**【{chosen_enchant}】** (*{ENCHANT_POOL[chosen_enchant]['desc']}*)")

# ======= 🎒 指令十四：個人背包面板 =======
@bot.tree.command(name="背包", description="查看屬性、海域、附魔詞條日常任務與個人倉庫")
async def inventory(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT item_name, item_count FROM inventory WHERE user_id=? AND item_count > 0", (user_id,))
    items = c.fetchall()
    conn.close()
    xp_needed = (user["level"] + 1) * 50
    embed = discord.Embed(title=f"🎒 {interaction.user.display_name} 的大冒險家面板", color=0x3498DB)
    embed.add_field(name="📊 個人屬性", value=f"• 等級：`LV.{user['level']}` ({user['xp']}/{xp_needed})\n• 錢包：`{user['balance']} 🪙`\n• 所在海域：【`{user['current_map']}`】", inline=True)
    embed.add_field(name="🎣 附魔守護", value=f"• 魚竿：`{user['rod']}`\n• 附魔：`【{user['enchant']}】`\n• 儲備普通餌：`{user['bait_count']} 個`", inline=True)
    inv_str = "\n".join([f"• {name} x{count}" for name, count in items]) if items else "空空如也"
    embed.add_field(name="🐟 儲存大倉庫", value=inv_str, inline=False)
    await interaction.response.send_message(embed=embed)

# ======= 💰 指令十五：一鍵全賣（支援公會自動抽稅 5% 存入金庫） =======
@bot.tree.command(name="全賣", description="一鍵清空大倉庫魚獲換取大量金幣（突變享加成，有公會自動繳納金庫稅金！）")
async def sell_all(interaction: discord.Interaction):
    await interaction.response.defer()
    user_id = interaction.user.id
    user = get_user(user_id)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT item_name, item_count FROM inventory WHERE user_id=? AND item_count > 0", (user_id,))
    items = c.fetchall()
    if not items:
        await interaction.followup.send("📭 背包大倉庫空空如也，沒有可回收物。", ephemeral=True)
        conn.close()
        return
    prices_map = {}
    for _, v_list in FISH_POOL.items():
        for fname, fprice in v_list: prices_map[fname] = fprice
    for _, r_dict in MAP_EXCLUSIVE_FISH.items():
        for _, f_list in r_dict.items():
            for fname, fprice in f_list: prices_map[fname] = fprice
    total_revenue, sold_details, sold_any = 0, [], False
    for item_name, count in items:
        base_name = item_name
        for p in ["[🟢毒性突變] ", "[🔵晶螢閃耀] ", "[👑極致黃金] ", "[🔴血色異變] ", "[🌌星空突變] "]: 
            base_name = base_name.replace(p, "")
        if base_name in prices_map:
            revenue = prices_map[base_name] * count
            if "[🟢毒性突變]" in item_name: revenue = int(revenue * 1.3); tag = "(🔥1.3倍毒性)"
            elif "[🔵晶螢閃耀]" in item_name: revenue = int(revenue * 1.6); tag = "(🔥1.6倍晶螢)"
            elif "[👑極致黃金]" in item_name: revenue = int(revenue * 2.0); tag = "(🔥2.0倍黃金)"
            elif "[🔴血色異變]" in item_name: revenue = int(revenue * 2.5); tag = "(🔥2.5倍血色)"
            elif "[🌌星空突變]" in item_name: revenue = int(revenue * 3.0); tag = "(🔥3.0倍星空)"
            else: tag = ""
            sold_details.append(f"• {item_name} x{count} -> 獲得 {revenue} 金幣 {tag}")
            total_revenue += revenue; sold_any = True
            c.execute("UPDATE inventory SET item_count=0 WHERE user_id=? AND item_name=?", (user_id, item_name))
            
    if not sold_any or total_revenue == 0:
        conn.close(); await interaction.followup.send("❌ 大倉庫內沒有常規可回收魚獲。", ephemeral=True); return
    conn.commit(); conn.close()
    if "招財貓" in user["pet"]:
        bonus_cash = int(total_revenue * 0.1); total_revenue += bonus_cash
        sold_details.append(f"🐱 【招財貓加持】 額外抓回了 {bonus_cash} 金幣！")
        
    # 🏰 公會自動抽稅機制：若有组织，全賣自動上繳 5% 凝聚公會金庫
    tax_msg = ""
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("SELECT guild_name FROM guild_members WHERE user_id=?", (user_id,))
    g_res = c.fetchone()
    if g_res:
        g_name = g_res[0]
        tax_amount = int(total_revenue * 0.05)
        total_revenue -= tax_amount
        c.execute("UPDATE guilds SET vault = vault + ? WHERE guild_name=?", (tax_amount, g_name))
        conn.commit()
        tax_msg = f"\n🏰 **【公會共榮】5% 稅金 ({tax_amount} 金幣) 已自動繳入【{g_name}】金庫！**"
    conn.close()
    
    update_user(user_id, balance=user["balance"] + total_revenue)
    embed = discord.Embed(title="💰 魚獲交易結算完畢", description="\n".join(sold_details) + f"\n\n💵 實際賺得：**{total_revenue}** 金幣！{tax_msg}", color=0xF1C40F)
    await interaction.followup.send(embed=embed)


# ======= ⚔️ 指令十六：公會重裝武器軍火庫 =======
WEAPONS_SHOP = {
    "⚔️ 鐵製魚叉": {"cost": 500, "dmg": 85}, "⚔️ 精鋼巨弩": {"cost": 2500, "dmg": 260},
    "🔱 海神破滅戟": {"cost": 8500, "dmg": 680}, "🌌 ADMIN破碼弒神劍": {"cost": 99999, "dmg": 9999}
}
BOSS_POOL = {
    "🐙 北海深淵巨怪・克拉肯": {"hp": 12000, "cost": 1000, "desc": "揮舞著千米觸手的遠古海怪，能輕易拍碎一整支遠征艦隊！"},
    "🐉 滅世混亂巨龍・利維坦": {"hp": 25000, "cost": 2500, "desc": "沉睡在海底火山的熔岩魔龍，吐息能將整片海域化為灰燼！"},
    "🛸 外星機械母艦・核心眼": {"hp": 45000, "cost": 6000, "desc": "來自外星星域的墜落遺蹟，專產代碼零件！"},
    "🤨 終極邪神・SIGMA_FACE": {"hp": 88888, "cost": 15000, "desc": "用絕對極致的表情鄙視一切生物，凡人直視便會理智崩潰！"},
    "🐳 虛空吞噬者・莫比迪克": {"hp": 150000, "cost": 30000, "desc": "吞噬時間與海域的終極幻獸，三海至高王座的守門人！"}
}

@bot.tree.command(name="武器商店", description="向航海公會軍火庫採購討伐世界 BOSS 的重型武器裝備")
async def weapon_shop(interaction: discord.Interaction):
    embed = discord.Embed(title="⚔️ 遠古重型武器軍火庫", description="`──────────────────────────`", color=0xC0392B)
    for k, v in WEAPONS_SHOP.items():
        embed.add_field(name=k, value=f"• 採購費用：`{v['cost']} 🪙`\n• 討伐魔王基礎傷害：`💥 {v['dmg']} Pts`", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="購買武器", description="向軍火庫支付金幣採購並裝備重型武器")
@app_commands.describe(武器名稱="請輸入完整的武器裝備名稱")
async def buy_weapon(interaction: discord.Interaction, 武器名稱: str):
    user_id = interaction.user.id
    user = get_user(user_id)
    if 武器名稱 not in WEAPONS_SHOP:
        await interaction.response.send_message("❌ 軍火庫裡找不到這把武器！", ephemeral=True); return
    w_data = WEAPONS_SHOP[武器名稱]
    if user["balance"] < w_data["cost"]:
        await interaction.response.send_message(f"❌ 金幣不足！需要 `{w_data['cost']}` 金幣！", ephemeral=True); return
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    for old_w in WEAPONS_SHOP.keys(): c.execute("UPDATE inventory SET item_count=0 WHERE user_id=? AND item_name=?", (user_id, old_w))
    conn.commit(); conn.close()
    update_user(user_id, balance=user["balance"]-w_data["cost"])
    add_inventory(user_id, 武器名稱, 1)
    await interaction.response.send_message(f"🛍️ 裝備成功！**{interaction.user.display_name}** 成功裝備了重型殺器：【**{武器名稱}**】！")

# ======= 🏰 指令十七：大航海公會創立與管理 =======
@bot.tree.command(name="創立公會", description="創立你專屬的航海公會（條件：需達到 LV.50 且支付 5000 金幣）")
@app_commands.describe(公會名稱="你想為公會取什麼名字？")
async def create_guild(interaction: discord.Interaction, 公會名稱: str):
    user_id = interaction.user.id
    user = get_user(user_id)
    if user["level"] < 50:
        await interaction.response.send_message(f"❌ 創立失敗！等級實力不足！需要達到 `LV.50`。", ephemeral=True); return
    if user["balance"] < 5000:
        await interaction.response.send_message(f"❌ 資金不足！向總部註冊公會需要 `5000` 金幣！", ephemeral=True); return
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("SELECT guild_name FROM guild_members WHERE user_id=?", (user_id,))
    if c.fetchone():
        await interaction.response.send_message("❌ 你已經是某個公會的成員了，請先退出！", ephemeral=True); conn.close(); return
    try:
        c.execute("INSERT INTO guilds VALUES (?, ?, 0, '無', 0)", (公會名稱, user_id))
        c.execute("INSERT INTO guild_members VALUES (?, ?)", (user_id, 公會名稱))
        conn.commit()
        update_user(user_id, balance=user["balance"]-5000)
        await interaction.response.send_message(f"🏰 🎉 恭喜 **{interaction.user.display_name}** 成功註冊大公會：【**{公會名稱}**】！")
    except sqlite3.IntegrityError:
        await interaction.response.send_message("❌ 這個公會名稱已經被搶先註冊了！", ephemeral=True)
    conn.close()

@bot.tree.command(name="加入公會", description="申請加入其他大師開創的航海公會")
@app_commands.describe(公會名稱="你想加入的公會名稱")
async def join_guild(interaction: discord.Interaction, 公會名稱: str):
    user_id = interaction.user.id
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("SELECT guild_name FROM guilds WHERE guild_name=?", (公會名稱,))
    if not c.fetchone():
        await interaction.response.send_message("❌ 找不到這個公會！", ephemeral=True); conn.close(); return
    c.execute("SELECT guild_name FROM guild_members WHERE user_id=?", (user_id,))
    if c.fetchone():
        await interaction.response.send_message("❌ 你身上已經有公會會籍了！", ephemeral=True); conn.close(); return
    c.execute("INSERT INTO guild_members VALUES (?, ?)", (user_id, 公會名稱))
    conn.commit(); conn.close()
    await interaction.response.send_message(f"🤝 **{interaction.user.display_name}** 成功加入航海公會：【**{公會名稱}**】！")

@bot.tree.command(name="公會背包", description="查看當前公會的資金金庫、世界 BOSS 狀態以及全體船長名單")
async def guild_panel(interaction: discord.Interaction):
    user_id = interaction.user.id
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("SELECT guild_name FROM guild_members WHERE user_id=?", (user_id,))
    res = c.fetchone()
    if not res:
        await interaction.response.send_message("❌ 老哥，你目前還是一介散人，沒有加入任何公會！", ephemeral=True); conn.close(); return
    g_name = res[0]
    c.execute("SELECT leader_id, vault, current_boss, boss_hp FROM guilds WHERE guild_name=?", (g_name,))
    leader_id, vault, c_boss, b_hp = c.fetchone()
    c.execute("SELECT user_id FROM guild_members WHERE guild_name=?", (g_name,))
    members = c.fetchall(); conn.close()
    leader_user = interaction.guild.get_member(leader_id) if interaction.guild else None
    leader_name = leader_user.display_name if leader_user else f"老船長({leader_id})"
    m_list = [f"• {interaction.guild.get_member(row[0]).display_name if interaction.guild and interaction.guild.get_member(row[0]) else f'船長({row[0]})'}" for row in members]
    embed = discord.Embed(title=f"🏰 航海公會面板 ── 【{g_name}】", description="`──────────────────────────`", color=0x34495E)
    embed.add_field(name="👑 公會領袖", value=f"`{leader_name}`", inline=True)
    embed.add_field(name="💰 金庫總資金", value=f"`{vault} 🪙`", inline=True)
    boss_status = f"🔴 **【{c_boss}】** 圍剿中！\n• 剩餘總血量：`❤️ {b_hp} Pts`" if c_boss != "無" else "💤 目前海域平靜，暫無魔王肆虐。"
    embed.add_field(name="🐉 世界魔王狀態", value=boss_status, inline=False)
    embed.add_field(name="👥 全體成員名單", value="\n".join(m_list), inline=False)
    await interaction.response.send_message(embed=embed)


# ======= 🐉 指令十八：會長專屬世界 BOSS 召喚 =======
@bot.tree.command(name="召喚魔王", description="【會長專屬】消耗公會金庫資金，向全服海域隨機召喚一隻史詩級世界 BOSS 巨獸！")
async def summon_boss(interaction: discord.Interaction):
    user_id = interaction.user.id
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("SELECT guild_name FROM guilds WHERE leader_id=?", (user_id,))
    g_res = c.fetchone()
    if not g_res:
        await interaction.response.send_message("❌ 權限不足！只有【公會會長】才能發動魔王召喚！", ephemeral=True); conn.close(); return
    g_name = g_res
    c.execute("SELECT current_boss, vault FROM guilds WHERE guild_name=?", (g_name,))
    c_boss, vault = c.fetchone()
    if c_boss != "無":
        await interaction.response.send_message(f"❌ 召喚失敗！海域中已經有 【{c_boss}】 肆虐了！", ephemeral=True); conn.close(); return
    b_name = random.choice(list(BOSS_POOL.keys()))
    b_data = BOSS_POOL[b_name]
    if vault < b_data["cost"]:
        await interaction.response.send_message(f"❌ 公會金庫資金不足！召喚需要 `{b_data['cost']}` 資金，目前金庫只有 `{vault}` 🪙。", ephemeral=True); conn.close(); return
    c.execute("UPDATE guilds SET current_boss=?, boss_hp=?, vault=vault-? WHERE guild_name=?", (b_name, b_data["hp"], b_data["cost"], g_name))
    c.execute("CREATE TABLE IF NOT EXISTS boss_damage (guild_name TEXT, user_id INTEGER, dmg_done INTEGER, PRIMARY KEY(guild_name, user_id))")
    c.execute("DELETE FROM boss_damage WHERE guild_name=?", (g_name,))
    conn.commit(); conn.close()
    embed = discord.Embed(title="🚨 ── 全服警告：遠古魔王降臨 ── 🚨", description=f"🏰 【**{g_name}**】的會長使用了遠古共振器！\n\n🐉 **魔王現世**：【**{b_name}**】\n❤️ 初始總血量：`{b_data['hp']} Pts`\n\n*{b_data['desc']}*", color=0xE74C3C)
    await interaction.response.send_message(embed=embed)

# ======= ⚔️ 指令十九：全公會合力圍剿世界 BOSS 遠征 =======
@bot.tree.command(name="公會遠征", description="【全體成員可參與】集體進攻圍剿當前公會的世界 BOSS，共享神話戰利品大獎禮包！")
async def attack_boss(interaction: discord.Interaction):
    await interaction.response.defer()
    user_id = interaction.user.id
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("SELECT guild_name FROM guild_members WHERE user_id=?", (user_id,))
    g_res = c.fetchone()
    if not g_res:
        await interaction.followup.send("❌ 遠征失敗！你必須先加入一個航海公會！", ephemeral=True); conn.close(); return
    g_name = g_res
    c.execute("SELECT current_boss, boss_hp FROM guilds WHERE guild_name=?", (g_name,))
    c_boss, b_hp = c.fetchone()
    if c_boss == "無" or b_hp <= 0:
        await interaction.followup.send("❌ 遠征失敗！目前暫無魔王可以討伐。", ephemeral=True); conn.close(); return
    player_dmg = 10; equipped_weapon = "🦴 徒手肉搏"
    for w_name, w_info in WEAPONS_SHOP.items():
        c.execute("SELECT item_count FROM inventory WHERE user_id=? AND item_name=? AND item_count > 0", (user_id, w_name))
        if c.fetchone(): player_dmg = w_info["dmg"]; equipped_weapon = w_name; break
    crit_roll = random.choice([1.0, 1.0, 1.0, 1.5, 2.0])
    final_dmg = int(player_dmg * crit_roll)
    new_hp = max(0, b_hp - final_dmg)
    c.execute("INSERT INTO boss_damage VALUES (?, ?, ?) ON CONFLICT(guild_name, user_id) DO UPDATE SET dmg_done=dmg_done+?", (g_name, user_id, final_dmg, final_dmg))
    c.execute("UPDATE guilds SET boss_hp=? WHERE guild_name=?", (new_hp, g_name))
    conn.commit()
    crit_msg = "🔥 **【致命一擊】觸發超高倍率暴擊！**\n" if crit_roll > 1.0 else ""
    msg = f"⚔️ **{interaction.user.display_name}** 裝備 【{equipped_weapon}】 投身遠征！\n{crit_msg}💥 輸出傷害：**`{final_dmg}`** Pts！ (❤️ 剩餘血量：`{new_hp} Pts`)\n"
    if new_hp <= 0:
        c.execute("SELECT user_id FROM boss_damage WHERE guild_name=?", (g_name,))
        participants = c.fetchall()
        c.execute("UPDATE guilds SET current_boss='無', boss_hp=0 WHERE guild_name=?", (g_name,))
        conn.commit()
        msg += f"\n🏆 🎉 **【魔王隕落・史詩大捷！】** 🎉 🏆\n🌌 **【全員大獎賞】參與成員（共 {len(participants)} 人）全部獲得戰利品：\n💰 錢包金幣 `+5000 🪙` | `🥳神祕黃金寶箱 x2` | `🔵高級運氣藥水 x3`！**"
        for p_row in participants:
            p_id = p_row
            c.execute("SELECT balance FROM users WHERE user_id=?", (p_id,))
            p_res = c.fetchone()
            if p_res: c.execute("UPDATE users SET balance=? WHERE user_id=?", (int(p_res)+5000, p_id))
            c.execute("INSERT INTO inventory (user_id, item_name, item_count) VALUES (?, '🥳神祕黃金寶箱', 2) ON CONFLICT(user_id, item_name) DO UPDATE SET item_count=item_count+2", (p_id,))
            c.execute("INSERT INTO inventory (user_id, item_name, item_count) VALUES (?, '🔵高級運氣藥水', 3) ON CONFLICT(user_id, item_name) DO UPDATE SET item_count=item_count+3", (p_id,))
        conn.commit()
    conn.close(); await interaction.followup.send(msg)

# ======= 🗺️ 指令二十：解鎖地幔隱藏地圖 =======
@bot.tree.command(name="解鎖隱藏島嶼", description="當你累積完成日常任務且實力足夠時，永久解鎖四海・諸神黃昏地幔隱藏海域！")
async def unlock_hidden_map(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    if user["level"] < 220:
        await interaction.response.send_message(f"❌ 破譯失敗！船長實力需要達到 `LV.220`！(你目前只有 `LV.{user['level']}`)", ephemeral=True)
        return
    if user["balance"] < 15000:
        await interaction.response.send_message(f"❌ 破譯手札失敗！需要支付 `15000` 金幣的研究費，你目前只有 `{user['balance']}` 🪙。", ephemeral=True)
        return
    if "四海・地幔熔岩禁地" in MAPS:
        await interaction.response.send_message("❌ 老哥，你的航海日誌上早就已經破譯並解鎖這片隱藏地幔禁地了！", ephemeral=True)
        return
        
    MAPS["四海・地幔熔岩禁地"] = {
        "req_lvl": 220, "cost": 5000, "npc": "👁️ 覺醒老哥本人",
        "desc": "完全脫離三海控制的終極破碎虛空！這裡充滿百萬倍變異磁場，只出產終極突變首綴的作者級究極產物！",
        "image": "https://imgur.com", "shop": {"🏆 任務大師榮譽紀念竿": 1}
    }
    update_user(user_id, balance=user["balance"]-15000)
    embed = discord.Embed(title="🌌 ── 航海禁忌突破：隱藏島嶼解鎖！ ── 🌌", description=f"🎉 成功破譯遠古公會手札！\n\n🧭 **新航線**：【**四海・地幔熔岩禁地**】永久解鎖！", color=0x9B59B6)
    await interaction.response.send_message(embed=embed)

# ======= 📘 指令二十一：物種收藏圖鑑系統 =======
@bot.tree.command(name="查看圖鑑", description="查看你在四大海域（一海、二海、三海、地幔）中所成功解鎖的所有特產魚獲物種圖鑑進度")
async def view_encyclopedia(interaction: discord.Interaction):
    user_id = interaction.user.id
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS fish_encyclopedia (user_id INTEGER, fish_name TEXT, PRIMARY KEY(user_id, fish_name))")
    c.execute("SELECT fish_name FROM fish_encyclopedia WHERE user_id=?", (user_id,))
    unlocked_fishes = [row[0] for row in c.fetchall()]
    conn.close()
    
    embed = discord.Embed(title=f"📘 {interaction.user.display_name} 的大航海・世界物種百科圖鑑", description="`──────────────────────────`", color=0x34495E)
    for m_name, rarity_dict in MAP_EXCLUSIVE_FISH.items():
        all_map_fishes = []
        for rarity, f_list in rarity_dict.items():
            for fname, _ in f_list:
                if fname not in all_map_fishes: all_map_fishes.append(fname)
        unlocked_count = sum(1 for fish in all_map_fishes if any(fish in uf for uf in unlocked_fishes))
        detail_lines = [f"• ✅ **{fish}**" if any(fish in uf for uf in unlocked_fishes) else f"• 🔒 *未探索生物*" for fish in all_map_fishes]
        embed.add_field(name=f"🚢 【{m_name}】 (進度: {unlocked_count}/{len(all_map_fishes)} 🪐)", value="\n".join(detail_lines) if detail_lines else "暫無產物", inline=False)
    await interaction.response.send_message(embed=embed)

# ──────────────────────────────────────────────────────────
# 🛑 0 空格區域：全專案的最底層啟動入口（必須完全頂格靠左，絕對不能留空白！）
init_db()
keep_alive()
DISCORD_CODE = os.getenv("DISCORD_TOKEN")
bot.run(DISCORD_CODE)
