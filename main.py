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

# 🌐 Flask 網頁製造機（保持 24h 不休息）
app = Flask('')

@app.route('/')
def home():
    return "機器人正在 24h 運作中！"

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
            print("連線成功：斜線指令已完全同步至 Discord 官方後台！")
        except Exception as e:
            print(f"指令同步提示: {e}")

bot = MyBot()
# 🌟 持久化硬碟路徑（如果是在本地電腦測試，可以改回 "fishing_game.db"）
DB_FILE = "/data/fishing_game.db"
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

# 2. RPG 資料庫初始化
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 100, rod TEXT DEFAULT '新手魚竿', bait_count INTEGER DEFAULT 5,
        level INTEGER DEFAULT 0, xp INTEGER DEFAULT 0, current_map TEXT DEFAULT '小池塘', pet TEXT DEFAULT '無'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER, item_name TEXT, item_count INTEGER DEFAULT 0, PRIMARY KEY(user_id, item_name)
    )''')
    conn.commit()
    conn.close()

# 3. 🏪 商店道具與高階魚竿屬性加成
RODS_SHOP = {"初級魚竿": 200, "高級魚竿": 1000, "深海魚竿": 3500, "量子魚竿": 8000, "ADMIN魚桿": 500000}
BAITS_SHOP = {
    "普通魚餌": 15, "高級魚餌": 60, "🥳神祕黃金寶箱": 500,
    "🟢普通運氣藥水": 100, "🔵高級運氣藥水": 400, "💗性慾藥水": 150, "🌌轉生神仙水(運氣+1000000%)": 99999
}

ROD_STATS = {
    "新手魚竿": {"luck": 1.0, "speed_bonus": 0.0, "mutation": 0.05},
    "初級魚竿": {"luck": 1.3, "speed_bonus": 0.5, "mutation": 0.10},
    "高級魚竿": {"luck": 2.0, "speed_bonus": 1.5, "mutation": 0.20},
    "深海魚竿": {"luck": 3.5, "speed_bonus": 3.0, "mutation": 0.35},
    "量子魚竿": {"luck": 7.0, "speed_bonus": 5.0, "mutation": 0.60},
    "ADMIN魚桿": {"luck": 999.0, "speed_bonus": 8.5, "mutation": 1.00}
}
# 🌟 全球統一天氣池
WEATHER_POOL = {
    "☀️ 晴空萬里": {
        "desc": "風平浪靜，陽光灑落海面，非常適合出海。",
        "加成": {
            "小池塘": {"luck": 1.0, "speed": 0.0},
            "陽光沙灘": {"luck": 1.2, "speed": 0.5},
            "神祕深海": {"luck": 1.0, "speed": 0.0}
        }
    },
    "🌧️ 狂風暴雨": {
        "desc": "大雨傾盆，海浪洶湧，魚群紛紛浮上水面呼吸！",
        "加成": {
            "小池塘": {"luck": 1.5, "speed": -1.0},
            "陽光沙灘": {"luck": 1.8, "speed": -1.0},
            "神祕深海": {"luck": 1.3, "speed": -0.5}
        }
    },
    "🌫️ 濃霧密佈": {
        "desc": "海上大霧遮蔽視線，魚兒容易受驚，收竿需格外小心。",
        "加成": {
            "小池塘": {"luck": 0.8, "speed": 0.5},
            "陽光沙灘": {"luck": 0.7, "speed": 1.0},
            "神祕深海": {"luck": 0.9, "speed": 0.0}
        }
    },
    "🌌 天降異象": {
        "desc": "星海與遠古神光撕裂天空！各地湧現傳奇特產潮汐！",
        "加成": {
            "小池塘": {"luck": 2.0, "speed": 1.0},
            "陽光沙灘": {"luck": 3.0, "speed": 2.0},
            "神祕深海": {"luck": 5.0, "speed": 3.0}
        }
    }
}

def get_global_weather():
    """全服統一時間種子：每 5 分鐘全球所有玩家同步變換一次天氣"""
    time_seed = int(time.time() / 300)
    random.seed(time_seed)
    w_name = random.choice(list(WEATHER_POOL.keys()))
    w_info = WEATHER_POOL[w_name]
    random.seed()  # 還原隨機數
    return w_name, w_info

# 地圖解鎖等級定義
MAPS = {
    "小池塘": {"req_lvl": 0, "desc": "新手起步的溫馨小池塘（出產基礎常規魚獲）"},
    "陽光沙灘": {"req_lvl": 5, "desc": "風光明媚（專屬收穫：沙灘蟹、鯊魚、排球與海神叉）"},
    "神祕深海": {"req_lvl": 15, "desc": "極度危險（專屬收穫：遠古神話生物、外星零件與代碼）"}
}

FISH_POOL = {
    "普通": [("🐟 吳郭魚", 15), ("🐠 小丑魚", 20), ("👟 舊鞋子", 2)],
    "稀有": [("🐡 黃金河豚", 200)]
}

# 地圖限定收穫系統
MAP_EXCLUSIVE_FISH = {
    "小池塘": {
        "普通": [("🐟 吳郭魚", 15), ("🐠 小丑魚", 20), ("🐡 氣噗噗河豚", 25)],
        "稀有": [("🐡 黃金河豚", 200)],
        "傳奇": [("👑 黃金鯉魚", 800)]
    },
    "陽光沙灘": {
        "普通": [("👟 舊鞋子", 2)],
        "稀有": [("🦑 大王烏賊", 60), ("🦈 藍色鯊魚", 120), ("🦀 帝王蟹", 150)],
        "傳奇": [("🔱 海神三叉戟", 1200)],
        "秘密": [("🏐一顆...排球?", 27000)],
        "神話": [("🧜‍♀️ 美人魚的眼淚", 7500)]
    },
    "神祕深海": {
        "傳奇": [("🐳 藍鯨", 500)],
        "神話": [("🐉 東方青龍", 5000), ("🌊 亞特蘭提斯之心", 8000)],
        "秘密": [("🛸 外星科技零件", 25000)],
        "作者級": [("💻 作者的未編譯源代碼", 100000), ("🤨神秘的SIGMAFACE", 300000)]
    }
}
# 4. 資料庫核心工具（🌟 標準拆包解包，徹底終結簽到未回應錯誤）
def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT balance, rod, bait_count, level, xp, current_map, pet FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    if not res:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        c.execute("SELECT balance, rod, bait_count, level, xp, current_map, pet FROM users WHERE user_id=?", (user_id,))
        res = c.fetchone()
    conn.close()
    
    bal, rod, bait, lvl, xp, cmap, pet = res
    return {
        "balance": int(bal), "rod": str(rod), "bait_count": int(bait),
        "level": int(lvl), "xp": int(xp), "current_map": str(cmap), "pet": str(pet)
    }

def update_user(user_id, balance=None, rod=None, bait_count=None, level=None, xp=None, current_map=None, pet=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if balance is not None: c.execute("UPDATE users SET balance=? WHERE user_id=?", (balance, user_id))
    if rod is not None: c.execute("UPDATE users SET rod=? WHERE user_id=?", (rod, user_id))
    if bait_count is not None: c.execute("UPDATE users SET bait_count=? WHERE user_id=?", (bait_count, user_id))
    if level is not None: c.execute("UPDATE users SET level=? WHERE user_id=?", (level, user_id))
    if xp is not None: c.execute("UPDATE users SET xp=? WHERE user_id=?", (xp, user_id))
    if current_map is not None: c.execute("UPDATE users SET current_map=? WHERE user_id=?", (current_map, user_id))
    if pet is not None: c.execute("UPDATE users SET pet=? WHERE user_id=?", (pet, user_id))
    conn.commit()
    conn.close()

def add_inventory(user_id, item_name, amount=1):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO inventory (user_id, item_name, item_count) VALUES (?, ?, ?) ON CONFLICT(user_id, item_name) DO UPDATE SET item_count=item_count+?", (user_id, item_name, amount, amount))
    conn.commit()
    conn.close()

# ======= 📖 指令一：使用教學 =======
@bot.tree.command(name="釣魚說明", description="查看歡樂釣魚場的玩家指南與基本指令")
async def guide(interaction: discord.Interaction):
    embed = discord.Embed(title="🎣 歡樂釣魚場 - 玩家指南", color=0x5865F2)
    embed.add_field(name="🎮 核心功能指令", value="`/釣魚` : 隨機出海釣魚\n`/背包` : 查看個人的屬性面板與當前魚獲\n`/天氣` : 查看當前全服全球天氣同步影響", inline=False)
    embed.add_field(name="🏪 商店與經濟系統", value="`/普通商店` : 採購全套高階漁具與神奇藥水\n`/購買 <物品名稱> [數量]` : 購買特定商品\n`/全賣` : 將背包裡所有的魚獲全部售出換取金幣", inline=False)
    await interaction.response.send_message(embed=embed)

# ======= 全新擴充指令 =======
@bot.tree.command(name="天氣", description="觀測當前全服統一的大氣觀測站與各地圖海域共振影響")
async def current_weather_cmd(interaction: discord.Interaction):
    w_name, w_info = get_global_weather()
    embed = discord.Embed(title=f"🌤️ 全服統一氣象觀測站 ── 當前全球：【{w_name}】", description=f"*{w_info['desc']}*", color=0x3498DB)
    for m_name in MAPS.keys():
        m_stat = w_info["加成"].get(m_name, {"luck": 1.0, "speed": 0.0})
        embed.add_field(name=f"🚢 【{m_name}】海域共振", value=f"運氣效率：`x{m_stat['luck']}`\n冷卻增減：`{'+' if m_stat['speed']>=0 else ''}{m_stat['speed']} 秒`", inline=True)
    await interaction.response.send_message(embed=embed)

# ======= 📅 指令二：每日簽到 =======
@bot.tree.command(name="簽到", description="每日領取 200 金幣與 3 個普通魚餌補給！")
async def daily(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    update_user(user_id, balance=user["balance"]+200, bait_count=user["bait_count"]+3)
    await interaction.response.send_message(f"🎁 **{interaction.user.display_name}** 簽到成功！獲得 `200` 金幣 與 `3` 個普通魚餌！")
# ======= 💸 指令三：玩家匯款轉帳 =======
@bot.tree.command(name="匯款", description="將金幣轉帳給伺服器內的其他玩家")
@app_commands.describe(target="你想匯款給誰？", amount="你想轉帳的金幣數量")
async def transfer(interaction: discord.Interaction, target: discord.Member, amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ 匯款金額必須大於 0！", ephemeral=True)
        return
    if target.id == interaction.user.id:
        await interaction.response.send_message("❌ 你不能匯款給自己！", ephemeral=True)
        return
    sender = get_user(interaction.user.id)
    if sender["balance"] < amount:
        await interaction.response.send_message(f"❌ 餘額不足！你目前只有 {sender['balance']} 金幣。", ephemeral=True)
        return
    receiver = get_user(target.id)
    update_user(interaction.user.id, balance=sender["balance"] - amount)
    update_user(target.id, balance=receiver["balance"] + amount)
    await interaction.response.send_message(f"💸 **{interaction.user.display_name}** 成功匯款了 **{amount}** 金幣給 **{target.display_name}**！")

# ======= 🧰 指令四：神祕黃金寶箱 =======
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
        await interaction.followup.send("❌ 你的背包裡沒有寶箱！請先去商店使用 `/購買 🥳神祕黃金寶箱 1` 採購一個吧！", ephemeral=True)
        conn.close()
        return
    c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🥳神祕黃金寶箱'", (user_id,))
    conn.commit()
    conn.close()
    roll = random.random()
    user = get_user(user_id)
    if roll < 0.05:
        colors_pool = ["🐱 招財貓(金幣+10%)", "🦅 尋寶獵鷹(XP+30%)", "🐉 迷你小青龍(XP+50%)"]
        chosen_pet = random.choice(colors_pool)
        update_user(user_id, pet=chosen_pet)
        await interaction.followup.send(f"🌌 ✨ **【神光降臨！！】** **{interaction.user.display_name}** 成功孵化出極稀有寵物：**{chosen_pet}**！！")
    elif roll < 0.25:
        add_inventory(user_id, "🔵高級運氣藥水", 1)
        await interaction.followup.send(f"🧰 **{interaction.user.display_name}** 打開了黃金寶箱，獲得了：`🔵高級運氣藥水` x1！")
    elif roll < 0.55:
        add_inventory(user_id, "🟢普通運氣藥水", 1)
        await interaction.followup.send(f"🧰 **{interaction.user.display_name}** 打開了黃金寶箱，獲得了：`🟢普通運氣藥水` x1！")
    else:
        bonus_money = random.randint(150, 400)
        update_user(user_id, balance=user["balance"]+bonus_money, bait_count=user["bait_count"]+5)
        await interaction.followup.send(f"🧰 **{interaction.user.display_name}** 打開了黃金寶箱，獲得了：`🪙 {bonus_money} 金幣` 補給與 `🐛 高級魚餌` x5！")

# ======= 🏆 指令五：伺服器天梯排行榜 =======
@bot.tree.command(name="排行榜", description="查看當前伺服器中最強的釣魚大師（依等級與金幣排行）")
async def leaderboard(interaction: discord.Interaction):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, level, balance FROM users ORDER BY level DESC, balance DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    embed = discord.Embed(title="🏆 歡樂釣魚場 - 榮譽天梯排行榜", color=0xF1C40F)
    if not rows:
        embed.description = "目前排行榜上空空如也..."
    else:
        rank_str = ""
        for i, row in enumerate(rows):
            u_id, lvl, bal = row
            member = interaction.guild.get_member(u_id)
            name = member.display_name if member else f"神祕挑戰者({u_id})"
            medal = "🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else f"第 {i+1} 名"
            rank_str += f"{medal} **{name}** ── `LV.{lvl}` | `錢包: {bal} 金幣`\n"
        embed.description = rank_str
    await interaction.response.send_message(embed=embed)
# ======= 🗺️ 指令六：切換冒險地圖 =======
@bot.tree.command(name="地圖", description="切換冒險海域（不同地圖有解鎖等級需求）")
@app_commands.describe(map_name="你想前往哪一張地圖？")
async def change_map(interaction: discord.Interaction, map_name: str):
    if map_name not in MAPS:
        await interaction.response.send_message(f"❌ 找不到這張地圖！可用地圖：{', '.join(MAPS.keys())}", ephemeral=True)
        return
    user_id = interaction.user.id
    user = get_user(user_id)
    req = MAPS[map_name]["req_lvl"]
    if user["level"] < req:
        await interaction.response.send_message(f"🔒 實力不足！前往【{map_name}】需要達到 `LV.{req}`，你目前只有 `LV.{user['level']}`。", ephemeral=True)
        return
    update_user(user_id, current_map=map_name)
    await interaction.response.send_message(f"🚢 **{interaction.user.display_name}** 揚帆啟航！成功進駐新海域：【**{map_name}**】（{MAPS[map_name]['desc']}）")

cooldowns = {}
# ======= 🎣 指令七：全功能進化核心釣魚（🌟 拋棄 W 矩陣 ── 終極無錯版） =======
@bot.tree.command(name="釣魚", description="拋出釣竿！(自動帶出全服天氣及目前地圖海域專屬特產生物！)")
async def fish(interaction: discord.Interaction):
    await interaction.response.defer()
    
    user_id = interaction.user.id
    user = get_user(user_id)
    current_map = user["current_map"]
    current_rod = user["rod"] if user["rod"] in ROD_STATS else "新手魚竿"
    
    weather_name, weather_info = get_global_weather()
    weather_stat = weather_info["加成"].get(current_map, {"luck": 1.0, "speed": 0.0})
    rod_stat = ROD_STATS[current_rod]
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT item_name, item_count FROM inventory WHERE user_id=? AND item_name IN ('💗性慾藥水', '🌌轉生神仙水(運氣+1000000%)', '🟢普通運氣藥水', '🔵高級運氣藥水', '高級魚餌')", 
        (user_id,)
    )
    inv_data = dict(c.fetchall())
    
    has_potion = inv_data.get('💗性慾藥水', 0) > 0
    has_god_water = inv_data.get('🌌轉生神仙水(運氣+1000000%)', 0) > 0
    has_normal_pot = inv_data.get('🟢普通運氣藥水', 0) > 0
    has_high_pot = inv_data.get('🔵高級運氣藥水', 0) > 0
    has_high_bait = inv_data.get('高級魚餌', 0) > 0
    
    current_time = time.time()
    base_cooldown = 10.0
    base_cooldown -= rod_stat["speed_bonus"]
    base_cooldown -= weather_stat["speed"]
    if has_potion: base_cooldown = 3.0
    if base_cooldown < 1.0: base_cooldown = 1.0
    
    if user_id in cooldowns:
        time_passed = current_time - cooldowns[user_id]
        if time_passed < base_cooldown:
            remaining = round(base_cooldown - time_passed, 1)
            await interaction.followup.send(f"🚨 拋竿速度太快了！手拉得好酸...再等 {remaining} 秒。(當前冷卻: {round(base_cooldown, 1)}秒)", ephemeral=True)
            conn.close()
            return
    cooldowns[user_id] = current_time
       luck_multiplier = rod_stat["luck"] * weather_stat["luck"]
    bait_msg = f"🌍 **全服全球天氣：【{weather_name}】** (*{weather_info['desc']}*)\n📈 海域共振影響：運氣 `x{weather_stat['luck']}` | 裝備：**{current_rod}**\n"
    
    # 🌟 徹底拋棄 w 變數：100% 轉化為純數字「幸運積分點數」！
    if has_god_water:
        luck_score = 999999
        c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🌌轉生神仙水(運氣+1000000%)'", (user_id,))
        bait_msg += "🌌 **[神仙降臨]** 你喝下了百萬倍運氣神仙水！！\n"
    else:
        luck_score = 10.0 * luck_multiplier
        if has_high_pot:
            luck_score += 50.0
            c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🔵高級運氣藥水'", (user_id,))
            bait_msg += "🔵 **[運氣沖天]** 喝下高級運氣藥水！\n"
        elif has_normal_pot:
            luck_score += 20.0
            c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🟢普通運氣藥水'", (user_id,))
            bait_msg += "🟢 **[靈氣附體]** 喝下普通運氣藥水！\n"
        if has_high_bait:
            luck_score += 35.0
            c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='高級魚餌'", (user_id,))
            bait_msg += "✨ 你使用了 **高級魚餌**！\n"
        elif user["bait_count"] > 0:
            luck_score += 15.0
            update_user(user_id, bait_count=user["bait_count"]-1)
            bait_msg += "🐛 你消耗了 1 個 **普通魚餌**！\n"
        else:
            bait_msg += "🪝 無魚餌素釣，全憑直覺！\n"

    if has_potion:
        c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='💗性慾藥水'", (user_id,))
        bait_msg = "🔥 **[速度狂暴]** 速度大增！\n" + bait_msg
    conn.commit()
    conn.close()

    # 🌟 2026 終極安全機制：採用純數字隨機落點（0-100），完全不需要 random.choices，100% 阻斷卡死！
    roll = random.uniform(0, 100)
    if luck_score >= 500000: 
        chosen_rarity = "作者級" if roll < 40 else "秘密" if roll < 80 else "神話"
    elif luck_score >= 150: 
        chosen_rarity = "作者級" if roll < 1 else "秘密" if roll < 5 else "神話" if roll < 20 else "傳奇" if roll < 60 else "稀有"
    elif luck_score >= 50: 
        chosen_rarity = "神話" if roll < 2 else "傳奇" if roll < 15 else "稀有" if roll < 50 else "普通"
    else: 
        chosen_rarity = "傳奇" if roll < 1 else "稀有" if roll < 20 else "普通"
    
    # 動態安全地圖特產過濾（防空防閃退 Fallback）
    available_fish = []
    if current_map in MAP_EXCLUSIVE_FISH and chosen_rarity in MAP_EXCLUSIVE_FISH[current_map]:
        available_fish = MAP_EXCLUSIVE_FISH[current_map][chosen_rarity]
    if not available_fish:
        available_fish = FISH_POOL.get(chosen_rarity, FISH_POOL["普通"])
        
    fish_item = random.choice(available_fish)
    fish_name, _ = fish_item
    
    is_mutated = random.random() < rod_stat["mutation"]
    if is_mutated: fish_name = f"{fish_name} [✨變異體]"
    add_inventory(user_id, fish_name, 1)

    xp_gained = random.randint(15, 30)
    pet_msg = ""
    if "尋寶獵鷹" in user["pet"]:
        bonus_xp = int(xp_gained * 0.3)
        xp_gained += bonus_xp
        pet_msg = f"（🦅 獵鷹額外咬回 +{bonus_xp}xp！）"
    elif "迷你小青龍" in user["pet"]:
        bonus_xp = int(xp_gained * 0.5)
        xp_gained += bonus_xp
        pet_msg = f"（🐉 小青龍賜予額外 +{bonus_xp}xp！）"
    elif "招財貓" in user["pet"]: pet_msg = "（🐱 招財貓默默幫你累積財運...）"

    new_xp = user["xp"] + xp_gained
    current_lvl = user["level"]
    xp_needed = (current_lvl + 1) * 50
    lvl_up_msg = ""
    while new_xp >= xp_needed:
        new_xp -= xp_needed
        current_lvl += 1
        xp_needed = (current_lvl + 1) * 50
        lvl_up_msg = f"\n⚡ **【LEVEL UP！】恭喜你升級到了 🌟 LV.{current_lvl} 🌟！！**"
    update_user(user_id, level=current_lvl, xp=new_xp)

    icons = {"普通":"⚪", "稀有":"🔵", "傳奇":"🟡", "神話":"🔴", "秘密":"🟣", "作者級":"🌌"}
    mutate_str = "✨ 🚨 **【驚天異變】拉竿瞬間，你居然捕捉到極稀有的特殊變異物種！**\n" if is_mutated else ""
    msg = f"{bait_msg}{mutate_str}🎣 **{interaction.user.display_name}** 在【{current_map}】拋竿...\n【{icons[chosen_rarity]} {chosen_rarity}】釣到了 **{fish_name}**！(獲得 +{xp_gained}xp {pet_msg} 🧬 {new_xp}/{xp_needed}){lvl_up_msg}"
    if chosen_rarity in ["神話", "秘密", "作者級"] and lvl_up_msg == "":
        msg += "\n🎉 **【世界廣播】全服見證！極致歐皇在海域中撈起了不世珍寶！！** 🎉"
    await interaction.followup.send(msg)

@bot.tree.command(name="普通商店", description="顯示豐收漁具普通商店的道具與藥水")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🏪 豐收漁具普通商店", description="使用 `/購買` 來購買道具、全套運氣藥水與黃金保箱", color=0x2ECC71)
    embed.add_field(name="🎣 升級魚竿 (具備隱藏幸運與變異加成！)", value="\n".join([f"• {k}: {v} 金幣" for k, v in RODS_SHOP.items()]), inline=False)
    embed.add_field(name="🐛 消耗品藥水", value="\n".join([f"• {k}: {v} 金幣 / 個" for k, v in BAITS_SHOP.items()]), inline=False)
    await interaction.response.send_message(embed=embed)

@app_commands.describe(item_name="物品名稱", quantity="數量")
@bot.tree.command(name="購買", description="向商店採購商品道具")
async def buy(interaction: discord.Interaction, item_name: str, quantity: int = 1):
    if quantity <= 0: 
        await interaction.response.send_message("❌ 購買數量必須大於 0！", ephemeral=True)
        return
    user_id = interaction.user.id
    user = get_user(user_id)
    price, is_rod, is_bait = None, False, False
    if item_name in RODS_SHOP: price, is_rod = RODS_SHOP[item_name], True
    elif item_name in BAITS_SHOP: price, is_bait = BAITS_SHOP[item_name], True
    if not price:
        await interaction.response.send_message("❌ 找不到該商品，請確認名稱完整正確。", ephemeral=True)
        return
    total_cost = price * quantity
    if user["balance"] < total_cost:
        await interaction.response.send_message(f"❌ 餘額不足！你需要 {total_cost} 金幣。", ephemeral=True)
        return
    new_balance = user["balance"] - total_cost
    if is_rod:
        update_user(user_id, balance=new_balance, rod=item_name)
        await interaction.response.send_message(f"🛍️ 購買成功！你裝備了 **{item_name}**！")
    elif is_bait:
        update_user(user_id, balance=new_balance)
        add_inventory(user_id, item_name, quantity)
        await interaction.response.send_message(f"🛍️ 購買成功！你將 {quantity} 個 **{item_name}** 收進背包！")

@bot.tree.command(name="背包", description="查看個人屬性與倉庫魚獲")
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
    embed.add_field(name="🌟 冒險家等級", value=f"`LV.{user['level']}` ({user['xp']}/{xp_needed} XP)", inline=True)
    embed.add_field(name="🐾 隨身神獸", value=f"`{user['pet']}`", inline=True)
    embed.add_field(name="🚢 當前海域", value=f"【{user['current_map']}】", inline=True)
    embed.add_field(name="💰 錢包金幣", value=f"`{user['balance']} 🪙`", inline=True)
    embed.add_field(name="🎣 裝備魚竿", value=f"`{user['rod']}`", inline=True)
    embed.add_field(name="🐛 儲備魚餌", value=f"`{user['bait_count']} 個`", inline=True)
    inv_str = "\n".join([f"• {name} x{count}" for name, count in items]) if items else "空空如也"
    embed.add_field(name="🐟 儲存倉庫 (可使用 `/全賣` 變現)", value=inv_str, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="全賣", description="將背包裡所有的常規魚獲全部售出（變異體 1.5 倍金幣！）")
async def sell_all(interaction: discord.Interaction):
    await interaction.response.defer()
    user_id = interaction.user.id
    user = get_user(user_id)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT item_name, item_count FROM inventory WHERE user_id=? AND item_count > 0", (user_id,))
    items = c.fetchall()
    if not items:
        await interaction.followup.send("📭 你的背包裡沒有任何魚獲可以販賣。", ephemeral=True)
        conn.close()
        return
    prices_map = {}
    for _, v_list in FISH_POOL.items():
        for fname, fprice in v_list: prices_map[fname] = fprice
    for _, r_dict in MAP_EXCLUSIVE_FISH.items():
        for _, f_list in r_dict.items():
            for fname, fprice in f_list: prices_map[fname] = fprice
    total_revenue = 0
    sold_details = []
    sold_any = False
    for item_name, count in items:
        base_name = item_name.replace(" [✨變異體]", "")
        if base_name in prices_map:
            revenue = prices_map[base_name] * count
            if " [✨變異體]" in item_name:
                revenue = int(revenue * 1.5)
                sold_details.append(f"• {item_name} x{count} -> 獲得 {revenue} 金幣 (🔥含變異加成)")
            else:
                sold_details.append(f"• {item_name} x{count} -> 獲得 {revenue} 金幣")
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
    embed = discord.Embed(title="💰 魚獲交易結算完畢", color=0xF1C40F)
    embed.description = "\n".join(sold_details) + f"\n\n💵 總計賺得：{total_revenue} 金幣！"
    await interaction.followup.send(embed=embed)

init_db()
keep_alive()
DISCORD_CODE = os.getenv("DISCORD_TOKEN")
bot.run(DISCORD_CODE)
