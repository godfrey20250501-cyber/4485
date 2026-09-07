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

    # 🛡️ 安全機制：防指令上限大爆炸
    async def setup_hook(self):
        try:
            await self.tree.sync()
            print("連線成功：斜線指令已完全同步至 Discord 官方後台！")
        except Exception as e:
            print(f"指令同步提示: {e}")

bot = MyBot()
DB_FILE = "fishing_game.db"

# 2. 修正版 RPG 資料庫
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

# 3. 豪華版道具、地圖與魚池特產定義
RODS_SHOP = {"初級魚竿": 200, "高級魚竿": 1000, "深海魚竿": 3500, "量子魚竿": 8000}
BAITS_SHOP = {
    "普通魚餌": 15, "高級魚餌": 60, "🧰_神祕黃金寶箱": 500,
    "🟢_普通運氣藥水": 100, "🔵_高級運氣藥水": 400, "💗_性慾藥水(速度300%)": 150, "🌌_轉生神仙水(運氣+1000000%)": 99999
}

MAPS = {
    "小池塘": {"req_lvl": 0, "desc": "新手起步的溫馨小池塘"},
    "陽光沙灘": {"req_lvl": 5, "desc": "風光明媚，可以釣到海魚（需等級 5）"},
    "神祕深海": {"req_lvl": 15, "desc": "極度危險，藏有遠古神話生物（需等級 15）"}
}
FISH_POOL = {
    "普通": [("🐟 吳郭魚", 15), ("🐠 小丑魚", 20), ("🐡 氣噗噗河豚", 25), ("👟 舊鞋子", 2)],
    "稀有": [("🦑 大王烏賊", 60), ("🦈 藍色鯊魚", 120), ("🦀 帝王蟹", 150), ("🐡 黃金河豚", 200)],
    "傳奇": [("🐳 藍鯨", 500), ("👑 黃金鯉魚", 800), ("🔱 海神三叉戟", 1200)],
    "神話": [("🐉 東方青龍", 5000), ("🌊 亞特蘭提斯之心", 8000), ("🧜‍♀️ 美人魚的眼淚", 7500)],
    "秘密": [("🛸 外星科技零件", 25000)],
    "作者級": [("💻 作者的未編譯源代碼", 100000)]
}
# 4. 資料庫核心工具（🌟已修正 Tuple 賦值錯誤，徹底解決簽到閃退）
def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT balance, rod, bait_count, level, xp, current_map, pet FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    if not res:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        res = (100, '新手魚竿', 5, 0, 0, '小池塘', '無')
    conn.close()
    return {
        "balance": res[0], "rod": res[1], "bait_count": res[2],
        "level": res[3], "xp": res[4], "current_map": res[5], "pet": res[6]
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

@bot.event
async def on_ready():
    init_db()
    print(f"🎣 豪華RPG釣魚機器人已成功上線：{bot.user.name}")

# ======= 📖 指令一：使用教學 =======
@bot.tree.command(name="釣魚說明", description="查看歡樂釣魚場的玩家指南與基本指令")
async def guide(interaction: discord.Interaction):
    embed = discord.Embed(title="🎣 歡樂釣魚場 - 玩家指南", color=0x5865F2)
    embed.add_field(name="🎮 核心功能指令", value="`/釣魚` : 隨機出海釣魚\n`/背包` : 查看個人的RPG屬性面板與當前魚獲", inline=False)
    embed.add_field(name="🏪 商店與經濟系統", value="`/普通商店` : 採購道具、全套藥水與黃金保箱\n`/購買 <物品名稱> [數量]` : 購買特定商品\n`/全賣` : 將背包裡所有的魚獲全部售出換取金幣", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="查看歡樂釣魚場的玩家指南與基本指令（英文版快捷鍵）")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="🎣 歡樂釣魚場 - 玩家指南", color=0x5865F2)
    embed.add_field(name="🎮 核心功能指令", value="`/釣魚` : 隨機出海釣魚\n`/背包` : 查看個人的RPG屬性面板與當前魚獲", inline=False)
    embed.add_field(name="🏪 商店與經濟系統", value="`/普通商店` : 採購道具、全套藥水與黃金保箱\n`/購買 <物品名稱> [數量]` : 購買特定商品\n`/全賣` : 將背包裡所有的魚獲全部售出換取金幣", inline=False)
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
    user_id = interaction.user.id
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT item_count FROM inventory WHERE user_id=? AND item_name='🧰_神祕黃金寶箱'", (user_id,))
    res = c.fetchone()
    box_count = res[0] if res else 0
    if box_count <= 0:
        await interaction.response.send_message("❌ 你的背包裡沒有寶箱！請先去商店使用 `/購買 🧰_神祕黃金寶箱 1` 採購一個吧！", ephemeral=True)
        conn.close()
        return
    c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🧰_神祕黃金寶箱'", (user_id,))
    conn.commit()
    conn.close()
    roll = random.random()
    user = get_user(user_id)
    if roll < 0.05:
        colors_pool = ["🐱 招財貓(金幣+10%)", "🦅 尋寶獵鷹(XP+30%)", "🐉 迷你小青龍(XP+50%)"]
        chosen_pet = random.choice(colors_pool)
        update_user(user_id, pet=chosen_pet)
        await interaction.response.send_message(f"🌌 ✨ **【神光降臨！！】** **{interaction.user.display_name}** 打開黃金寶箱，居然奇蹟般孵化出極稀有寵物：**{chosen_pet}**！！")
    elif roll < 0.25:
        add_inventory(user_id, "🔵_高級運氣藥水", 1)
        await interaction.response.send_message(f"🧰 **{interaction.user.display_name}** 打開了黃金寶箱，獲得了：`🔵_高級運氣藥水` x1！")
    elif roll < 0.55:
        add_inventory(user_id, "🟢_普通運氣藥水", 1)
        await interaction.response.send_message(f"🧰 **{interaction.user.display_name}** 打開了黃金寶箱，獲得了：`🟢_普通運氣藥水` x1！")
    else:
        bonus_money = random.randint(150, 400)
        update_user(user_id, balance=user["balance"]+bonus_money, bait_count=user["bait_count"]+5)
        await interaction.response.send_message(f"🧰 **{interaction.user.display_name}** 打開了黃金寶箱，獲得了：`🪙 {bonus_money} 金幣` 補給與 `🐛 高級魚餌` x5！")

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
# ======= 🎣 指令七：全功能進化版核心釣魚 =======
@bot.tree.command(name="釣魚", description="拋出釣竿！(魚餌非必要，喝了運氣藥水可以瘋狂增加爆率！)")
async def fish(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 🛡️ 潛在問題優化：加上安全元組解包，防範 None 類型噴錯
    c.execute("SELECT item_count FROM inventory WHERE user_id=? AND item_name='💗_性慾藥水(速度300%)'", (user_id,))
    res_p = c.fetchone()
    has_potion = res_p and res_p[0] > 0
    
    c.execute("SELECT item_count FROM inventory WHERE user_id=? AND item_name='🌌_轉生神仙水(運氣+1000000%)'", (user_id,))
    res_g = c.fetchone()
    has_god_water = res_g and res_g[0] > 0
    
    c.execute("SELECT item_count FROM inventory WHERE user_id=? AND item_name='🟢_普通運氣藥水'", (user_id,))
    res_n_pot = c.fetchone()
    has_normal_pot = res_n_pot and res_n_pot[0] > 0
    c.execute("SELECT item_count FROM inventory WHERE user_id=? AND item_name='🔵_高級運氣藥水'", (user_id,))
    res_h_pot = c.fetchone()
    has_high_pot = res_h_pot and res_h_pot[0] > 0
    
    c.execute("SELECT item_count FROM inventory WHERE user_id=? AND item_name='高級魚餌'", (user_id,))
    res_hb = c.fetchone()
    has_high_bait = res_hb and res_hb[0] > 0
    
    current_time = time.time()
    base_cooldown = 3.0 if has_potion else 10.0
    if user_id in cooldowns:
        time_passed = current_time - cooldowns[user_id]
        if time_passed < base_cooldown:
            remaining = round(base_cooldown - time_passed, 1)
            await interaction.response.send_message(f"🚨 拋竿速度太快了！手拉得好酸...再等 {remaining} 秒。", ephemeral=True)
            conn.close()
            return
    cooldowns[user_id] = current_time
    
    w = [80.0, 19.0, 0.9, 0.08, 0.019, 0.001]
    bait_msg = "🪝 你這次採用**無魚餌素釣**，全憑直覺！\n"
    if has_god_water:
        w = [0.0, 1.0, 9.0, 30.0, 40.0, 20.0]
        c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🌌_轉生神仙水(運氣+1000000%)'", (user_id,))
        bait_msg = "🌌 **[神仙降臨]** 你喝下了百萬倍運氣神仙水！百寶爆率全開！！\n"
    elif has_high_pot:
        w = [25.0, 50.0, 18.0, 6.0, 0.9, 0.1]
        c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🔵_高級運氣藥水'", (user_id,))
        bait_msg = "🔵 **[運氣沖天]** 喝下高級運氣藥水，感知能力大幅大增 **(+200%運氣)**！\n"
    elif has_normal_pot:
        w = [50.0, 38.0, 9.0, 2.5, 0.4, 0.1]
        c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='🟢_普通運氣藥水'", (user_id,))
        bait_msg = "🟢 **[靈氣附體]** 喝下普通運氣藥水，雙眼發光 **(+50%運氣)**！\n"
    elif has_high_bait:
        w = [40.0, 45.0, 10.0, 4.0, 0.9, 0.1]
        c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='高級魚餌'", (user_id,))
        bait_msg = "✨ 你使用了 **高級魚餌**，運氣暴增 **+550%**！！\n"
    elif user["bait_count"] > 0:
        w = [65.0, 28.0, 5.0, 1.5, 0.4, 0.1]
        update_user(user_id, bait_count=user["bait_count"]-1)
        bait_msg = "🐛 你消耗了 1 個 **普通魚餌**，運氣提升 **+100%**！\n"
        
    if has_potion:
        c.execute("UPDATE inventory SET item_count=item_count-1 WHERE user_id=? AND item_name='💗_性慾藥水(速度300%)'", (user_id,))
        bait_msg = "🔥 **[速度狂暴]** 喝下速度藥水，拋竿快如閃電！\n" + bait_msg
        
    conn.commit()
    conn.close()

    rarities = ["普通", "稀有", "傳奇", "神話", "秘密", "作者級"]
    # 🌟 潛在問題修正：random.choices 會傳回 list，後面加上 [0] 取出真實字串，否則字典取值會崩潰
    chosen_rarity = random.choices(rarities, weights=w, k=1)[0]
    fish_item = random.choice(FISH_POOL[chosen_rarity])
    fish_name, _ = fish_item
    if user["current_map"] == "小池塘" and chosen_rarity in ["神話", "秘密", "作者級"]:
        fish_name, _ = ("🐟 肥美的池塘大鯉魚", 40)
        chosen_rarity = "稀有"
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
    elif "招財貓" in user["pet"]:
        pet_msg = "（🐱 招財貓默默幫你累積財運...）"

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
    msg = f"{bait_msg}🎣 **{interaction.user.display_name}** 在【{user['current_map']}】拋竿...\n【{icons[chosen_rarity]} {chosen_rarity}】釣到了 **{fish_name}**！(獲得 +{xp_gained}xp {pet_msg} 🧬 {new_xp}/{xp_needed}){lvl_up_msg}"
    if chosen_rarity in ["神話", "秘密", "作者級"] and lvl_up_msg == "":
        msg += "\n🎉 **【世界廣播】全服見證！極致歐皇在海域中撈起了不世珍寶！！** 🎉"
    await interaction.response.send_message(msg)

# ======= 🏪 指令八：全功能商店與購買系統 =======
@bot.tree.command(name="普通商店", description="顯示豐收漁具普通商店的道具、全套藥水與神祕保箱")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🏪 豐收漁具普通商店", description="使用 `/購買` 來購買道具、全套運氣藥水與黃金保箱", color=0x2ECC71)
    embed.add_field(name="🎣 升級魚竿 (直接替換等級)", value="\n".join([f"• {k}: {v} 金幣" for k, v in RODS_SHOP.items()]), inline=False)
    embed.add_field(name="🐛 消耗品、保箱與多款增益藥水", value="\n".join([f"• {k}: {v} 金幣 / 個" for k, v in BAITS_SHOP.items()]), inline=False)
    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="購買", description="向商店採購商品道具、高級魚餌、運氣藥水或黃金寶箱")
@app_commands.describe(item_name="請輸入你想購買的物品完整名稱", quantity="你想購買的數量")
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
        await interaction.response.send_message("❌ 找不到該商品，請確認名稱輸入完全正確。", ephemeral=True)
        return
    total_cost = price * quantity
    if user["balance"] < total_cost:
        await interaction.response.send_message(f"❌ 餘額不足！你需要 {total_cost} 金幣，但目前只有 {user['balance']} 金幣。", ephemeral=True)
        return
    new_balance = user["balance"] - total_cost
    if is_rod:
        update_user(user_id, balance=new_balance, rod=item_name)
        await interaction.response.send_message(f"🛍️ 購買成功！你花費 {total_cost} 金幣裝備了 **{item_name}**！")
    elif is_bait:
        update_user(user_id, balance=new_balance)
        add_inventory(user_id, item_name, quantity)
        await interaction.response.send_message(f"🛍️ 購買成功！你將 {quantity} 個 **{item_name}** 收納進背包囉！")

# ======= 🎒 指令九：個人狀態與背包展示 =======
@bot.tree.command(name="背包", description="查看個人的等級、當前神獸寵物、錢包餘額與魚獲")
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

@bot.tree.command(name="全賣", description="將背包裡所有的常規魚獲全部售出換取金幣")
async def sell_all(interaction: discord.Interaction):
    user_id = interaction.user.id
    user = get_user(user_id)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT item_name, item_count FROM inventory WHERE user_id=? AND item_count > 0", (user_id,))
    items = c.fetchall()
    if not items:
        await interaction.response.send_message("📭 你的背包裡沒有任何常規魚獲可以販賣。", ephemeral=True)
        conn.close()
        return
    prices_map = {}
    for r, v_list in FISH_POOL.items():
        for fname, fprice in v_list: prices_map[fname] = fprice
    total_revenue = 0
    sold_details = []
    for item_name, count in items:
        if item_name in prices_map:
            revenue = prices_map[item_name] * count
            total_revenue += revenue
            sold_details.append(f"• {item_name} x{count} -> 獲得 {revenue} 金幣")
            c.execute("UPDATE inventory SET item_count=0 WHERE user_id=? AND item_name=?", (user_id, item_name))
    conn.commit()
    conn.close()
    if total_revenue == 0:
        await interaction.response.send_message("❌ 背包內沒有可常規販賣的魚獲（保箱、藥水不予回收）。", ephemeral=True)
        return
    if "招財貓" in user["pet"]:
        bonus_cash = int(total_revenue * 0.1)
        total_revenue += bonus_cash
        sold_details.append(f"🐱 **【招財貓加持】** 貓爪幫你多抓回了 `{bonus_cash}` 金幣！")
    update_user(user_id, balance=user["balance"] + total_revenue)
    embed = discord.Embed(title="💰 魚獲交易結算完畢", color=0xF1C40F)
    embed.description = "\n".join(sold_details) + f"\n\n💵 總計賺得：**{total_revenue}** 金幣！"
    await interaction.response.send_message(embed=embed)

# 🚀 啟動區
keep_alive()
DISCORD_CODE = os.getenv("DISCORD_TOKEN")
bot.run(DISCORD_CODE)
