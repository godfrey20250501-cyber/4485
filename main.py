import discord
from discord.ext import commands
import random
import sqlite3

# 1. 基礎設定與意圖 (Intents)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DB_FILE = "fishing_game.db"

# 2. 初始化資料庫：建立玩家資產表與背包表
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 100, rod TEXT DEFAULT '新手魚竿', bait_count INTEGER DEFAULT 5
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER, item_name TEXT, item_count INTEGER DEFAULT 0, PRIMARY KEY(user_id, item_name)
    )''')
    conn.commit()
    conn.close()

# 3. 定義普通商店、活動商店與獎勵池（物品名稱、售價/回收價）
RODS_SHOP = {"初級魚竿": 200, "高級魚竿": 1000, "量子魚竿": 5000}
BAITS_SHOP = {"普通魚餌": 10, "幸運魚餌": 50}
EVENT_SHOP = {"【活動限定】深海夜光珠": 1500, "【活動限定】遠古亞特蘭提斯密鑰": 8000}

FISH_POOL = {
    "普通": [("🐟 吳郭魚", 15), ("🐠 小丑魚", 20), ("鞋子", 2)],
    "稀有": [("🦑 大王烏賊", 60), ("🦈 鯊魚", 120), ("🦀 帝王蟹", 150)],
    "傳奇": [("🐳 藍鯨", 500), ("👑 黃金鯉魚", 800), ("🔱 海神三叉戟", 1200)],
    "神話": [("🐉 東方青龍", 5000), ("🌊 亞特蘭提斯之心", 8000)],
    "秘密": [("🛸 外星科技零件", 25000)],
    "作者級": [("💻 作者的未編譯源代碼", 100000)]
}

# 資料庫輔助函式
def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT balance, rod, bait_count FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    if not res:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        res = (100, '新手魚竿', 5)
    conn.close()
    return {"balance": res[0], "rod": res[1], "bait_count": res[2]}

def update_user(user_id, balance=None, rod=None, bait_count=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if balance is not None: c.execute("UPDATE users SET balance=? WHERE user_id=?", (balance, user_id))
    if rod is not None: c.execute("UPDATE users SET rod=? WHERE user_id=?", (rod, user_id))
    if bait_count is not None: c.execute("UPDATE users SET bait_count=? WHERE user_id=?", (bait_count, user_id))
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
    print(f"🎣 釣魚機器人已成功上線：{bot.user.name}")

# ======= 📖 指令四：使用教學 =======
@bot.command(name="釣魚說明")
async def guide(ctx):
    embed = discord.Embed(title="🎣 歡樂釣魚場 - 玩家指南", color=0x5865F2)
    embed.add_field(name="🎮 核心功能指令", value="`!釣魚` : 消耗 1 個魚餌出海釣魚\n`!背包` : 查看錢包餘額、當前魚竿與擁有的魚獲", inline=False)
    embed.add_field(name="🏪 商店與經濟系統", value="`!普通商店` : 採購進階魚竿與普通魚餌\n`!活動商店` : 搶購賽季限定稀有高價收藏品\n`!購買 <物品名稱> [數量]` : 購買特定商品\n`!全賣` : 將背包裡所有的魚獲全部售出換取金幣", inline=False)
    await ctx.send(embed=embed)

# ======= 🎣 核心功能：隨機加權釣魚 =======
@bot.command(name="釣魚")
async def fish(ctx):
    user_id = ctx.author.id
    user = get_user(user_id)
    if user["bait_count"] <= 0:
        await ctx.send("❌ 你沒有魚餌了！請前往商店使用 `!購買 普通魚餌 10` 進行補給。")
        return
        
    update_user(user_id, bait_count=user["bait_count"]-1)
    
    rarities = ["普通", "稀有", "傳奇", "神話", "秘密", "作者級"]
    weights = [80.0, 19.0, 0.9, 0.08, 0.019, 0.001] # 完美符合 100% 分佈
    chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]
    fish_item = random.choice(FISH_POOL[chosen_rarity])
    fish_name, _ = fish_item
    
    add_inventory(user_id, fish_name, 1)
    
    icons = {"普通":"⚪", "稀有":"🔵", "傳奇":"🟡", "神話":"🔴", "秘密":"🟣", "作者級":"🌌"}
    msg = f"🎣 **{ctx.author.display_name}** 拋出釣竿... 消耗 1 個魚餌。\n【{icons[chosen_rarity]} {chosen_rarity}】你釣到了 **{fish_name}**！已存入背包。"
    if chosen_rarity in ["神話", "秘密", "作者級"]:
        msg += "\n🎉 **【全服世界廣播】見證奇蹟！稀世珍寶被釣起來啦！！** 🎉"
    await ctx.send(msg)

# ======= 🏪 指令二：商店系統 (普通與活動) =======
@bot.command(name="普通商店")
async def shop(ctx):
    embed = discord.Embed(title="🏪 豐收漁具普通商店", description="使用 `!購買 <商品名稱> [數量]` 來購買道具", color=0x2ECC71)
    embed.add_field(name="🎣 升級魚竿 (直接替換等級)", value="\n".join([f"• {k}: {v} 金幣" for k, v in RODS_SHOP.items()]), inline=False)
    embed.add_field(name="🐛 消耗性魚餌", value="\n".join([f"• {k}: {v} 金幣 / 個" for k, v in BAITS_SHOP.items()]), inline=False)
    await ctx.send(embed=embed)

@bot.command(name="活動商店")
async def event_shop(ctx):
    embed = discord.Embed(title="✨ 限時神祕活動黑市", description="使用 `!購買 <商品名稱> 1` 收集限定稀有收藏品", color=0xE91E63)
    embed.add_field(name="💎 賽季限定珍寶", value="\n".join([f"• {k}: {v} 金幣" for k, v in EVENT_SHOP.items()]), inline=False)
    await ctx.send(embed=embed)

@bot.command(name="購買")
async def buy(ctx, item_name: str, quantity: int = 1):
    if quantity <= 0: return
    user_id = ctx.author.id
    user = get_user(user_id)
    price, is_rod, is_bait, is_event = None, False, False, False
    
    if item_name in RODS_SHOP: price, is_rod = RODS_SHOP[item_name], True
    elif item_name in BAITS_SHOP: price, is_bait = BAITS_SHOP[item_name], True
    elif item_name in EVENT_SHOP: price, is_event = EVENT_SHOP[item_name], True
    
    if not price:
        await ctx.send("❌ 找不到該商品，請確認名稱輸入完全正確（例：`!購買 普通魚餌 5`）。")
        return
    
    total_cost = price * quantity
    if user["balance"] < total_cost:
        await ctx.send(f"❌ 餘額不足！你需要 {total_cost} 金幣，但目前只有 {user['balance']} 金幣。")
        return
        
    new_balance = user["balance"] - total_cost
    if is_rod:
        update_user(user_id, balance=new_balance, rod=item_name)
        await ctx.send(f"🛍️ 購買成功！你花費 {total_cost} 金幣裝備了 **{item_name}**！")
    elif is_bait:
        update_user(user_id, balance=new_balance, bait_count=user["bait_count"]+quantity)
        await ctx.send(f"🛍️ 購買成功！你花費 {total_cost} 金幣購買了 {quantity} 個 **{item_name}**。")
    elif is_event:
        update_user(user_id, balance=new_balance)
        add_inventory(user_id, item_name, quantity)
        await ctx.send(f"🛍️ 購買成功！你收購了活動限定 **{item_name}** x{quantity}！")

# ======= 🎒 指令三：物品欄與售賣功能 =======
@bot.command(name="背包")
async def inventory(ctx):
    user_id = ctx.author.id
    user = get_user(user_id)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT item_name, item_count FROM inventory WHERE user_id=? AND item_count > 0", (user_id,))
    items = c.fetchall()
    conn.close()
    
    embed = discord.Embed(title=f"🎒 {ctx.author.display_name} 的個人背包", color=0x3498DB)
    embed.add_field(name="💰 錢包帳戶", value=f"{user['balance']} 金幣", inline=True)
    embed.add_field(name="🎣 當前魚竿", value=user["rod"], inline=True)
    embed.add_field(name="🐛 剩餘魚餌", value=f"{user['bait_count']} 個", inline=True)
    
    inv_str = "\n".join([f"• {name} x{count}" for name, count in items]) if items else "空空如也"
    embed.add_field(name="🐟 儲存倉庫 (可使用 `!全賣` 變現)", value=inv_str, inline=False)
    await ctx.send(embed=embed)

@bot.command(name="全賣")
async def sell_all(ctx):
    user_id = ctx.author.id
    user = get_user(user_id)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT item_name, item_count FROM inventory WHERE user_id=? AND item_count > 0", (user_id,))
    items = c.fetchall()
    
    if not items:
        await ctx.send("📭 你的背包裡沒有任何常規魚獲可以販賣。")
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
        await ctx.send("❌ 背包內沒有可常規販賣的魚獲（活動商品不予回收）。")
        return
        
    update_user(user_id, balance=user["balance"] + total_revenue)
    
    embed = discord.Embed(title="💰 魚獲交易結算完畢", color=0xF1C40F)
    embed.description = "\n".join(sold_details) + f"\n\n💵 總計賺得：**{total_revenue}** 金幣！"
    await ctx.send(embed=embed)

bot.run("你的_DISCORD_BOT_TOKEN")
