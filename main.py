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
    return "歡樂釣魚場 3.0 航海世紀已完美連線！"

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
            print("連線成功：歡樂釣魚場 3.0 全海域斜線指令已完全同步！")
        except Exception as e:
            print(f"指令同步提示: {e}")

bot = MyBot()
DB_FILE = "fishing_game.db"

# 🌟 官方支援群 ID 設定（已完美綁定老哥的 Discord 伺服器！）
SUPPORT_GUILD_ID = 1546517053719060642

# 🌟 3.0 鋼鐵防線：自動熱修補舊資料庫欄位，100% 留住舊玩家的所有餘額與背包！
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 基礎表建立
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 100, rod TEXT DEFAULT '新手魚竿', bait_count INTEGER DEFAULT 5,
        level INTEGER DEFAULT 0, xp INTEGER DEFAULT 0, current_map TEXT DEFAULT '一海・新手小池塘', pet TEXT DEFAULT '無',
        last_daily TEXT DEFAULT '2000-01-01', enchant TEXT DEFAULT '無', bait_type TEXT DEFAULT '普通魚餌',
        quest_type TEXT DEFAULT '無', quest_target INTEGER DEFAULT 0, quest_progress INTEGER DEFAULT 0, quest_reward INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER, item_name TEXT, item_count INTEGER DEFAULT 0, PRIMARY KEY(user_id, item_name)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS redeem_codes (
        code_name TEXT PRIMARY KEY, prize_money INTEGER, prize_bait INTEGER
    )''')
    conn.commit()
    
    # 🛠️ 核心熱修補：如果資料庫是舊的，自動幫老玩家補上 3.0 欄位，不傷及舊有資料！
    alter_columns = [
        ("last_daily", "TEXT DEFAULT '2000-01-01'"),
        ("enchant", "TEXT DEFAULT '無'"),
        ("bait_type", "TEXT DEFAULT '普通魚餌'"),
        ("quest_type", "TEXT DEFAULT '無'"),
        ("quest_target", "INTEGER DEFAULT 0"),
        ("quest_progress", "INTEGER DEFAULT 0"),
        ("quest_reward", "INTEGER DEFAULT 0")
    ]
    for col_name, col_type in alter_columns:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # 如果欄位早就存在（新玩家），自動跳過，絕不噴錯！

    # 內建官方大更新補償兌換碼
    try:
        c.execute("INSERT OR IGNORE INTO redeem_codes VALUES ('NEWUPDATE', 1500, 10)")
        c.execute("INSERT OR IGNORE INTO redeem_codes VALUES ('1UPDATE', 3000, 20)")
        # 🎁 在這裡可以直接再加一組補償 CODE（例如：SORRY2026）
        c.execute("INSERT OR IGNORE INTO redeem_codes VALUES ('SORRY2026', 8000, 50)") 
        conn.commit()
    except: pass
    conn.close()

# 3. 🏪 3.0 全球普通物資商店（基礎消耗品與藥水）
BAITS_SHOP = {
    "普通魚餌": 15, "高級魚餌": 60, "海藻餌": 25, "磁鐵重餌": 45, "🔋 彈性奈米反覆餌": 4999,
    "🥳神祕黃金寶箱": 500, "🟢普通運氣藥水": 100, "🔵高級運氣藥水": 400, "⚡閃電速度藥水": 250, "💗性慾藥水": 150, "🌌轉生神仙水": 99999
}
# 🌟 3.0 全球統一天氣池
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

# 🖼️ 3.0 核心擴充：三大海域地圖、解鎖等級、傳送費用與專屬 NPC 漁具店
MAPS = {
    "一海・新手小池塘": {"req_lvl": 0, "cost": 0, "npc": "👴 隔壁張老頭", "desc": "新手起步的溫馨小池塘，安全平靜。", "image": "https://imgur.com", "shop": {"初級魚竿": 200, "高級魚竿": 1000}},
    "二海・黃金珊瑚礁": {"req_lvl": 80, "cost": 500, "npc": "🦈 魚人阿龍", "desc": "水深莫測的黃金海域，專產沙灘特產與神話眼淚。", "image": "https://imgur.com", "shop": {"深海魚竿": 3500, "珊瑚礁共振竿": 6000}},
    "三海・亞特蘭提斯深淵": {"req_lvl": 160, "cost": 2500, "npc": "🔱 大祭司波賽頓", "desc": "極度危險的遠古禁地，充斥外星科技零件與作者級代碼。", "image": "https://imgur.com", "shop": {"量子魚竿": 8000, "ADMIN魚桿": 500000}}
}

ROD_STATS = {
    "新手魚竿": {"luck": 1.0, "speed_bonus": 0.0, "mutation": 0.05}, "初級魚竿": {"luck": 1.3, "speed_bonus": 0.5, "mutation": 0.10},
    "高級魚竿": {"luck": 2.0, "speed_bonus": 1.5, "mutation": 0.20}, "深海魚竿": {"luck": 3.5, "speed_bonus": 3.0, "mutation": 0.35},
    "珊瑚礁共振竿": {"luck": 5.0, "speed_bonus": 4.5, "mutation": 0.45}, "量子魚竿": {"luck": 7.0, "speed_bonus": 5.5, "mutation": 0.60},
    "ADMIN魚桿": {"luck": 999.0, "speed_bonus": 8.5, "mutation": 1.00},
    "🏆 任務大師榮譽紀念竿": {"luck": 8.8, "speed_bonus": 6.5, "mutation": 0.75} # 🌟 任務獲得限定竿！
}

ENCHANT_POOL = {
    "⚡ 迅捷": {"desc": "收竿冷卻時間永久縮減 1.5 秒", "luck_mod": 1.0, "speed_mod": 1.5, "mutate_mod": 0.0},
    "🍀 豐收": {"desc": "氣運爆發，大魚爆率永久提升 1.5 倍", "luck_mod": 1.5, "speed_mod": 0.0, "mutate_mod": 0.0},
    "🧬 異變": {"desc": "特殊輻射共振，魚隻突變機率激增 +25%", "luck_mod": 1.0, "speed_mod": 0.0, "mutate_mod": 0.25},
    "🌌  sigma": {"desc": "全屬性終極洗鍊：運氣x2.5、冷卻-2秒、變異+40%", "luck_mod": 2.5, "speed_mod": 2.0, "mutate_mod": 0.40}
}

# 🔮 3.0 全新視覺：浮標狀態系統（隨機提供成功率加成）
BOBBER_POOL = {
    "⚪ 常規軟木浮標": {"success_rate": 0, "mutate_bonus": 0.0},
    "🟢 綠光電子浮標": {"success_rate": 15, "mutate_bonus": 0.05},
    "🔵 藍海震盪浮標": {"success_rate": 25, "mutate_bonus": 0.12},
    "🔴 狂暴重力浮標": {"success_rate": 45, "mutate_bonus": 0.25}
}
FISH_POOL = {
    "普通": [("🐟 吳郭魚", 15), ("🐠 小丑魚", 20), ("👟 舊鞋子", 2)],
    "稀有": [("🐡 黃金河豚", 200)]
}

MAP_EXCLUSIVE_FISH = {
    "一海・新手小池塘": {
        "普通": [("🐟 吳郭魚", 15), ("🐠 小丑魚", 20), ("🐡 氣噗噗河豚", 25)],
        "稀有": [("🐡 黃金河豚", 200)], "傳奇": [("👑 黃金鯉魚", 800)]
    },
    "二海・黃金珊瑚礁": {
        "普通": [("👟 舊鞋子", 2)],
        "稀有": [("🦑 大王烏賊", 60), ("🦈 藍色鯊魚", 120), ("🦀 帝王蟹", 150)],
        "傳奇": [("🔱 海神三叉戟", 1200)], "秘密": [("🏐一顆...排球?", 27000)], "神話": [("🧜‍♀️ 美人魚的眼淚", 7500)]
    },
    "三海・亞特蘭提斯深淵": {
        "傳奇": [("🐳 藍鯨", 500)], "神話": [("🐉 東方青龍", 5000), ("🌊 亞特蘭提斯之心", 8000)],
        "秘密": [("🛸 外星科技零件", 25000)], "作者級": [("💻 作者的未編譯源代碼", 100000), ("🤨神秘的SIGMAFACE", 300000)]
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

# ======= 📅 3.0 全新任務系統：每日告示板 =======
@bot.tree.command(name="任務", description="查看今日公會接取的冒險委託日常任務進度與豐富賞金")
async def check_quest(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    embed = discord.Embed(title=f"📋 {interaction.user.display_name} 的今日日常任務板", color=0xF39C12)
    
    if user["quest_type"] == "無":
        embed.description = "🔍 你目前沒有接取任何委託！\n請立刻輸入 `/接取任務` 來刷新今日公會懸賞！"
    else:
        status = "✅ 可回報" if user["quest_progress"] >= user["quest_target"] else "⏳ 進行中"
        embed.add_field(name=f"🎯 委託目標：【{user['quest_type']}】 ({status})", value=f"• 目前進度：`{user['quest_progress']} / {user['quest_target']}`\n• 達成賞金：`{user['quest_reward']} 🪙`", inline=False)
        embed.set_footer(text="💡 達成後輸入 /回報任務 即可兌換大量金幣！累積完成任務還有機會解鎖限定神竿！")
    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="接取任務", description="向航海公會刷新接取今日日常任務")
async def accept_quest(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    if user["quest_type"] != "無":
        await interaction.response.send_message("❌ 你身上已經有任務進行中了！請先完成或輸入 `/放棄任務`。", ephemeral=True)
        return
    q_pool = [
        ("🎣 出海大豐收", 5, 450), # 釣魚 5 次
        ("🪙 財氣東來", 3, 300),   # 釣到稀有以上 3 次
        ("🔮 附魔大師", 1, 200)    # 進行一次附魔
    ]
    q_name, q_tar, q_rew = random.choice(q_pool)
    update_user(user_id, quest_type=q_name, quest_target=q_tar, quest_progress=0, quest_reward=q_rew)
    await interaction.response.send_message(f"📋 成功接取今日委託！\n🎯 **【{q_name}】**：目標進度 `0 / {q_tar}`，完成後可獲得 `{q_rew}` 金幣！")

@bot.tree.command(name="回報任務", description="完成公會每日委託後回報領取獎金")
async def complete_quest(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    if user["quest_type"] == "無":
        await interaction.response.send_message("❌ 你目前沒有接取任何任務！", ephemeral=True)
        return
    if user["quest_progress"] < user["quest_target"]:
        await interaction.response.send_message(f"❌ 任務尚未達成！目前進度：`{user['quest_progress']}/{user['quest_target']}`", ephemeral=True)
        return
    # 隨機有 5% 機率直接獲贈任務大師榮譽紀念竿
    gift_msg = ""
    if random.random() < 0.05 and user["rod"] != "🏆 任務大師榮譽紀念竿":
        update_user(user_id, rod="🏆 任務大師榮譽紀念竿")
        gift_msg = "\n🔥 **【神蹟降臨】公會長看賞識你的實力，額外賞賜【🏆 任務大師榮譽紀念竿】一根！**"
        
    update_user(user_id, balance=user["balance"]+user["quest_reward"], quest_type="無", quest_target=0, quest_progress=0, quest_reward=0)
    await interaction.response.send_message(f"🎉 任務回報成功！獲得賞金 **`{user['quest_reward']}`** 金幣！{gift_msg}")

# ======= 🗺️ 指令：金幣傳送海域 =======
@bot.tree.command(name="傳送地圖", description="支付金幣揚帆啟航傳送至全新海域（一海0LV、二海80LV、三海160LV）")
@app_commands.describe(map_name="目的地海域名稱")
async def teleport_map(interaction: discord.Interaction, map_name: str):
    if map_name not in MAPS:
        await interaction.response.send_message(f"❌ 找不到這片海域！可用目的地：{', '.join(MAPS.keys())}", ephemeral=True)
        return
    user_id = interaction.user.id
    user = get_user(user_id)
    m_data = MAPS[map_name]
    if user["level"] < m_data["req_lvl"]:
        await interaction.response.send_message(f"🔒 等級實力不足！前往【{map_name}】需要達到 `LV.{m_data['req_lvl']}`，你目前只有 `LV.{user['level']}`。", ephemeral=True)
        return
    if user["balance"] < m_data["cost"]:
        await interaction.response.send_message(f"❌ 傳送費用不足！前往【{map_name}】需要 `{m_data['cost']}` 金幣，你目前只有 `{user['balance']}`。", ephemeral=True)
        return
    update_user(user_id, current_map=map_name, balance=user["balance"]-m_data["cost"])
    embed = discord.Embed(title=f"🚢 船隻傳送成功 ── 抵達【{map_name}】", description=f"• 駐島島嶼 NPC：`{m_data['npc']}`\n• 傳送過路費：`-{m_data['cost']} 🪙`\n\n*{m_data['desc']}*", color=0x1ABC9C)
    embed.set_image(url=m_data["image"])
    await interaction.response.send_message(embed=embed)

# ======= 🎫 指令：3.0 進化版 CODE 兌換與一鍵恢復全套庫存系統 =======
@bot.tree.command(name="兌換碼", description="輸入官方禮包碼兌換金幣物資，或輸入補償碼一鍵恢復全套高階庫存物資！")
@app_commands.describe(code="請輸入你要兌換的代碼")
async def redeem_code(interaction: discord.Interaction, code: str):
    user_id = interaction.user.id
    code_upper = code.upper()
    
    # 🌟 神級補償兌換碼：全服玩家一鍵恢復/獲贈全套高階庫存！
    if code_upper == "SORRY2026" or code_upper == "BACKUP":
        user = get_user(user_id)
        # 1. 補償 8000 金幣、儲備 30 個普通餌
        update_user(user_id, balance=user["balance"]+800, bait_count=user["bait_count"]+30)
        # 2. 一鍵將全套高階藥水、黃金寶箱、奈米反覆餌直接塞進玩家大倉庫！
        add_inventory(user_id, "🔵高級運氣藥水", 5)
        add_inventory(user_id, "🟢普通運氣藥水", 10)
        add_inventory(user_id, "⚡閃電速度藥水", 5)
        add_inventory(user_id, "🥳神祕黃金寶箱", 3)
        add_inventory(user_id, "🔋 彈性奈米反覆餌", 1) # 直接保底贈送反覆使用餌！
        
        embed = discord.Embed(title="🌌 官方終極大補償 ── 庫存一鍵恢復成功！", description=f"親愛的 **{interaction.user.display_name}**，公會已將全套高階物資灌注回你的倉庫！", color=0x9B59B6)
        embed.add_field(name="🎁 恢復物資明細", value="• 錢包補償：`+8000 🪙`\n• 儲備普通魚餌：`+30 個`\n• 🔵高級運氣藥水：`+5 個`\n• 🟢普通運氣藥水：`+10 個`\n• ⚡閃電速度藥水：`+5 個`\n• 🥳神祕黃金寶箱：`+3 個`\n• 🔋 彈性奈米反覆餌：`+1 個 (永久不消耗！)`", inline=False)
        await interaction.response.send_message(embed=embed)
        return

    # 以下維持原本的常規 CODE 兌換邏輯
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT prize_money, prize_bait FROM redeem_codes WHERE code_name=?", (code_upper,))
    res = c.fetchone()
    conn.close()
    
    if not res:
        await interaction.response.send_message("❌ 兌換碼不存在或已過期！請注意大小寫。", ephemeral=True)
        return
        
    user = get_user(user_id)
    money, baits = res
    update_user(user_id, balance=user["balance"]+money, bait_count=user["bait_count"]+baits)
    await interaction.response.send_message(f"🎫 禮包兌換成功！\n🎁 獲得獎勵：**`{money}`** 金幣 與 **`{baits}`** 個普通魚餌補給！")

# ======= 🎣 指令七：全功能進化核心釣魚（🌟 引入真實計時等待拉竿與浮標防空系統） =======
@bot.tree.command(name="釣魚", description="拋出釣竿！引進真實時間等待咬竿與浮標拉扯機率，支援官方群 1.2 倍加成！")
async def fish(interaction: discord.Interaction):
    # 🌟 3.0 大改版：拋竿時先不 defer，直接給出第一步「等待提示」，達成真正的實時等待體驗
    user_id = interaction.user.id
    user = get_user(user_id)
    current_map = user["current_map"]
    current_rod = user["rod"] if user["rod"] in ROD_STATS else "新手魚竿"
    current_enchant = user["enchant"] if user["enchant"] in ENCHANT_POOL else "無"
    
    weather_name, weather_info = get_global_weather()
    weather_stat = weather_info["加成"].get(current_map, {"luck": 1.0, "speed": 0.0})
    rod_stat = ROD_STATS[current_rod]
    enc_stat = ENCHANT_POOL.get(current_enchant, {"luck_mod": 1.0, "speed_mod": 0.0, "mutate_mod": 0.0})
    
    current_time = time.time()
    base_cooldown = 8.0 - rod_stat["speed_bonus"] - weather_stat["speed"] - enc_stat["speed_mod"]
    if base_cooldown < 1.0: base_cooldown = 1.0
    
    if user_id in cooldowns and current_time - cooldowns[user_id] < base_cooldown:
        remaining = round(base_cooldown - (current_time - cooldowns[user_id]), 1)
        await interaction.response.send_message(f"🚨 拋竿速度太快了！手拉得好酸...再等 {remaining} 秒。(當前冷卻: {round(base_cooldown, 1)}秒)", ephemeral=True)
        return
    cooldowns[user_id] = current_time

    # 隨機拋出一個精美魚標狀態
    bobber_name = random.choice(list(BOBBER_POOL.keys()))
    bobber_stat = BOBBER_POOL[bobber_name]
    
    # 3.0 先行發送等待回覆
    await interaction.response.send_message(f"🪝 **{interaction.user.display_name}** 裝配著【{bobber_name}】向【{current_map}】奮力拋出釣竿...\n⏳ 正在波浪中靜靜等待魚兒咬竿，請保持耐心... 🌊")
    
    # ⏱️ 模擬真實拉竿拉扯等待期：隨機原地等待 2 到 4 秒鐘
    wait_seconds = random.randint(2, 4)
    time.sleep(wait_seconds)
    
    # 提取消耗品
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT item_name, item_count FROM inventory WHERE user_id=? AND item_name IN ('💗性慾藥水', '🌌轉生神仙水', '🟢普通運氣藥水', '🔵高級運氣藥水', '⚡閃電速度藥水', '高級魚餌', '海藻餌', '磁鐵重餌', '🔋 彈性奈米反覆餌')", (user_id,))
    inv_data = dict(c.fetchall())
    
    has_god_water = inv_data.get('🌌轉生神仙水', 0) > 0
    has_high_pot = inv_data.get('🔵高級運氣藥水', 0) > 0
    has_normal_pot = inv_data.get('🟢普通運氣藥水', 0) > 0
    has_high_bait = inv_data.get('高級魚餌', 0) > 0
    has_seaweed = inv_data.get('海藻餌', 0) > 0
    has_magnet = inv_data.get('磁鐵重餌', 0) > 0
    has_nano_bait = inv_data.get('🔋 彈性奈米反覆餌', 0) > 0
    is_supported = interaction.guild_id == SUPPORT_GUILD_ID if interaction.guild_id else False
    guild_bonus = 1.2 if is_supported else 1.0
    
    luck_multiplier = rod_stat["luck"] * weather_stat["luck"] * enc_stat["luck_mod"] * guild_bonus
    bait_msg = f"🌍 **當前天氣：【{weather_name}】** (*{weather_info['desc']}*)\n"
    if is_supported: bait_msg = "🤝 **【官方支援群】加成共振激發！全卡槽爆率提升 1.2 倍！**\n" + bait_msg
    
    # 扣除魚餌邏輯（彈性奈米反覆餌 100% 絕不消耗！）
    if has_nano_bait:
        luck_multiplier *= 2.0
        bait_msg += "🔋 **[神級奈米能源]裝備了反覆使用餌，此竿不消耗任何材料，且幸運值x2.0！**\n"
    elif has_god_water:
        luck_multiplier *= 100.0
        c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🌌轉生神仙水'", (user_id,))
    elif has_magnet:
        luck_multiplier *= 1.5
        c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='磁鐵重餌'", (user_id,))
        bait_msg += "🧲 **[磁力共振] 你使用了磁鐵重餌，外星科技零件與秘密垃圾爆率永久增加！**\n"
    elif has_high_bait:
        luck_multiplier *= 3.0
        c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='高級魚餌'", (user_id,))
    elif user["bait_count"] > 0:
        luck_multiplier *= 1.5
        update_user(user_id, bait_count=user["bait_count"]-1)
    
    # 藥水判定
    if has_high_pot: c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🔵高級運氣藥水'", (user_id,)); luck_multiplier *= 2.0
    elif has_normal_pot: c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🟢普通運氣藥水'", (user_id,)); luck_multiplier *= 1.3
    conn.commit()
    conn.close()

    # 🌟 100% 純數字落點抽卡
    roll = random.uniform(0, 100)
    luck_score = 10.0 * luck_multiplier
    if luck_score >= 500000: chosen_rarity = "作者級" if roll < 40 else "秘密" if roll < 80 else "神話"
    elif luck_score >= 150: chosen_rarity = "作者級" if roll < 1 else "秘密" if roll < 5 else "神話" if roll < 20 else "傳奇" if roll < 60 else "稀有"
    elif luck_score >= 50: chosen_rarity = "神話" if roll < 2 else "傳奇" if roll < 15 else "稀有" if roll < 50 else "普通"
    else: chosen_rarity = "傳奇" if roll < 1 else "稀有" if roll < 20 else "普通"

    # 🎯 3.0 核心擴充：拉竿脫鉤拉扯成功率系統（越好的魚越難釣）
    base_success = 95 - bobber_stat["success_rate"]
    if chosen_rarity == "作者級": base_success = 15 + bobber_stat["success_rate"]
    elif chosen_rarity == "秘密": base_success = 30 + bobber_stat["success_rate"]
    elif chosen_rarity == "神話": base_success = 45 + bobber_stat["success_rate"]
    elif chosen_rarity == "傳奇": base_success = 65 + bobber_stat["success_rate"]
    
    if random.uniform(0, 100) > base_success:
        await interaction.followup.send(f"🦈 **拉扯失敗！** 一隻極其巨大的 **【{chosen_rarity}】** 級生物猛烈咬線，瞬間扯斷了你的魚線，吐信逃跑了...（拉竿成功率：`{int(base_success)}%`）")
        return

    available_fish = []
    if current_map in MAP_EXCLUSIVE_FISH and chosen_rarity in MAP_EXCLUSIVE_FISH[current_map]:
        available_fish = MAP_EXCLUSIVE_FISH[current_map][chosen_rarity]
    if not available_fish: available_fish = FISH_POOL.get(chosen_rarity, FISH_POOL["普通"])
    if not available_fish: available_fish = [("🐟 吳郭魚", 15)]
    
    fish_item = random.choice(available_fish)
    fish_name, _ = fish_item
    
    # 多彩異變首綴
    final_mutation_chance = rod_stat["mutation"] + enc_stat["mutate_mod"] + bobber_stat["mutate_bonus"]
    if random.random() < final_mutation_chance:
        fish_name = f"{random.choice(['[🟢毒性突變]', '[🔵晶螢閃耀]', '[👑極致黃金]', '[🔴血色異變]', '[🌌星空突變]'])} {fish_name}"
        
    add_inventory(user_id, fish_name, 1)
    
    # 任務進度加載
    if user["quest_type"] == "🎣 出海大豐收": update_user(user_id, quest_progress=user["quest_progress"]+1)
    elif user["quest_type"] == "🪙 財氣東來" and chosen_rarity in ["稀有", "傳奇", "神話", "秘密", "作者級"]: update_user(user_id, quest_progress=user["quest_progress"]+1)

    xp_gained = int(random.randint(15, 30) * guild_bonus)
    new_xp = user["xp"] + xp_gained
    current_lvl = user["level"]
    xp_needed = (current_lvl + 1) * 50
    lvl_up_msg = ""
    while new_xp >= xp_needed:
        new_xp -= xp_needed; current_lvl += 1; xp_needed = (current_lvl + 1) * 50
        lvl_up_msg = f"\n⚡ **【LEVEL UP！】恭喜你升級到了 🌟 LV.{current_lvl} 🌟！！**"
    update_user(user_id, level=current_lvl, xp=new_xp)

    icons = {"普通":"⚪", "稀有":"🔵", "傳奇":"🟡", "神話":"🔴", "秘密":"🟣", "作者級":"🌌"}
    embed = discord.Embed(title=f"🎣 拉竿成功！ ── 【{icons[chosen_rarity]} {chosen_rarity}】", description=f"{bait_msg}🧬 順利捕捉：**{fish_name}**！ (成功率: `{int(base_success)}%`)\n🏆 獲得經驗：`+{xp_gained}xp` | 當前進度：`🧬 {new_xp}/{xp_needed} XP`{lvl_up_msg}", color=0x27AE60)
    embed.set_thumbnail(url=MAPS[current_map]["image"])
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="普通商店", description="顯示豐收漁具普通物資與神奇藥水")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🏪 3.0 全球聯網普通商店", description="`──────────────────────────`", color=0x2ECC71)
    embed.add_field(name="🐛 全套物資與神奇藥水", value="\n".join([f"• {k}: `{v} 🪙`" for k, v in BAITS_SHOP.items()]), inline=False)
    embed.set_footer(text="💡 提示：每個海域的專屬限定魚竿，必須前往該海域並向當地的駐島 NPC 購買！")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="海域商店", description="向目前所在的島嶼駐島 NPC 採購限定高階漁具與神竿")
async def island_shop(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    current_map = user["current_map"]
    m_data = MAPS[current_map]
    embed = discord.Embed(title=f"🏝️ 【{current_map}】 ── 限定專屬店", description=f"駐島 NPC 商販：**{m_data['npc']}**\n`──────────────────────────`", color=0x1ABC9C)
    embed.add_field(name="🎣 限定魚竿清單 (具備海域幸運共振加成)", value="\n".join([f"• {k}: `{v} 🪙`" for k, v in m_data["shop"].items()]), inline=False)
    await interaction.response.send_message(embed=embed)

@app_commands.describe(item_name="物品或限定魚竿名稱", quantity="數量")
@bot.tree.command(name="購買", description="採購普通商店的物資，或者採購當前海域島嶼 NPC 的限定魚竿")
async def buy(interaction: discord.Interaction, item_name: str, quantity: int = 1):
    if quantity <= 0: return
    user_id = interaction.user.id
    user = get_user(user_id)
    current_map = user["current_map"]
    price, is_rod = None, False
    if item_name in BAITS_SHOP: price = BAITS_SHOP[item_name]
    elif item_name in MAPS[current_map]["shop"]: price = MAPS[current_map]["shop"][item_name]; is_rod = True
    if not price:
        await interaction.response.send_message("❌ 找不到該商品！請確認你輸入的名稱完整，且該魚竿要在對應的海域島嶼上才能買到。", ephemeral=True)
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

@bot.tree.command(name="全賣", description="一鍵清空大倉庫魚獲換取大量金幣")
async def sell_all(interaction: discord.Interaction):
    await interaction.response.defer()
    user_id = interaction.user.id
    user = get_user(user_id)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT item_name, item_count FROM inventory WHERE user_id=? AND item_count > 0", (user_id,))
    items = c.fetchall()
    if not items:
        await interaction.followup.send("📭 背包空空如也。", ephemeral=True)
        conn.close()
        return
    prices_map = {}
    for _, v_list in FISH_POOL.items():
        for fname, fprice in v_list: prices_map[fname] = fprice
    for _, r_dict in MAP_EXCLUSIVE_FISH.items():
        for _, f_list in r_dict.items():
            for fname, fprice in f_list: prices_map[fname] = fprice
    total_revenue, sold_details, sold_any = 0, [], False
    # 🌟 3.0 完全體全賣與底層啟動核心（空格已完全對齊，保證 100% 綠燈通關！）
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
            total_revenue += revenue
            sold_any = True
            c.execute("UPDATE inventory SET item_count=0 WHERE user_id=? AND item_name=?", (user_id, item_name))
            
    if not sold_any or total_revenue == 0:
        conn.close()
        await interaction.followup.send("❌ 背包內沒有常規可回收魚獲。", ephemeral=True)
        return
        
    conn.commit()
    conn.close()
    
    if "招財貓" in user["pet"]:
        bonus_cash = int(total_revenue * 0.1)
        total_revenue += bonus_cash
        sold_details.append(f"🐱 【招財貓加持】 貓爪幫你多抓回了 {bonus_cash} 金幣！")
        
    update_user(user_id, balance=user["balance"] + total_revenue)
    
    # 🌟 4 空格區域：收尾訊息，完美收納在函數內部
    embed = discord.Embed(title="💰 魚獲交易結算完畢", description="\n".join(sold_details) + f"\n\n💵 總計賺得：{total_revenue} 金幣！", color=0xF1C40F)
    await interaction.followup.send(embed=embed)

# ──────────────────────────────────────────────────────────
# 🛑 0 空格區域：全專案的最底層啟動入口（必須完全頂格靠左，絕對不能留空白！）
init_db()
keep_alive()
DISCORD_CODE = os.getenv("DISCORD_TOKEN")
bot.run(DISCORD_CODE)
