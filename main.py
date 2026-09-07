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
    return "歡樂釣魚場 2.0 完美連線中！"

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
            print("連線成功：歡樂釣魚場 2.0 斜線指令已完全同步！")
        except Exception as e:
            print(f"指令同步提示: {e}")

bot = MyBot()
DB_FILE = "fishing_game.db"

# 🌟 官方支援群 ID 設定（請在此更換為你 Discord 伺服器的真實 ID）
SUPPORT_GUILD_ID = 123456789012345678

# 2. RPG 資料庫初始化（🌟 擴充支援：last_daily 天氣鎖、enchant 魚竿附體屬性）
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 100, rod TEXT DEFAULT '新手魚竿', bait_count INTEGER DEFAULT 5,
        level INTEGER DEFAULT 0, xp INTEGER DEFAULT 0, current_map TEXT DEFAULT '小池塘', pet TEXT DEFAULT '無',
        last_daily TEXT DEFAULT '2000-01-01', enchant TEXT DEFAULT '無'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER, item_name TEXT, item_count INTEGER DEFAULT 0, PRIMARY KEY(user_id, item_name)
    )''')
    conn.commit()
    conn.close()

# 3. 🏪 商店升級大擴充（新增：⚡閃電速度藥水）
RODS_SHOP = {"初級魚竿": 200, "高級魚竿": 1000, "深海魚竿": 3500, "量子魚竿": 8000, "ADMIN魚桿": 500000}
BAITS_SHOP = {
    "普通魚餌": 15, "高級魚餌": 60, "🥳神祕黃金寶箱": 500,
    "🟢普通運氣藥水": 100, "🔵高級運氣藥水": 400, "⚡閃電速度藥水": 250, "💗性慾藥水": 150, "🌌轉生神仙水(運氣+1000000%)": 99999
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
        "加成": {"小池塘": {"luck": 1.0, "speed": 0.0}, "陽光沙灘": {"luck": 1.2, "speed": 0.5}, "神祕深海": {"luck": 1.0, "speed": 0.0}}
    },
    "🌧️ 狂風暴雨": {
        "desc": "大雨傾盆，海浪洶湧，魚群紛紛浮上水面呼吸！",
        "加成": {"小池塘": {"luck": 1.5, "speed": -1.0}, "陽光沙灘": {"luck": 1.8, "speed": -1.0}, "神祕深海": {"luck": 1.3, "speed": -0.5}}
    },
    "🌫️ 濃霧密佈": {
        "desc": "海上大霧遮蔽視線，魚兒容易受驚，收竿需格外小心。",
        "加成": {"小池塘": {"luck": 0.8, "speed": 0.5}, "陽光沙灘": {"luck": 0.7, "speed": 1.0}, "神祕深海": {"luck": 0.9, "speed": 0.0}}
    },
    "🌌 天降異象": {
        "desc": "星海與遠古神光撕裂天空！各地湧現傳奇特產潮汐！",
        "加成": {"小池塘": {"luck": 2.0, "speed": 1.0}, "陽光沙灘": {"luck": 3.0, "speed": 2.0}, "神祕深海": {"luck": 5.0, "speed": 3.0}}
    }
}

def get_global_weather():
    time_seed = int(time.time() / 300)
    random.seed(time_seed)
    w_name = random.choice(list(WEATHER_POOL.keys()))
    w_info = WEATHER_POOL[w_name]
    random.seed()
    return w_name, w_info

# 🖼️ 2.0 核心擴充：地圖全面綁定精美網址圖片
MAPS = {
    "小池塘": {"req_lvl": 0, "desc": "新手起步的溫馨小池塘（出產基礎常規魚獲）", "image": "https://imgur.com"},
    "陽光沙灘": {"req_lvl": 5, "desc": "風光明媚（專屬收穫：沙灘蟹、鯊魚、排球與海神叉）", "image": "https://imgur.com"},
    "神祕深海": {"req_lvl": 15, "desc": "極度危險（專屬收穫：遠古神話生物、外星零件與代碼）", "image": "https://imgur.com"}
}

# 🔮 2.0 核心擴充：附魔詞條屬性面板
ENCHANT_POOL = {
    "⚡ 迅捷": {"desc": "收竿冷卻時間永久縮減 1.5 秒", "luck_mod": 1.0, "speed_mod": 1.5, "mutate_mod": 0.0},
    "🍀 豐收": {"desc": "氣運爆發，大魚爆率永久提升 1.5 倍", "luck_mod": 1.5, "speed_mod": 0.0, "mutate_mod": 0.0},
    "🧬 異變": {"desc": "特殊輻射共振，魚隻突變機率激增 +25%", "luck_mod": 1.0, "speed_mod": 0.0, "mutate_mod": 0.25},
    "🌌  sigma": {"desc": "全屬性終極洗鍊：運氣x2.5、冷卻-2秒、變異+40%", "luck_mod": 2.5, "speed_mod": 2.0, "mutate_mod": 0.40}
}

FISH_POOL = {
    "普通": [("🐟 吳郭魚", 15), ("🐠 小丑魚", 20), ("👟 舊鞋子", 2)],
    "稀修": [("🐡 黃金河豚", 200)]
}

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
# 4. 資料庫核心工具
def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT balance, rod, bait_count, level, xp, current_map, pet, last_daily, enchant FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    if not res:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        c.execute("SELECT balance, rod, bait_count, level, xp, current_map, pet, last_daily, enchant FROM users WHERE user_id=?", (user_id,))
        res = c.fetchone()
    conn.close()
    
    bal, rod, bait, lvl, xp, cmap, pet, l_daily, enc = res
    return {
        "balance": int(bal), "rod": str(rod), "bait_count": int(bait), "level": int(lvl),
        "xp": int(xp), "current_map": str(cmap), "pet": str(pet), "last_daily": str(l_daily), "enchant": str(enc)
    }

def update_user(user_id, balance=None, rod=None, bait_count=None, level=None, xp=None, current_map=None, pet=None, last_daily=None, enchant=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if balance is not None: c.execute("UPDATE users SET balance=? WHERE user_id=?", (balance, user_id))
    if rod is not None: c.execute("UPDATE users SET rod=? WHERE user_id=?", (rod, user_id))
    if bait_count is not None: c.execute("UPDATE users SET bait_count=? WHERE user_id=?", (bait_count, user_id))
    if level is not None: c.execute("UPDATE users SET level=? WHERE user_id=?", (level, user_id))
    if xp is not None: c.execute("UPDATE users SET xp=? WHERE user_id=?", (xp, user_id))
    if current_map is not None: c.execute("UPDATE users SET current_map=? WHERE user_id=?", (current_map, user_id))
    if pet is not None: c.execute("UPDATE users SET pet=? WHERE user_id=?", (pet, user_id))
    if last_daily is not None: c.execute("UPDATE users SET last_daily=? WHERE user_id=?", (last_daily, user_id))
    if enchant is not None: c.execute("UPDATE users SET enchant=? WHERE user_id=?", (enchant, user_id))
    conn.commit()
    conn.close()

def add_inventory(user_id, item_name, amount=1):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO inventory (user_id, item_name, item_count) VALUES (?, ?, ?) ON CONFLICT(user_id, item_name) DO UPDATE SET item_count=item_count+?", (user_id, item_name, amount, amount))
    conn.commit()
    conn.close()

# ======= 📖 指令一：使用教學 =======
@bot.tree.command(name="釣魚說明", description="查看歡樂釣魚場 2.0 的大師指南")
async def guide(interaction: discord.Interaction):
    embed = discord.Embed(title="🎣 歡樂釣魚場 2.0 ── 大師指南", description="`──────────────────────────`", color=0x5865F2)
    embed.add_field(name="🎮 RPG 核心指令", value="`/釣魚` : 拋竿出海挑戰\n`/背包` : 查看大倉庫與附魔狀態\n`/地圖` : 切換海域冒險", inline=True)
    embed.add_field(name="🔮 養成與經濟", value="`/附魔` : 洗鍊漁具屬性\n`/普通商店` : 採購消耗品漁具\n`/全賣` : 一鍵回收賺取金幣", inline=True)
    embed.set_footer(text="💡 提示：在官方支援伺服器拋竿可獲得 1.2 倍共振收益加成！")
    await interaction.response.send_message(embed=embed)

# ======= 全新擴充指令 =======
@bot.tree.command(name="天氣", description="觀測當前全服統一的大氣觀測站與各地圖海域共振影響")
async def current_weather_cmd(interaction: discord.Interaction):
    w_name, w_info = get_global_weather()
    embed = discord.Embed(title=f"🌤️ 全服統一氣象觀測站 ── 當前全球：【{w_name}】", description=f"*{w_info['desc']}*", color=0x3498DB)
    for m_name, m_data in MAPS.items():
        m_stat = w_info["加成"].get(m_name, {"luck": 1.0, "speed": 0.0})
        embed.add_field(name=f"🚢 【{m_name}】海域共振", value=f"運氣效率：`x{m_stat['luck']}`\n冷卻增減：`{'+' if m_stat['speed']>=0 else ''}{m_stat['speed']} 秒`", inline=True)
    await interaction.response.send_message(embed=embed)

# ======= 📅 指令二：每日簽到 =======
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
    box_count = res if res else 0
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

# ======= 🔮 2.0 全新擴充指令：遠古附魔台 =======
@bot.tree.command(name="附魔", description="消耗 500 金幣對你的魚竿進行遠古共振附魔（隨機洗鍊神級永久屬性！）")
async def enchant_rod(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    if user["balance"] < 500:
        await interaction.response.send_message("❌ 附魔需要消耗 `500` 金幣，你目前的餘額不足！", ephemeral=True)
        return
    chosen_enchant = random.choice(list(ENCHANT_POOL.keys()))
    update_user(user_id, balance=user["balance"]-500, enchant=chosen_enchant)
    embed = discord.Embed(title="🔮 遠古附魔台 ── 洗鍊共振成功！", description=f"**{interaction.user.display_name}** 的漁具已被灌注永久印記！", color=0x9B59B6)
    embed.add_field(name=f"✨ 當前附魔詞條：【{chosen_enchant}】", value=f"*{ENCHANT_POOL[chosen_enchant]['desc']}*", inline=False)
    await interaction.response.send_message(embed=embed)
# ======= 🏆 指令五：伺服器天梯排行榜 =======
@bot.tree.command(name="排行榜", description="查看當前伺服器中最強的釣魚大師（依等級與金幣排行）")
async def leaderboard(interaction: discord.Interaction):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, level, balance FROM users ORDER BY level DESC, balance DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    embed = discord.Embed(title="🏆 歡樂釣魚場 - 榮譽天梯排行榜", color=0xF1C40F)
    if not rows: embed.description = "目前排行榜上空空如也..."
    else:
        rank_str = ""
        for i, row in enumerate(rows):
            u_id, lvl, bal = row
            member = interaction.guild.get_member(u_id) if interaction.guild else None
            name = member.display_name if member else f"大師挑戰者({u_id})"
            medal = "🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else f"第 {i+1} 名"
            rank_str += f"{medal} **{name}** ── `LV.{lvl}` | `錢包: {bal} 金幣`\n"
        embed.description = rank_str
    await interaction.response.send_message(embed=embed)

# ======= 🗺️ 指令六：切換冒險地圖（🖼️ 2.0 核心擴充：對齊網址底圖秀出） =======
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
    embed = discord.Embed(title=f"🚢 揚帆啟航 ── 進駐【{map_name}】", description=f"*{MAPS[map_name]['desc']}*", color=0x1ABC9C)
    embed.set_image(url=MAPS[map_name]["image"])
    await interaction.response.send_message(embed=embed)

cooldowns = {}
# ======= 🎣 指令七：全功能核心進化釣魚 =======
@bot.tree.command(name="釣魚", description="拋出釣竿！(帶出全球天氣、精美網址海域、支援官方群特殊收益共振！)")
async def fish(interaction: discord.Interaction):
    await interaction.response.defer()
    user_id = interaction.user.id
    user = get_user(user_id)
    current_map = user["current_map"]
    current_rod = user["rod"] if user["rod"] in ROD_STATS else "新手魚竿"
    current_enchant = user["enchant"] if user["enchant"] in ENCHANT_POOL else "無"
    
    weather_name, weather_info = get_global_weather()
    weather_stat = weather_info["加成"].get(current_map, {"luck": 1.0, "speed": 0.0})
    rod_stat = ROD_STATS[current_rod]
    enc_stat = ENCHANT_POOL.get(current_enchant, {"luck_mod": 1.0, "speed_mod": 0.0, "mutate_mod": 0.0})
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT item_name, item_count FROM inventory WHERE user_id=? AND item_name IN ('💗性慾藥水', '🌌轉生神仙水(運氣+1000000%)', '🟢普通運氣藥水', '🔵高級運氣藥水', '⚡閃電速度藥水', '高級魚餌')", (user_id,))
    inv_data = dict(c.fetchall())
    
    has_potion = inv_data.get('💗性慾藥水', 0) > 0
    has_god_water = inv_data.get('🌌轉生神仙水(運氣+1000000%)', 0) > 0
    has_normal_pot = inv_data.get('🟢普通運氣藥水', 0) > 0
    has_high_pot = inv_data.get('🔵高級運氣藥水', 0) > 0
    has_speed_pot = inv_data.get('⚡閃電速度藥水', 0) > 0
    has_high_bait = inv_data.get('高級魚餌', 0) > 0
    
    current_time = time.time()
    base_cooldown = 10.0 - rod_stat["speed_bonus"] - weather_stat["speed"] - enc_stat["speed_mod"]
    if has_potion: base_cooldown = 3.0
    if has_speed_pot: base_cooldown -= 4.0
    if base_cooldown < 1.0: base_cooldown = 1.0
    
    if user_id in cooldowns and current_time - cooldowns[user_id] < base_cooldown:
        remaining = round(base_cooldown - (current_time - cooldowns[user_id]), 1)
        await interaction.followup.send(f"🚨 拋竿速度太快了！手拉得好酸...再等 {remaining} 秒。(當前冷卻: {round(base_cooldown, 1)}秒)", ephemeral=True)
        conn.close()
        return
    cooldowns[user_id] = current_time
    # 🤝 2.0 全新擴充：檢測是否在官方支援伺服器拋竿，提供 1.2 倍收益加成
    is_supported = interaction.guild_id == SUPPORT_GUILD_ID if interaction.guild_id else False
    guild_bonus = 1.2 if is_supported else 1.0
    
    luck_multiplier = rod_stat["luck"] * weather_stat["luck"] * enc_stat["luck_mod"] * guild_bonus
    bait_msg = f"🌍 **全服全球天氣：【{weather_name}】** (*{weather_info['desc']}*)\n"
    if is_supported: bait_msg = "🤝 **【官方群共振】檢測到你在支援伺服器拋竿，全收益乘 1.2 倍！**\n" + bait_msg
    if current_enchant != "無": bait_msg += f"🔮 漁具灌注附魔：**【{current_enchant}】** 加持中\n"
    
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
        if has_speed_pot:
            c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='⚡閃電速度藥水'", (user_id,))
            bait_msg += "⚡ **[神速拋竿]** 喝下閃電速度藥水 (冷卻時間激減 4 秒)！\n"
        if has_high_bait:
            luck_score += 35.0
            c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='高級魚餌'", (user_id,))
            bait_msg += "✨ 你使用了 **高級魚餌**！\n"
        elif user["bait_count"] > 0:
            luck_score += 15.0
            update_user(user_id, bait_count=user["bait_count"]-1)
            bait_msg += "🐛 你消耗了 1 個 **普通魚餌**！\n"
        else: bait_msg += "🪝 無魚餌素釣，全憑直覺！\n"

    if has_potion:
        c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='💗性慾藥水'", (user_id,))
        bait_msg = "🔥 **[速度狂暴]** 速度大增！\n" + bait_msg
    conn.commit()
    conn.close()

    # 🌟 100% 純數字落點判定，徹底踢走 w
    roll = random.uniform(0, 100)
    if luck_score >= 500000: chosen_rarity = "作者級" if roll < 40 else "秘密" if roll < 80 else "神話"
    elif luck_score >= 150: chosen_rarity = "作者級" if roll < 1 else "秘密" if roll < 5 else "神話" if roll < 20 else "傳奇" if roll < 60 else "稀有"
    elif luck_score >= 50: chosen_rarity = "神話" if roll < 2 else "傳奇" if roll < 15 else "稀有" if roll < 50 else "普通"
    else: chosen_rarity = "傳奇" if roll < 1 else "稀有" if roll < 20 else "普通"

    available_fish = []
    if current_map in MAP_EXCLUSIVE_FISH and chosen_rarity in MAP_EXCLUSIVE_FISH[current_map]:
        available_fish = MAP_EXCLUSIVE_FISH[current_map][chosen_rarity]
    if not available_fish: available_fish = FISH_POOL.get(chosen_rarity, FISH_POOL["普通"])
    if not available_fish: available_fish = [("🐟 吳郭魚", 15)]
        
    fish_item = random.choice(available_fish)
    fish_name, _ = fish_item
    
    # 🌟 2.0 全新擴充：多彩史詩變異首綴系統
    final_mutation_chance = rod_stat["mutation"] + enc_stat["mutate_mod"]
    if random.random() < final_mutation_chance:
        m_prefix = random.choice(["[🟢毒性突變]", "[🔵晶螢閃耀]", "[👑極致黃金]", "[🔴血色異變]", "[🌌星空突變]"])
        fish_name = f"{m_prefix} {fish_name}"
        
    add_inventory(user_id, fish_name, 1)

    xp_gained = int(random.randint(15, 30) * guild_bonus)
    pet_msg = f"（🤝 官方伺服器加乘 +{int(xp_gained*0.2)}xp！）" if is_supported else ""
    if "尋寶獵鷹" in user["pet"]:
        xp_gained += int(xp_gained * 0.3)
        pet_msg = "（🦅 獵鷹叼回 +30%xp！）"
    elif "迷你小青龍" in user["pet"]:
        xp_gained += int(xp_gained * 0.5)
        pet_msg = "（🐉 小青龍賜予 +50%xp！）"

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
    embed = discord.Embed(title=f"🎣 拋竿結果 ── 【{icons[chosen_rarity]} {chosen_rarity}】", description=f"{bait_msg}\n🧬 捕捉到生物：**{fish_name}**！\n🏆 獲得經驗：`+{xp_gained}xp` {pet_msg}\n🧬 當前進度：`🧬 {new_xp}/{xp_needed} XP`{lvl_up_msg}", color=0x34495E)
    embed.set_thumbnail(url=MAPS[current_map]["image"])
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="普通商店", description="顯示豐收漁具普通商店的道具與藥水")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🏪 豐收漁具普通商店", description="`──────────────────────────`", color=0x2ECC71)
    embed.add_field(name="🎣 升級魚竿 (具備隱藏加成)", value="\n".join([f"• {k}: `{v} 🪙`" for k, v in RODS_SHOP.items()]), inline=True)
    embed.add_field(name="🐛 消耗品與神奇藥水", value="\n".join([f"• {k}: `{v} 🪙`" for k, v in BAITS_SHOP.items()]), inline=True)
    await interaction.response.send_message(embed=embed)

@app_commands.describe(item_name="物品名稱", quantity="數量")
@bot.tree.command(name="購買", description="向商店採購商品道具")
async def buy(interaction: discord.Interaction, item_name: str, quantity: int = 1):
    if quantity <= 0: return
    user_id = interaction.user.id
    user = get_user(user_id)
    price, is_rod, is_bait = None, False, False
    if item_name in RODS_SHOP: price, is_rod = RODS_SHOP[item_name], True
    elif item_name in BAITS_SHOP: price, is_bait = BAITS_SHOP[item_name], True
    if not price: return
    total_cost = price * quantity
    if user["balance"] < total_cost:
        await interaction.response.send_message("❌ 餘額不足！", ephemeral=True)
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
    embed.add_field(name="📊 個人屬性", value=f"• 等級：`LV.{user['level']}` ({user['xp']}/{xp_needed})\n• 錢包：`{user['balance']} 🪙`\n• 冒險海域：【`{user['current_map']}`】", inline=True)
    embed.add_field(name="🎣 裝備與守護", value=f"• 魚竿：`{user['rod']}`\n• 附魔：`【{user['enchant']}】`\n• 神獸：`{user['pet']}`\n• 儲備普通餌：`{user['bait_count']} 個`", inline=True)
    inv_str = "\n".join([f"• {name} x{count}" for name, count in items]) if items else "空空如也"
    embed.add_field(name="🐟 儲存大倉庫", value=inv_str, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="全賣", description="將背包裡所有的常規魚獲全部售出（高階變異享有高額金幣加成！）")
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
    for item_name, count in items:
        base_name = item_name
        for p in ["[🟢毒性突變] ", "[🔵晶螢閃耀] ", "[👑極致黃金] ", "[🔴血色異變] ", "[🌌星空突變] "]:
            base_name = base_name.replace(p, "")
        if base_name in prices_map:
            revenue = prices_map[base_name] * count
            # 🌟 2.0 核心擴充：多彩突變首綴高額倍率結算
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
        await interaction.followup.send("❌ 無常規可售物。", ephemeral=True)
        return
    conn.commit()
    conn.close()
    if "招財貓" in user["pet"]:
        bonus_cash = int(total_revenue * 0.1)
        total_revenue += bonus_cash
        sold_details.append(f"🐱 【招財貓加持】 額外抓回了 {bonus_cash} 金幣！")
    update_user(user_id, balance=user["balance"] + total_revenue)
    # 🌟 完美歸位縮排：徹底收進函數內部，防堵 Deploy 閃退！
    # 🌟 完美歸位縮排：最前面「必須有 4 個空格」，讓它完全收進函數內部！
    embed = discord.Embed(title="💰 魚獲交易結算完畢", description="\n".join(sold_details) + f"\n\n💵 總計賺得：{total_revenue} 金幣！", color=0xF1C40F)
    await interaction.followup.send(embed=embed)

# ─── 🛑 警告：以下這四行是全專案的最底層啟動區，最左邊「絕對不能有任何空格」！ ───
init_db()
keep_alive()
DISCORD_CODE = os.getenv("DISCORD_TOKEN")
bot.run(DISCORD_CODE)
