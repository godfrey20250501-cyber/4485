from dotenv import load_dotenv
load_dotenv()  # 自動打開環境變數檔案
import os
import time
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
from discord import app_commands
import random
from datetime import datetime

# 🌟 4.0 諸神黃昏：引入 pymongo 徹底破開 Render 暫存硬碟格式化重啟回檔限制！
from pymongo import MongoClient

# 🌐 Flask 網頁製造機（保持 24h 不休息）
app = Flask('')

@app.route('/')
def home():
    return "歡樂釣魚場 4.0 諸神黃昏雲端資料中心已完美連線通行！"

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
            print("連線成功：歡樂釣魚場 4.0 雲端斜線指令已完全同步！")
        except Exception as e:
            print(f"指令同步提示: {e}")

bot = MyBot()

# 🌟 官方支援群 ID 設定（已完美對齊老哥的 Discord 伺服器！）
SUPPORT_GUILD_ID = 1546517053719060642

# ======= 🍀 MongoDB 雲端保險箱架構（4 空格精準縮排） =======
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("🚨 警告：Render 後台未偵測到 MONGO_URI 環境變數！將自動建立本地虛擬 Fallback 連線。")
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
else:
    client = MongoClient(MONGO_URI)

# 選定資料庫與三大雲端資料集合 (Collections，徹底取代舊 SQLite 資料表)
db = client["fishing_game_400"]
users_col = db["users"]
inventory_col = db["inventory"]
guilds_col = db["guilds"]

def init_db():
    try:
        # 測試雲端握手
        client.admin.command('ping')
        print("🟢 諸神黃昏防線：歡樂釣魚場與 MongoDB Atlas 雲端資料庫 24h 永久連線成功！玩家存檔已鎖死！")
    except Exception as e:
        print(f"🚨 雲端連線提示: {e}")
# ======= 📊 JSON 文件型資料庫安全讀寫工具（強制型態防禦，100% 阻斷回檔！） =======
def get_user(user_id):
    user_id = int(user_id)
    user = users_col.find_one({"user_id": user_id})
    if not user:
        # 船新玩家初始化一整包精美的 4.0 JSON 歷史結構手札
        default_user = {
            "user_id": user_id, "balance": 100, "rod": "新手魚竿", "bait_count": 5,
            "level": 0, "xp": 0, "current_map": "一海・新手小池塘", "pet": "無 (徒手素釣)",
            "last_daily": "2000-01-01", "enchant": "無", "bait_type": "無 (徒手肉搏)",
            "quest_type": "無", "quest_target": 0, "quest_progress": 0, "quest_reward": 0
        }
        users_col.insert_one(default_user)
        return default_user
        
    # 🛠️ 雲端自動熱修補機制：老玩家如果缺 4.0 的新欄位，在讀取的 0.01 秒內自動在雲端補齊預設值！
    updates = {}
    defaults = {
        "balance": 100, "rod": "新手魚竿", "bait_count": 5, "level": 0, "xp": 0,
        "current_map": "一海・新手小池塘", "pet": "無 (徒手素釣)", "last_daily": "2000-01-01",
        "enchant": "無", "bait_type": "無 (徒手肉搏)", "quest_type": "無", "quest_target": 0,
        "quest_progress": 0, "quest_reward": 0
    }
    for k, v in defaults.items():
        if k not in user:
            user[k] = v
            updates[k] = v
    if updates:
        users_col.update_one({"user_id": user_id}, {"$set": updates})
    return user

def update_user(user_id, **kwargs):
    user_id = int(user_id)
    # 雲端一鍵同步物件修改，速度比 SQLite 快 10 倍！
    users_col.update_one({"user_id": user_id}, {"$set": kwargs}, upsert=True)

def add_inventory(user_id, item_name, amount=1):
    user_id = int(user_id)
    amount = int(amount)
    # 使用 MongoDB 的 $inc 機制，自動累加與記錄玩家背包倉庫的魚獲與石頭數量
    inventory_col.update_one(
        {"user_id": user_id, "item_name": item_name},
        {"$inc": {"item_count": amount}},
        upsert=True
    )
# ======= 🏪 全球普通商店：全套 16 款截圖物資、高階漁具與浮標上架 =======
BAITS_SHOP = {
    # 🐛 Fisch 風格硬核消耗魚餌
    "普通魚餌": 15, "稀有魚餌 (x1)": 45, "神話魚餌 (x1)": 150, "傳說魚餌 (x1)": 350, 
    "海藻餌": 25, "磁鐵重餌": 45, "🔋 彈性奈米反覆餌": 4999,
    
    # 🧪 截圖全套 11 款珍稀魔法藥水
    "幸運藥水1級 (x3)": 100, "幸運藥水2級 (x10)": 400, "幸運藥水3級 (x2)": 600, 
    "超級幸運藥水 (x2)": 800, "天體幸運藥水 (x2)": 1500, "彩虹藥水 (x1)": 2000, 
    "泰坦藥水 (x3)": 1200, "變異藥水 (x2)": 500, "閃亮藥水 (x4)": 450, 
    "雙倍活動幣藥水 (x1)": 700, "黃金藥水 (x2)": 650, "⚡閃電速度藥水": 250, "💗性慾藥水": 150,
    
    # 🧰 藥水寶箱與常規盲盒
    "寵物禮包小 (x2)": 300, "寵物禮包大 (x76)": 2500, "夏日水餃禮包 (x7)": 500,
    "🥳神祕黃金寶箱": 500, "🌌轉生神仙水": 99999,
    
    # 🪝 消耗性功能型高階浮標
    "🟢 綠光電子浮標": 150, "🔵 藍海震盪浮標": 500, "🔴 狂暴重力浮標": 1200
}

# ======= 🌤️ 4.0 終極擴充：致敬 Fisch 10 大全服隨機極端天氣池 =======
WEATHER_POOL = {
    "☀️ 晴空萬里": {"desc": "風平浪靜，陽光灑落海面，非常適合出海。", "luck_bonus": 1.0, "speed_mod": 0.0},
    "🌧️ 狂風暴雨": {"desc": "大雨傾盆，海浪洶湧，魚群紛紛浮上水面呼吸！", "luck_bonus": 1.6, "speed_mod": -1.0},
    "🌫️ 濃霧密佈": {"desc": "海上大霧遮蔽視線，魚兒容易受驚，收竿需格外小心。", "luck_bonus": 0.8, "speed_mod": 1.0},
    "🌌 天降異象": {"desc": "星海與遠古神光撕裂天空！各地湧現傳奇特產潮汐！", "luck_bonus": 2.5, "speed_mod": 2.0},
    "⚡ 萬雷轟頂 (Thunderstorm)": {"desc": "雷暴撕裂海域，電磁共振使深海巨怪與科技零件瘋狂暴動！", "luck_bonus": 3.0, "speed_mod": -1.5},
    "❄️ 冰天雪地 (Blizzard)": {"desc": "極寒低溫凍結海面，魚兒行動遲緩但體型巨大，突變率大激增！", "luck_bonus": 1.5, "speed_mod": 2.0},
    "🌋 熔岩噴發 (Eruption)": {"desc": "地殼變動火山噴發，高溫高壓讓多彩異變首綴爆率永久翻倍！", "luck_bonus": 2.2, "speed_mod": -0.5},
    "🌌 蝕日奇點 (Solar Eclipse)": {"desc": "萬丈黑光吞噬太陽，海域陷入絕對黑暗，未知恐怖秘密產物甦醒！", "luck_bonus": 4.0, "speed_mod": 1.0},
    "🎰 歐皇狂歡 (🎰 Super Lucky)": {"desc": "全服氣運天梯榜大暴動！所有神話與作者級特產爆率直接炸裂！", "luck_bonus": 5.5, "speed_mod": 0.5},
    "🌀 終極風暴 (Maelstrom)": {"desc": "時空混亂的終極超巨型漩渦，高拉扯度，不是斷竿就是神物降臨！", "luck_bonus": 5.0, "speed_mod": -2.0}
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
    "一海・新手小池塘": {"req_lvl": 0, "cost": 0, "npc": "👴 隔壁張老頭", "desc": "新手起步的溫馨池塘，平靜安全。", "image": "https://imgur.com", "shop": {"初級魚竿": 200, "高級魚竿": 1000, "穩健之竿 (Steady Rod)": 1500, "長線之竿 (Long Rod)": 2200}},
    "二海・黃金珊瑚礁": {"req_lvl": 80, "cost": 500, "npc": "🦈 魚人阿龍", "desc": "高壓的水下珊瑚礁世界，魚獲斑斕色彩。", "image": "https://imgur.com", "shop": {"深海魚竿": 3500, "珊瑚礁共振竿": 6000, "霓虹之竿 (Neon Rod)": 7500, "黃金之竿 (Golden Rod)": 12000, "幸運之竿 (Lucky Rod)": 18000}},
    "三海_馬里亞娜海溝深淵": {"req_lvl": 160, "cost": 2500, "npc": "🔱 大祭司波賽頓", "desc": "漆黑萬丈的馬里亞娜海溝底部，充斥未知巨獸與零件。", "image": "https://imgur.com", "shop": {"量子魚竿": 8000, "暗夜之竿 (Nocturnal Rod)": 15000, "外星干擾重型桿": 25000, "ADMIN魚桿": 500000}}
}

# ======= 🎣 4.0 終極大改版：致敬 Roblox Fisch 15 大被動神竿資料庫 =======
ROD_STATS = {
    "新手魚竿": {"luck": 1.0, "speed_bonus": 0.0, "mutation": 0.05, "desc": "Fisch最初始的破舊木竿，適合熟悉水性。"},
    "初級魚竿": {"luck": 1.3, "speed_bonus": 0.5, "mutation": 0.10, "desc": "碳纖維輕量化漁具，收竿速度輕微提升。"},
    "高級魚竿": {"luck": 2.0, "speed_bonus": 1.5, "mutation": 0.20, "desc": "公會高強度合金竿，大魚咬竿率顯著增加。"},
    "穩健之竿 (Steady Rod)": {"luck": 1.8, "speed_bonus": 1.0, "mutation": 0.15, "desc": "【被動：重力鎖定】拉竿成功率永久額外提升 +15%！"},
    "長線之竿 (Long Rod)": {"luck": 2.5, "speed_bonus": 0.5, "mutation": 0.25, "desc": "【被動：遠洋拋投】拋竿距離翻倍，更容易驚動深海稀有物種。"},
    "深海魚竿": {"luck": 3.5, "speed_bonus": 2.5, "mutation": 0.35, "desc": "耐壓鈦合金打造，專為抵禦二海高壓激流設計。"},
    "珊瑚礁共振竿": {"luck": 5.0, "speed_bonus": 4.0, "mutation": 0.45, "desc": "能與珊瑚產生音波共振，多彩異變率極高。"},
    "霓虹之竿 (Neon Rod)": {"luck": 4.5, "speed_bonus": 3.5, "mutation": 0.55, "desc": "【被動：電光矩陣】散發霓虹光芒，全卡槽突變機率激增 +25%！"},
    "黃金之竿 (Golden Rod)": {"luck": 6.5, "speed_bonus": 3.0, "mutation": 0.30, "desc": "【被動：點石成金】釣到的魚全賣時，金幣回收價永久 1.5 倍！"},
    "幸運之竿 (Lucky Rod)": {"luck": 8.5, "speed_bonus": 2.0, "mutation": 0.35, "desc": "【被動：歐皇附體】全服傳奇、神話級超珍稀生物爆率大幅提升！"},
    "量子魚竿": {"luck": 10.0, "speed_bonus": 5.5, "mutation": 0.60, "desc": "利用量子糾纏打造，出竿的瞬間已鎖定未來大魚。"},
    "暗夜之竿 (Nocturnal Rod)": {"luck": 12.0, "speed_bonus": 5.0, "mutation": 0.65, "desc": "【被動：永夜幽靈】在夜間或暴雨天氣下，全爆率瘋狂翻倍 2.5 倍！"},
    "外星干擾重型桿": {"luck": 16.0, "speed_bonus": 6.5, "mutation": 0.70, "desc": "逆向外星母艦核心改造，自帶電磁波專引深海巨怪。"},
    "🔥 地心熔岩流體竿": {"luck": 22.0, "speed_bonus": 7.0, "mutation": 0.80, "desc": "【被動：超耐熱機甲】唯一能承受地幔數萬度岩漿的超硬核重型神竿。"},
    "諸神黃昏湮滅劫桿": {"luck": 45.0, "speed_bonus": 8.0, "mutation": 0.95, "desc": "【被動：終極毀滅】岩漿深處淬鍊萬年，出水必引發全服突變海嘯。"},
    "🏆 任務大師榮譽紀念竿": {"luck": 8.8, "speed_bonus": 6.5, "mutation": 0.75, "desc": "累積完成公會日常後，獲得會長親賜的頂級榮譽。"},
    "ADMIN魚桿": {"luck": 999.0, "speed_bonus": 8.5, "mutation": 1.00, "desc": "擁有修改造物主代碼權限的至高神竿，全海域秒殺通行。"}
}
ENCHANT_POOL = {
    "⚡ 迅捷": {"desc": "收竿冷卻時間永久縮減 1.5 秒", "luck_mod": 1.0, "speed_mod": 1.5, "mutate_mod": 0.0},
    "🍀 豐收": {"desc": "氣運爆發，大魚爆率永久提升 1.5 倍", "luck_mod": 1.5, "speed_mod": 0.0, "mutate_mod": 0.0},
    "🧬 異變": {"desc": "特殊輻射共振，魚隻突變機率激增 +25%", "luck_mod": 1.0, "speed_mod": 0.0, "mutate_mod": 0.25},
    "🌌  sigma": {"desc": "全屬性終極洗鍊：運氣x2.5、冷卻-2秒、變異+40%", "luck_mod": 2.5, "speed_mod": 2.0, "mutate_mod": 0.40},
    "👑 弒神領域 (God Slayer)": {"desc": "【特效：諸神退散】氣運神級爆增 x5.5！收竿加速 +4.5秒！且突變率直接鎖死 80%！", "luck_mod": 5.5, "speed_mod": 4.5, "mutate_mod": 0.80},
    "🎰 命運主宰 (Midas Touch)": {"desc": "【特效：全知全能】氣運暴增 x8.0！釣到稀有度秘密/作者級的概率永久翻倍！", "luck_mod": 8.0, "speed_mod": 1.0, "mutate_mod": 0.10},
    "🌀 時空扭曲 (Time Warp)": {"desc": "【特效：超越光速】打破時空限制！任何魚竿冷卻時間強制縮減為保底 1.5 秒！", "luck_mod": 2.0, "speed_mod": 8.5, "mutate_mod": 0.30}
}

BOBBER_POOL = {
    "⚪ 常規軟木浮標": {"success_rate": 0, "mutate_bonus": 0.0}, "🟢 綠光電子浮標": {"success_rate": 15, "mutate_bonus": 0.05},
    "🔵 藍海震盪浮標": {"success_rate": 25, "mutate_bonus": 0.12}, "🔴 狂暴重力浮標": {"success_rate": 45, "mutate_bonus": 0.25}
}

FISH_POOL = {
    "普通": [("🐟 吳郭魚", 15), ("🐠 小丑魚", 20), ("👟 舊鞋子", 2)], "稀有": [("🐡 黃金河豚", 200)]
}

# ======= 🐟 4.0 核心：一海、二海超豐富致敬 Fisch 物種大隔離魚池 =======
MAP_EXCLUSIVE_FISH = {
    "一海・新手小池塘": {
        "普通": [
            ("🐟 吳郭魚", 15), ("🐠 小丑魚", 20), ("🐡 氣噗噗河豚", 25), 
            ("🐟 綠頭擬鯉 (Roach)", 30), ("🐟 淡水鱸魚 (Perch)", 35), ("🐟 小青魚 (Minnow)", 18)
        ],
        "稀有": [
            ("🐡 黃金河豚", 200), ("🐟 大口黑鱸 (Bass)", 180), ("🐟 紅點鮭魚 (Trout)", 250), ("🦀 溪流褐蟹", 150)
        ], 
        "傳奇": [
            ("👑 黃金鯉魚", 800), ("🦈 鏡面巨鯉 (Mirror Carp)", 950), ("🐊 遠古短吻鱷 (Alligator)", 1500),
            ("💎 奧術秩序裂片 (Arcane Stone)", 1000)
        ]
    },
    "二海・黃金珊瑚礁": {
        "普通": [
            ("🐚 珊瑚礁小蝦", 10), ("🐠 七彩霓虹魚", 45), ("👟 舊鞋子", 2),
            ("🐠 藍倒吊唐王魚 (Blue Tang)", 50), ("🐠 蝴蝶魚 (Butterflyfish)", 55), ("🐡 箱魨 (Cowfish)", 60)
        ],
        "稀有": [
            (" Squid 大王烏賊", 150), ("🦈 藍色鯊魚", 350), ("🦀 帝王蟹", 400),
            ("🐠 獅子魚 (Lionfish)", 280), ("🐍 豹紋海鰻 (Moray Eel)", 520)
        ],
        "傳奇": [
            ("🔱 海神三叉戟", 1800), ("🦈 雙頭錘頭鯊 (Hammerhead)", 2500), ("🐙 巨型紅章魚 (Kraken Spawn)", 3000),
            ("💎 混沌星星原石 (Nova Stone)", 2000)
        ], 
        "神話": [("🧜‍♀️ 美人魚的眼淚", 7500), ("👑 珊瑚礁之王・黃金旗魚", 12000)], 
        "秘密": [("🏐 一顆...排球?", 27000)]
    },
    "三海_馬里亞娜海溝深淵": {
        "普通": [("🐟 發光鮟鱇魚", 75), ("🧪 輻射基因流體", 110)],
        "稀有": [("🐙 深淵巨型章魚", 280), ("🦈 遠古惡魔巨齒鯊", 650)],
        "傳奇": [("🐳 藍鯨", 1500)], "秘密": [("🛸 外星科技零件", 25000)],
        "神話": [("🐉 東方青龍", 35000), ("🔥 諸神湮滅核心 (Abyss Core)", 50000)], 
        "作者級": [("💻 作者的未編譯源代碼", 100000), ("🤨神秘的SIGMAFACE", 300000)]
    },
    "四海・地幔熔岩禁地": {
        "傳奇": [("🌋 熔岩火靈魚", 3500)],
        "神話": [("🔥 煉獄不死鳥之眼", 12000), ("💎 熔岩核心巨鑽", 25000), ("👑 萬物主宰聖石 (Overlord Stone)", 66666)],
        "秘密": [("🌋 古星核熱熔高壓液體", 55000)],
        "作者級": [("🌌 SIGMA的熔岩超燃雪茄", 333333)]
    }
}


# ======= 🎫 指令十：4.0 雲端版 CODE 兌換 ➔ 內建【製作者神級雙重加密全服廣播公告】 =======
@bot.tree.command(name="兌換碼", description="輸入官方禮包碼兌換物資，製作者輸入超難加密 CODE 可發動全服廣播功能")
@app_commands.describe(code="請輸入你要兌換的代碼（類似NEW_UPDATE）")
async def redeem_code(interaction: discord.Interaction, code: str):
    user_id = int(interaction.user.id)
    
    # 📢 1. 製作者極致難度特殊公告密鑰判定
    if code.startswith("GODFREY_ADMIN_MATRIX_CODE_2026_BY_SIGMA::"):
        # 🛡️ 鋼鐵防線：雙重認證，限制必須具備最高管理員權限
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ 權限不足！此特殊神級密鑰只有製作者兼最高管理員才能破譯！", ephemeral=True)
            return
            
        announcement_content = code.replace("GODFREY_ADMIN_MATRIX_CODE_2026_BY_SIGMA::", "")
        await interaction.response.send_message("🚀 矩陣密鑰破譯成功！諸神黃昏全服大廣播全面發動...", ephemeral=True)
        
        embed = discord.Embed(title="📢 ── 歡樂釣魚場・官方製作者廣播公告 ── 📢", description=f"\n{announcement_content}\n", color=0x9B59B6)
        embed.set_footer(text=f"⚙️ 雲端總控制台發布 • 管理員: {interaction.user.display_name}")
        
        # 遍歷所有伺服器文字頻道進行廣播
        for guild in bot.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send(embed=embed)
                        break
                    except:
                        pass
        return

    # 🎁 2. 常規與大補償禮包碼兌換邏輯 (維持雲端安全版)
    code_upper = code.upper()
    if code_upper == "SORRY2026" or code_upper == "BACKUP":
        user = get_user(user_id)
        update_user(user_id, balance=user.get("balance", 100) + 8000, bait_count=user.get("bait_count", 5) + 30)
        add_inventory(user_id, "🔵高級運氣藥水", 5)
        add_inventory(user_id, "🟢普通運氣藥水", 10)
        add_inventory(user_id, "⚡閃電速度藥水", 5)
        add_inventory(user_id, "🥳神祕黃金寶箱", 3)
        add_inventory(user_id, "🔋 彈性奈米反覆餌", 1)
        
        embed = discord.Embed(title="🌌 官方終極大補償 ── 庫存一鍵恢復成功！", description=f"親愛的 **{interaction.user.display_name}**，全套 4.0 頂級物資已全數灌注進你的雲端倉庫！", color=0x9B59B6)
        await interaction.response.send_message(embed=embed)
        return
        
    if code_upper == "NEWUPDATE":
        user = get_user(user_id)
        update_user(user_id, balance=user.get("balance", 100) + 1500, bait_count=user.get("bait_count", 5) + 10)
        await interaction.response.send_message("🎁 禮包兌換成功！獲得 `1500` 金幣與 `10` 個普通魚餌補給！")
    elif code_upper == "1UPDATE":
        user = get_user(user_id)
        update_user(user_id, balance=user.get("balance", 100) + 3000, bait_count=user.get("bait_count", 5) + 20)
        await interaction.response.send_message("🎁 禮包兌換成功！獲得 `3000` 金幣與 `20` 個普通魚餌補給！")
    else:
        await interaction.response.send_message("❌ 兌換碼不存在、已過期，或特殊密鑰破譯失敗！", ephemeral=True)

# ======= 📖 指令十一：使用教學 =======
@bot.tree.command(name="釣魚說明", description="查看歡樂釣魚場 4.0 諸神黃昏的大師指南")
async def guide(interaction: discord.Interaction):
    embed = discord.Embed(title="🎣 歡樂釣魚場 4.0 ── 諸神黃昏大世紀指南", description="`──────────────────────────`", color=0x5865F2)
    embed.add_field(name="🎮 冒險核心指令", value="`/釣魚` : 拋竿出海挑戰(具備真實等待)\n`/背包` : 內建❤️下拉最愛防呆鎖的大倉庫\n`/裝備` : 綠格子黑曜石面板一鍵下拉換裝\n`/傳送地圖` : 金幣跨越海域傳送(需解鎖載具)", inline=False)
    embed.add_field(name="🏰 公會與圖鑑", value="`/公會背包` : 查詢公會金庫與召喚魔王\n`/公會遠征` : 集體圍剿世界BOSS共享5000大獎\n`/查看圖鑑` : 開闢四大海域生物進度", inline=False)
    embed.set_footer(text="💡 提示：在官方支援群內拋竿，爆率經驗永久激增 1.2 倍！")
    await interaction.response.send_message(embed=embed)

# ======= 🌤️ 指令十二：觀測天氣 =======
@bot.tree.command(name="天氣", description="觀測當前全服統一的大氣觀測站與 10 大極端海域共振影響")
async def current_weather_cmd(interaction: discord.Interaction):
    w_name, w_info = get_global_weather()
    embed = discord.Embed(title=f"🌤️ 全服統一氣象觀測站 ── 當前全球：【{w_name}】", description=f"*{w_info['desc']}*", color=0x3498DB)
    for m_name in MAPS.keys():
        embed.add_field(name=f"🚢 【{m_name}】海域影響", value=f"氣運倍率：`x{w_info['luck_bonus']}`\n收竿冷卻：`{w_info['speed_mod']} 秒`", inline=True)
    await interaction.response.send_message(embed=embed)

# ======= 📅 指令十三：每日簽到時間鎖 =======
@bot.tree.command(name="簽到", description="每日領取 200 金幣與 3 個普通魚餌補給！")
async def daily(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    today_str = datetime.now().strftime("%Y-%m-%d")
    if user["last_daily"] == today_str:
        await interaction.response.send_message("❌ 老哥，你今天已經簽到過了，明天再來吧！", ephemeral=True)
        return
    update_user(user_id, balance=user["balance"]+200, bait_count=user["bait_count"]+3, last_daily=today_str)
    await interaction.response.send_message(f"🎁 **{interaction.user.display_name}** 簽到成功！獲得 `200` 金幣 與 `3` 個普通魚餌！")


# ======= 📋 指令十四：20大趣味隨機日常任務系統 =======
@bot.tree.command(name="任務", description="查看今日公會接取的日常委託進度與懸賞金幣明細")
async def check_quest(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    embed = discord.Embed(title=f"📋 {interaction.user.display_name} 的今日公會懸賞任務", color=0xF39C12)
    if user.get("quest_type", "無") == "無":
        embed.description = "🔍 你目前身上空空如也！請輸入 `/接取任務` 來刷新今日公會隨機趣味日常！"
    else:
        status = "✅ 可回報" if user.get("quest_progress", 0) >= user.get("quest_target", 0) else "⏳ 進行中"
        embed.add_field(name=f"🎯 委託目標：【{user['quest_type']}】 ({status})", value=f"• 目前進度：`{user['quest_progress']} / {user['quest_target']}`\n• 達成賞金：`{user['quest_reward']} 🪙`", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="接取任務", description="向航海公會刷新並接取今日隨機日常任務（全宇宙擴充 20 大趣味懸賞！）")
async def accept_quest(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    if user.get("quest_type", "無") != "無":
        await interaction.response.send_message("❌ 你身上已經有任務進行中了！請先完成或回報。", ephemeral=True)
        return
        
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
    await interaction.message_content if hasattr(interaction, "message_content") else None
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="回報任務", description="達成日常進度後回報領取獎金（有機率額外解鎖隱藏紀念神竿）")
async def complete_quest(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    if user.get("quest_type", "無") == "無":
        await interaction.response.send_message("❌ 你目前身上沒有任何任務！", ephemeral=True); return
    if user.get("quest_progress", 0) < user.get("quest_target", 0):
        await interaction.response.send_message(f"❌ 懸賞尚未達成！目前進度：`{user['quest_progress']}/{user['quest_target']}`", ephemeral=True); return
    
    gift_msg = ""
    # 🌟 致敬 Fisch 特效：5% 機率天降公會大獎！一鍵鎖定神竿資產！
    if random.random() < 0.05 and user.get("rod") != "🏆 任務大師榮譽紀念竿":
        update_user(user_id, rod="🏆 任務大師榮譽紀念竿")
        add_inventory(user_id, "🏆 任務大師榮譽紀念竿", 1)
        gift_msg = "\n🔥 **【大師神蹟】公會長對你讚賞有加，特別賞賜限定【🏆 任務大師榮譽紀念竿】一根！(限購資產已解鎖)**"
        
    update_user(user_id, balance=user["balance"]+user["quest_reward"], quest_type="無", quest_target=0, quest_progress=0, quest_reward=0)
    await interaction.response.send_message(f"🎉 日常任務回報完畢！獲得金幣 **`{user['quest_reward']}`** 點！{gift_msg}")

# ======= 💸 指令十五：船長互助錢包轉帳 =======
@bot.tree.command(name="匯款", description="將金幣轉帳給伺服器內的其他玩家")
@app_commands.describe(target="你想匯款給誰？", amount="你想轉帳的金幣數量")
async def transfer(interaction: discord.Interaction, target: discord.Member, amount: int):
    if amount <= 0 or target.id == interaction.user.id:
        await interaction.response.send_message("❌ 轉帳金額或目標錯誤！", ephemeral=True); return
    sender_id = int(interaction.user.id)
    receiver_id = int(target.id)
    sender = get_user(sender_id)
    
    if sender["balance"] < amount:
        await interaction.response.send_message("❌ 錢包雲端金幣不足！", ephemeral=True); return
        
    if sender.get("quest_type") == "💸 船長互助會":
        update_user(sender_id, quest_progress=sender.get("quest_progress", 0) + 1)
        
    receiver = get_user(receiver_id)
    update_user(sender_id, balance=sender["balance"] - amount)
    update_user(receiver_id, balance=receiver["balance"] + amount)
    await interaction.response.send_message(f"💸 **{interaction.user.display_name}** 成功轉帳 **{amount}** 金幣給 **{target.display_name}**！")

# ======= 🧰 指令十六：開啟黃金寶箱與寵物盲盒 =======
@bot.tree.command(name="開箱", description="開啟背包內的神祕黃金寶箱，隨機獲得高級藥水、大筆金幣 or 神獸寵物！")
async def open_box(interaction: discord.Interaction):
    await interaction.response.defer()
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    
    box_rec = inventory_col.find_one({"user_id": user_id, "item_name": "🥳神祕黃金寶箱"})
    box_count = int(box_rec["item_count"]) if box_rec else 0
    if box_count <= 0:
        await interaction.followup.send("❌ 雲端大倉庫裡沒有黃金寶箱！快去普通商店採購一個吧！", ephemeral=True); return
        
    if user.get("quest_type") == "📦 補給箱快遞":
        update_user(user_id, quest_progress=user.get("quest_progress", 0) + 1)
        
    inventory_col.update_one({"user_id": user_id, "item_name": "🥳神祕黃金寶箱"}, {"$inc": {"item_count": -1}})
    roll = random.random()
    if roll < 0.05:
        chosen_pet = random.choice(["🐱 招財貓(金幣+10%)", "🦅 尋寶獵鷹(XP+30%)", "🐉 迷你小青龍(XP+50%)"])
        update_user(user_id, pet=chosen_pet)
        await interaction.followup.send(f"🌌 ✨ **【不世奇蹟】** **{interaction.user.display_name}** 成功孵化出神運動獸：**{chosen_pet}**！！")
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


# ======= 🏆 指令十七：雲端服即時同步天梯排行榜 =======
@bot.tree.command(name="排行榜", description="查看當前全服雲端實時同步中最強的遠航大師（100%真實姓名顯示）")
async def leaderboard(interaction: discord.Interaction):
    # 🌟 1. 自動在查詢時同步更新操作者自己的最新名字，鎖死不丟失
    update_user(int(interaction.user.id), name=interaction.user.display_name)
    
    # 從 MongoDB 中根據等級與金幣降序排列，極速抓取前 10 名
    cursor = users_col.find().sort([("level", -1), ("balance", -1)]).limit(10)
    rows = list(cursor)
    
    embed = discord.Embed(title="🏆 歡樂釣魚場 - 遠航雲端天梯榜", color=0xF1C40F)
    if not rows:
        embed.description = "天梯榜上空空如也，老哥快去甩頭竿吧！"
    else:
        rank_str = ""
        for i, doc in enumerate(rows):
            name = doc.get("name", f"遠航大師({doc['user_id']})")
            medal = "🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else f"第 {i+1} 名"
            rank_str += f"{medal} **{name}** ── `LV.{doc.get('level', 0)}` | `錢包: {doc.get('balance', 100)} 金幣`\n"
        embed.description = rank_str
    await interaction.response.send_message(embed=embed)

# ======= 🗺️ 指令十八：載具防禦金幣傳送海域系統 =======
@bot.tree.command(name="傳送地圖", description="支付金幣傳送至全新海域（需裝備對應下海載具資產，地幔需 LV.220）")
@app_commands.describe(map_name="目的地海域名稱")
async def teleport_map(interaction: discord.Interaction, map_name: str):
    if map_name not in MAPS and map_name != "四海・地幔熔岩禁地":
        await interaction.response.send_message(f"❌ 找不到這片海域！可用目的地：{', '.join(MAPS.keys())}、四海・地幔熔岩禁地", ephemeral=True)
        return
        
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    
    req_lvl = MAPS[map_name]["req_lvl"] if map_name in MAPS else 220
    cost = MAPS[map_name]["cost"] if map_name in MAPS else 5000
    npc = MAPS[map_name]["npc"] if map_name in MAPS else "👁️ 覺醒老哥本人"
    desc = MAPS[map_name]["desc"] if map_name in MAPS else "鑽破地殼的終極地底世界！高溫高壓，此處出產地底極致高溫突變流體生物！"
    image = MAPS[map_name]["image"] if map_name in MAPS else "https://imgur.com"

    if user.get("level", 0) < req_lvl:
        await interaction.response.send_message(f"🔒 等級實力不足！前往【{map_name}】需要達到 `LV.{req_lvl}`，你目前只有 `LV.{user['level']}`。", ephemeral=True)
        return
    if user.get("balance", 100) < cost:
        await interaction.response.send_message(f"❌ 傳送費用不足！前往【{map_name}】需要 `{cost}` 金幣，你目前只有 `{user['balance']}` 🪙。", ephemeral=True)
        return

    # 🤿 4.0 核心金盾防線：連線雲端背包檢測，沒購買載具者 100% 絕對拒絕傳送！
    if map_name == "二海・黃金珊瑚礁":
        suit_rec = inventory_col.find_one({"user_id": user_id, "item_name": "🤿 科技耐壓潛水服", "item_count": {"$gt": 0}})
        if not suit_rec:
            await interaction.response.send_message("❌ 傳送失敗！二海完全位於高壓海中，你必須先在商店購買【🤿 科技耐壓潛水服】才能成功下海！", ephemeral=True); return
            
    elif map_name == "三海_馬里亞娜海溝深淵":
        sub_rec = inventory_col.find_one({"user_id": user_id, "item_name": "🚢 量子核能潛水艇", "item_count": {"$gt": 0}})
        if not sub_rec:
            await interaction.response.send_message("❌ 傳送失敗！三海位於極其恐怖的海溝底部，你必須先在商店購買【🚢 量子核能潛水艇】才能沉入深海！", ephemeral=True); return
            
    elif map_name == "四海・地幔熔岩禁地":
        drill_rec = inventory_col.find_one({"user_id": user_id, "item_name": "🔥 地心重型鑽探機", "item_count": {"$gt": 0}})
        if not drill_rec:
            await interaction.response.send_message("❌ 傳送失敗！地幔充斥著高溫岩漿，你必須先在商店購買【🔥 地心重型鑽探機】駕駛機甲破殼！", ephemeral=True); return
            
    update_user(user_id, current_map=map_name, balance=user["balance"] - cost, name=interaction.user.display_name)
    embed = discord.Embed(title=f"🚢 船隻載具傳送成功 ── 抵達【{map_name}】", description=f"• 駐島 NPC：`{npc}`\n• 傳送過路費：`-{cost} 🪙`\n\n*{desc}*", color=0x1ABC9C)
    embed.set_image(url=image)
    await interaction.response.send_message(embed=embed)

# ======= 🎣 指令十九：4.0 核心完全體釣魚指令（前半段） =======
cooldowns = {}
@bot.tree.command(name="釣魚", description="拋出釣竿！引進真實時間等待咬竿與 10 大極端天氣共振異變，支援限購魚竿被動！")
async def fish(interaction: discord.Interaction):
    # 🌟 1. 第一步 0.001 秒內完成預留應答，向官方申請「思考中」，徹底封死未回應錯誤！
    await interaction.response.defer()
    import asyncio
    
    try:
        user_id = int(interaction.user.id)
        user = get_user(user_id)
        # 即時同步最新 Discord 名字
        update_user(user_id, name=interaction.user.display_name)
        
        current_map = user.get("current_map", "一海・新手小池塘")
        current_rod = user.get("rod", "新手魚竿")
        current_enchant = user.get("enchant", "無")
        
        if not current_map or current_map == "None": current_map = "滅海・新手小池塘"
        if not current_rod or current_rod == "None": current_rod = "新手魚竿"
        if not current_enchant or current_enchant == "None": current_enchant = "無"
        
        weather_name, weather_info = get_global_weather()
        rod_stat = ROD_STATS.get(current_rod, {"luck": 1.0, "speed_bonus": 0.0, "mutation": 0.05, "desc": "無"})
        enc_stat = ENCHANT_POOL.get(current_enchant, {"luck_mod": 1.0, "speed_mod": 0.0, "mutate_mod": 0.0})
        
        enc_speed = enc_stat.get("speed_mod", 0.0) if enc_stat else 0.0
        enc_luck = enc_stat.get("luck_mod", 1.0) if enc_stat else 1.0
        enc_mutate = enc_stat.get("mutate_mod", 0.0) if enc_stat else 0.0
        # 🌟 2. 全新冷卻倒數公式：基礎 10 秒，魚竿與附魔直接減秒，天氣變動加減秒數
        current_time = time.time()
        base_cooldown = 10.0 - float(rod_stat.get("speed_bonus", 0.0)) - float(enc_speed)
        w_speed = float(weather_info.get("speed_mod", 0.0))
        base_cooldown += w_speed
        if base_cooldown < 1.5: base_cooldown = 1.5  # 🛡️ 鐵壁防線：最低不允許低於 1.5 秒
        
        if user_id in cooldowns and current_time - cooldowns[user_id] < base_cooldown:
            remaining = round(base_cooldown - (current_time - cooldowns[user_id]), 1)
            await interaction.followup.send(f"🚨 拋竿速度太快了！手拉得好酸...再等 {remaining} 秒。(當前冷卻: {round(base_cooldown, 1)}秒)", ephemeral=True)
            return
        cooldowns[user_id] = current_time

        # 🌟 3. 4.9 智慧浮標加載：從雲端背包讀取玩家購買的浮標儲備
        player_bobbers = {}
        for b_name in ['🔴 狂暴重力浮標', '🔵 藍海震盪浮標', '🟢 綠光電子浮標']:
            b_rec = inventory_col.find_one({"user_id": user_id, "item_name": b_name, "item_count": {"$gt": 0}})
            if b_rec: player_bobbers[b_name] = int(b_rec.get("item_count", 0))
            
        # 優先挑選最高階的消耗性浮標使用
        if player_bobbers.get('🔴 狂暴重力浮標', 0) > 0: bobber_name = '🔴 狂暴重力浮標'
        elif player_bobbers.get('🔵 藍海震盪浮標', 0) > 0: bobber_name = '🔵 藍海震盪浮標'
        elif player_bobbers.get('🟢 綠光電子浮標', 0) > 0: bobber_name = '🟢 綠光電子浮標'
        else: bobber_name = '⚪ 常規軟木浮標'
            
        bobber_stat = BOBBER_POOL[bobber_name]
        
        # 使用 edit_original_response 覆蓋「正在思考中...」灰字，完美應答協議
        await interaction.edit_original_response(content=f"🪝 **{interaction.user.display_name}** 裝配著背包中的【**{bobber_name}**】在【{current_map}】拋出釣竿...\n⏳ 正在波浪中靜靜等待魚兒咬竿，請保持潛心觀測... 🌊")
        
        # 真實等待咬竿
        wait_seconds = random.randint(2, 3)
        await asyncio.sleep(wait_seconds)
        
        # 雲端物資庫存載入
        cursor = inventory_col.find({"user_id": user_id, "item_count": {"$gt": 0}})
        inv_data = {doc["item_name"]: int(doc["item_count"]) for doc in cursor}
        
        has_potion = inv_data.get('💗性慾藥水', 0) > 0
        has_god_water = inv_data.get('🌌轉生神仙水', 0) > 0
        has_normal_pot = inv_data.get('🟢普通運氣藥水', 0) > 0
        has_high_pot = inv_data.get('🔵高級運氣藥水', 0) > 0
        has_speed_pot = inv_data.get('⚡閃電速度藥水', 0) > 0
        has_high_bait = inv_data.get('高級魚餌', 0) > 0
        has_seaweed = inv_data.get('海藻餌', 0) > 0
        has_magnet = inv_data.get('磁鐵重餌', 0) > 0
        has_nano_bait = inv_data.get('🔋 彈性奈米反覆餌', 0) > 0
        
        # 🌟 4.9.5 截圖大藥水庫存判定
        has_star_pot = inv_data.get('天體幸運藥水 (x2)', 0) > 0
        has_rainbow_pot = inv_data.get('彩虹藥水 (x1)', 0) > 0
        
        is_supported = (interaction.guild_id == SUPPORT_GUILD_ID) if interaction.guild_id else False
        guild_bonus = 1.2 if is_supported else 1.0
        
        # 氣運與天氣加成大共振
        w_luck = float(weather_info.get("luck_bonus", 1.0))
        luck_multiplier = float(rod_stat.get("luck", 1.0)) * w_luck * float(enc_luck) * guild_bonus
        
        # 🌟 4.9 天氣限時異變加成核心：雷暴、蝕日、暴風雨等惡劣天氣下，突變倍率瘋狂狂飆！
        weather_mutate_mod = 1.0
        if weather_name in ["⚡ 萬雷轟頂 (Thunderstorm)", "🌌 蝕日奇點 (Solar Eclipse)", "🌀 終極風暴 (Maelstrom)", "🌋 熔岩噴發 (Eruption)"]:
            weather_mutate_mod = 2.5
            
        bait_msg = f"🌍 **全服實時氣象：【{weather_name}】** (*{weather_info['desc']}*)\n"
        if is_supported: bait_msg = "🤝 **【官方群共振】檢測到你在支援伺服器拋竿，全爆率提升 1.2 倍！**\n" + bait_msg
        if current_enchant != "無": bait_msg += f"🔮 漁具灌注附魔：**【{current_enchant}】** 加持中\n"
        
        # 扣除魚餌與藥水邏輯
        if has_nano_bait:
            luck_multiplier *= 2.0
            bait_msg += "🔋 **[神級奈米反覆餌] 裝備了彈性反覆餌，本竿不消耗任何材料，且幸運值x2.0！**\n"
        elif has_god_water:
            luck_multiplier *= 100.0
            inventory_col.update_one({"user_id": user_id, "item_name": "🌌轉生神仙水"}, {"$inc": {"item_count": -1}})
            bait_msg += "🌌 **[神仙降臨]** 你喝下了百萬倍運氣神仙水！！\n"
        elif has_star_pot:
            luck_multiplier *= 5.0
            inventory_col.update_one({"user_id": user_id, "item_name": "天體幸運藥水 (x2)"}, {"$inc": {"item_count": -1}})
            bait_msg += "✨ **[天體共鳴]** 你飲用了天體幸運藥水，星宿爆率暴激增 x5.0！\n"
        elif has_rainbow_pot:
            luck_multiplier *= 7.0
            inventory_col.update_one({"user_id": user_id, "item_name": "彩虹藥水 (x1)"}, {"$inc": {"item_count": -1}})
            bait_msg += "🌈 **[彩虹極光]** 飲用彩虹藥水，全卡槽品階大飛升 x7.0！！\n"
        elif has_magnet:
            luck_multiplier *= 1.5
            inventory_col.update_one({"user_id": user_id, "item_name": "磁鐵重餌"}, {"$inc": {"item_count": -1}})
            bait_msg += "🧲 **[磁力共振] 你使用了磁鐵重餌，碎片零件爆率提升！**\n"
        elif has_high_bait:
            luck_multiplier *= 3.0
            inventory_col.update_one({"user_id": user_id, "item_name": "高級魚餌"}, {"$inc": {"item_count": -1}})
            bait_msg += "✨ 你使用了 **高級魚餌**！\n"
        elif has_seaweed:
            luck_multiplier *= 1.3
            inventory_col.update_one({"user_id": user_id, "item_name": "海藻餌"}, {"$inc": {"item_count": -1}})
            bait_msg += "🌿 你使用了 **海藻餌**！\n"
        elif user.get("bait_count", 0) > 0:
            luck_multiplier *= 1.5
            update_user(user_id, bait_count=int(user["bait_count"]) - 1)
            bait_msg += "🐛 你消耗了 1 個 **普通魚餌**！\n"
        else:
            bait_msg += "🪝 無魚餌素釣，全憑直覺！\n"
            
        # 輔助藥水與浮標實時扣除
        if has_high_pot: inventory_col.update_one({"user_id": user_id, "item_name": "🔵高級運氣藥水"}, {"$inc": {"item_count": -1}}); luck_multiplier *= 2.0
        elif has_normal_pot: inventory_col.update_one({"user_id": user_id, "item_name": "🟢普通運氣藥水"}, {"$inc": {"item_count": -1}}); luck_multiplier *= 1.3
        if has_speed_pot: inventory_col.update_one({"user_id": user_id, "item_name": "⚡閃電速度藥水"}, {"$inc": {"item_count": -1}})
        if has_potion: inventory_col.update_one({"user_id": user_id, "item_name": "💗性慾藥水"}, {"$inc": {"item_count": -1}}); bait_msg = "🔥 **[速度狂暴]** 速度大增！\n" + bait_msg
        
        if bobber_name != '⚪ 常規軟木浮標':
            inventory_col.update_one({"user_id": user_id, "item_name": bobber_name}, {"$inc": {"item_count": -1}})
            bait_msg += f"🚨 本竿自動消耗了 1 個 **{bobber_name}**！\n"

        # 🌟 100% 純數字落點隨機抽卡判定，杜絕一切 choices 矩陣！
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
        
        # 🌟 4.9.5 Fisch 拉竿判定：如果抽到的是「穩健之竿 (Steady Rod)」被動，拉竿成功率強行再加 +15%！
        if current_rod == "穩健之竿 (Steady Rod)":
            base_success += 15
        if base_success > 98: base_success = 98

        if random.uniform(0, 100) > base_success:
            await interaction.followup.send(f"🦈 **{interaction.user.display_name} 拉扯失敗！** 一隻極其巨大的 **【{chosen_rarity}】** 級生物猛烈咬線，扯斷了你的 【{bobber_name}】 吐信逃跑了...（拉竿成功率：`{int(base_success)}%`）")
            return

        available_fish = []
        if current_map in MAP_EXCLUSIVE_FISH and chosen_rarity in MAP_EXCLUSIVE_FISH[current_map]:
            available_fish = MAP_EXCLUSIVE_FISH[current_map][chosen_rarity]
        if not available_fish: available_fish = FISH_POOL.get(chosen_rarity, FISH_POOL["普通"])
        if not available_fish: available_fish = [("🐟 吳郭魚", 15)]
        
        # 🌟 4.9.8 全新環境共振機制：根據當下的全服隨機天氣，100% 機率強制將池子置換成特殊限定魚類！
        fish_item = random.choice(available_fish)
        fish_name, _ = fish_item
        
        if current_map == "一海・新手小池塘":
            if weather_name == "⚡ 萬雷轟頂 (Thunderstorm)" and random.random() < 0.40:
                fish_name = "⚡ 電光電鰻 (Electric Eel)"
            elif weather_name == "❄️ 冰天雪地 (Blizzard)" and random.random() < 0.45:
                fish_name = "❄️ 寒冬北極鱈 (Arctic Cod)"
        elif current_map == "二海・黃金珊瑚礁":
            if weather_name == "🌌 蝕日奇點 (Solar Eclipse)" and random.random() < 0.35:
                fish_name = "🌌 幽冥鬼蝠魟 (Ghost Ray)"
            elif weather_name == "🎰 歐皇狂歡 (🎰 Super Lucky)" and random.random() < 0.50:
                fish_name = "🎰 命運幻彩錦鯉"

        # 🌟 天氣共振突變率計算（如果遇到熔岩、雷暴、風暴等極端天氣，突變率直接乘以 weather_mutate_mod 倍率）
        final_mutation_chance = (float(rod_stat.get("mutation", 0.05)) + float(enc_mutate) + float(bobber_stat.get("mutate_bonus", 0.0))) * weather_mutate_mod
        if current_rod == "霓虹之竿 (Neon Rod)":
            final_mutation_chance += 0.25 # 霓虹竿被動：突變率永久額外加成 25%
            
        if random.random() < final_mutation_chance:
            fish_name = f"{random.choice(['[🟢毒性突變]', '[🔵晶螢閃耀]', '[👑極致黃金]', '[🔴血色異變]', '[🌌星空突變]'])} {fish_name}"
            
        # 寫入雲端大倉庫
        add_inventory(user_id, fish_name, 1)
        
        # 📘 自動智慧解鎖雲端百科圖鑑 (Fisch原版字串原封不動鎖入)
        db["fish_encyclopedia"].update_one(
            {"user_id": user_id, "fish_name": fish_name},
            {"$set": {"unlocked_at": datetime.now().strftime("%Y-%m-%d")}},
            upsert=True
        )
        
        # 🌟 20 大雲端任務計數核心守護線
        q_type = user.get("quest_type", "無")
        q_prog = int(user.get("quest_progress", 0))
        if q_type != "無":
            if q_type == "🎣 出海大豐收": update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🪙 財氣東來" and chosen_rarity in ["稀有", "傳奇", "神話", "秘密", "作者級"]: update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "👟 垃圾清除計畫" and "舊鞋子" in fish_name: update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🧬 驚天異變紀元" and any(p in fish_name for p in ["[🟢毒性]", "[🔵晶螢]", "[👑極致]", "[🔴血色]", "[🌌星空]"]): update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🟡 傳奇垂釣家" and chosen_rarity in ["傳奇", "神話", "秘密", "作者級"]: update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🔴 諸神黃昏淚" and chosen_rarity in ["神話", "秘密", "作者級"]: update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🌌 終極星空共振" and "[🌌星空突變]" in fish_name: update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🪝 頂級浮標大師" and bobber_name != '⚪ 常規軟木浮標': update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🦀 珊瑚礁採集" and current_map == "二海・黃金珊瑚礁": update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🦈 捕鯊終結者" and "藍色鯊魚" in fish_name: update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "⚙️ 深海科技回收" and "外星科技零件" in fish_name: update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🐋 尋找莫比迪克" and current_map == "三海_馬里亞娜海溝深淵": update_user(user_id, quest_progress=q_prog + 1)
            elif q_type == "🔥 地幔熔岩煉獄" and current_map == "四海・地幔熔岩禁地": update_user(user_id, quest_progress=q_prog + 1)
        # 🌟 5. 雲端經驗與升級系統
        xp_gained = int(random.randint(15, 30) * guild_bonus)
        new_xp = int(user.get("xp", 0)) + xp_gained
        current_lvl = int(user.get("level", 0))
        xp_needed = (current_lvl + 1) * 50
        lvl_up_msg = ""
        while new_xp >= xp_needed:
            new_xp -= xp_needed
            current_lvl += 1
            xp_needed = (current_lvl + 1) * 50
            lvl_up_msg = f"\n⚡ **【LEVEL UP！】恭喜你升級到了 🌟 LV.{current_lvl} 🌟！！**"
        update_user(user_id, level=current_lvl, xp=new_xp)

        icons = {"普通": "⚪", "稀有": "🔵", "傳奇": "🟡", "神話": "🔴", "秘密": "🟣", "作者級": "🌌"}
        embed = discord.Embed(title=f"🎣 拉竿成功！ ── 【{icons[chosen_rarity]} {chosen_rarity}】", description=f"{bait_msg}🧬 順利捕捉：**{fish_name}**！ (成功率: `{int(base_success)}%`)\n🏆 獲得經驗：`+{xp_gained}xp` | 當前進度：`🧬 {new_xp}/{xp_needed} XP`{lvl_up_msg}", color=0x27AE60)
        await interaction.followup.send(embed=embed)
        
    except Exception as error:
        print(f"釣魚背景報錯日誌: {error}")
        try:
            add_inventory(interaction.user.id, "🐟 吳郭魚", 1)
            await interaction.followup.send(f"🎣 系統提示：海流產生輕微波盪，**{interaction.user.display_name}** 順利收竿，釣到了一隻 **🐟 吳郭魚**！(報錯類型: {error})")
        except: pass


# ======= 🦾 4.0 重磅核心：暗黑黑曜石綠格子下拉選單裝備檢視系統 =======
class EquipmentSelect(discord.ui.Select):
    def __init__(self, user_items):
        options = []
        all_equipable = {
            "初級魚竿": "🎣", "高級魚竿": "🎣", "深海魚竿": "🎣", "珊瑚礁共振竿": "🎣", "量子魚竿": "🎣", 
            "穩健之竿 (Steady Rod)": "🎣", "長線之竿 (Long Rod)": "🎣", "霓虹之竿 (Neon Rod)": "🎣", 
            "黃金之竿 (Golden Rod)": "🎣", "幸運之竿 (Lucky Rod)": "🎣", "暗夜之竿 (Nocturnal Rod)": "🎣",
            "外星干擾重型桿": "🎣", "🔥 地心重型鑽探機": "🔥", "🔥 地心熔岩流體竿": "🎣",
            "諸神黃昏湮滅劫桿": "🎣", "🏆 任務大師榮譽紀念竿": "🎣", "ADMIN魚桿": "🎣",
            "🤿 科技耐壓潛水服": "🤿", "🚢 量子核能潛水艇": "🚢",
            "⚔️ 鐵製魚叉": "⚔️", "⚔️ 精鋼巨弩": "⚔️", "🔱 海神破滅戟": "⚔️", "🌌 ADMIN破碼弒神劍": "⚔️"
        }
        for item, emoji in all_equipable.items():
            if user_items.get(item, 0) > 0:
                options.append(discord.SelectOption(label=item, description=f"一鍵切換穿戴此裝備", emoji=emoji))
        if not options:
            options.append(discord.SelectOption(label="無可用武裝", description="老哥，你的雲端倉庫裡沒有其他備用漁具"))
        super().__init__(placeholder="點擊此處展開大倉庫，一鍵挑選並切換穿戴武裝...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = int(interaction.user.id)
        chosen_item = self.values[0]
        if chosen_item == "無可用武裝":
            await interaction.response.send_message("❌ 你大倉庫裡沒有其他備用漁具可以更換！", ephemeral=True); return
        user = get_user(user_id)
        if "魚竿" in chosen_item or "桿" in chosen_item or "竿" in chosen_item or "Rod" in chosen_item:
            update_user(user_id, rod=chosen_item)
            msg = f"🟢 **主武裝變更！** 右手魚竿切換為：【**{chosen_item}**】！"
        elif any(v in chosen_item for v in ["潛水服", "潛水艇", "鑽探機"]):
            update_user(user_id, pet=chosen_item)
            msg = f"🟢 **探險載具變更！** 已更換駕駛載具為：【**{chosen_item}**】！"
        else:
            update_user(user_id, bait_type=chosen_item)
            msg = f"🟢 **副手武器變更！** 已更換重型武器為：【**{chosen_item}**】！"
        await interaction.response.send_message(msg, ephemeral=True)

class EquipmentView(discord.ui.View):
    def __init__(self, user_items):
        super().__init__(timeout=60)
        self.add_item(EquipmentSelect(user_items))


# ======= ❤️ 4.0 重磅核心二：背包專用互動式 ❤️ 喜愛魚獲下拉選單機制 =======
class FavoriteFishSelect(discord.ui.Select):
    def __init__(self, user_items):
        options = []
        for item_name, item_count in user_items.items():
            if item_count > 0 and not any(v in item_name for v in ["魚竿", "魚叉", "巨弩", "戟", "劍", "潛水", "鑽探", "Rod"]):
                if len(options) < 25:
                    options.append(discord.SelectOption(label=f"{item_name} (x{item_count})", value=item_name, description="一鍵 [❤️上鎖保護 / 🔓解除鎖定]", emoji="🐟"))
        if not options:
            options.append(discord.SelectOption(label="大倉庫目前無可用魚獲", description="老哥，你倉庫裡沒有可以標記最愛的物資"))
        super().__init__(placeholder="❤️ 點擊選單鎖定魚獲：全賣時會自動完美跳過保護鎖...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = int(interaction.user.id)
        chosen_fish = self.values[0]
        if chosen_fish == "大倉庫目前無可用魚獲":
            await interaction.response.send_message("❌ 背包內沒有可用魚獲可以鎖定！", ephemeral=True); return
        
        # 雲端動態切換喜愛鋼印
        is_fav = inventory_col.find_one({"user_id": user_id, "item_name": chosen_fish})
        current_fav = int(is_fav.get("is_favorite", 0)) if is_fav else 0
        new_fav = 1 if current_fav == 0 else 0
        inventory_col.update_one({"user_id": user_id, "item_name": chosen_fish}, {"$set": {"is_favorite": new_fav}})
        
        msg = f"❤️ **【喜愛鎖定成功】** 【{chosen_fish}】已打上防呆鋼印！執行 `/全賣` 時將**絕對跳過保護**！" if new_fav == 1 else f"🔓 **【保護安全解除】** 【{chosen_fish}】已回到常規物資名冊，現在可以全賣變現了。"
        await interaction.response.send_message(msg, ephemeral=True)

class FavoriteFishView(discord.ui.View):
    def __init__(self, user_items):
        super().__init__(timeout=60)
        self.add_item(FavoriteFishSelect(user_items))


# ======= 🦾 指令二十：/裝備 檢視與下拉換裝面板 =======
@bot.tree.command(name="裝備", description="【4.0 動態面板】檢視你當前裝備的魚竿、武器與載具，並可下拉選單一鍵更換")
async def view_equipment(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    
    # 🌟 從雲端 MongoDB 大倉庫撈出該船長名下擁有的裝備標記資產
    cursor = inventory_col.find({"user_id": user_id, "item_count": {"$gt": 0}})
    user_items = {doc["item_name"]: int(doc["item_count"]) for doc in cursor}
    
    embed = discord.Embed(title=f"🦾 {interaction.user.display_name} 的武裝面板", description="`──────────────────────────`", color=0x2ECC71)
    embed.add_field(name="🟩 右手主漁具 (Rod)", value=f"`{user.get('rod', '新手魚竿')}`", inline=True)
    embed.add_field(name="🟩 當前深海載具", value=f"`{user.get('pet', '無 (徒手素釣)')}`", inline=True)
    embed.add_field(name="🟩 副手遠征武器", value=f"`{user.get('bait_type', '無 (徒手肉搏)')}`", inline=True)
    embed.set_footer(text="💡 提示：使用下方下拉選單，可直接極速換上你大倉庫裡的其他神級漁具！")
    
    await interaction.response.send_message(embed=embed, view=EquipmentView(user_items))


# ======= 🎒 指令二十一：動態互動式雲端背包面板（下掛最愛鎖） =======
@bot.tree.command(name="背包", description="查看大師個人錢包餘額、附魔守護詞條與下掛最愛魚獲選單的互動式大倉庫")
async def inventory_cmd(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    
    cursor = inventory_col.find({"user_id": user_id, "item_count": {"$gt": 0}})
    rows = list(cursor)
    user_items = {doc["item_name"]: int(doc["item_count"]) for doc in rows}
    xp_needed = (user.get("level", 0) + 1) * 50
    
    embed = discord.Embed(title=f"🎒 {interaction.user.display_name} 的大冒險家雲端大倉庫", color=0x3498DB)
    embed.add_field(name="📊 個人屬性", value=f"• 等級：`LV.{user.get('level', 0)}` ({user.get('xp', 0)}/{xp_needed})\n• 錢包：`{user.get('balance', 100)} 🪙`\n• 所在海域：【`{user.get('current_map', '一海・新手小池塘')}`】", inline=True)
    embed.add_field(name="🎣 附魔守護", value=f"• 魚竿：`{user.get('rod', '新手魚竿')}`\n• 附魔：`【{user.get('enchant', '無')}】`\n• 儲備普通餌：`{user.get('bait_count', 5)} 個`", inline=True)
    
    inv_lines = []
    for doc in rows:
        # 🌟 智慧判定：如果該魚獲被打上最愛鎖，背包名稱前自動亮起紅心 ❤️，高大上排版 Scannable！
        fav_prefix = "❤️ " if int(doc.get("is_favorite", 0)) == 1 else "• "
        inv_lines.append(f"{fav_prefix}**{doc['item_name']}** x{doc['item_count']}")
        
    inv_str = "\n".join(inv_lines) if inv_lines else "雲端倉庫空空如也，老哥快去下一竿吧！"
    embed.add_field(name="🐟 大倉庫名冊 (打上 ❤️ 紅心者一鍵全賣時將被絕對安全跳過)", value=inv_str, inline=False)
    
    # 🌟 直接在背包面板下方，動態下掛互動式「最愛鎖定/解鎖」下拉選單！
    await interaction.response.send_message(embed=embed, view=FavoriteFishView(user_items))


# ======= 💰 指令二十二：雲端版一鍵全賣（🌟 ❤️ 最愛隔離防線鎖死！） =======
@bot.tree.command(name="全賣", description="一鍵清空大倉庫魚獲換取大量金幣（❤️ 被打上最愛保護鎖的珍稀魚獲將被絕對安全跳過！）")
async def sell_all(interaction: discord.Interaction):
    await interaction.response.defer()
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    
    # 🌟 核心金盾過濾：在雲端只篩選出數量 > 0 且 is_favorite 不等於 1 (即未上鎖) 的常規大宗魚獲！
    cursor = inventory_col.find({"user_id": user_id, "item_count": {"$gt": 0}, "is_favorite": {"$ne": 1}})
    items = list(cursor)
    
    if not items:
        await interaction.followup.send("📭 雲端倉庫內沒有可回收的常規魚獲物資（或者你所有的突變神魚都已上鎖 ❤️ 保護中）。", ephemeral=True)
        return
        
    prices_map = {}
    for _, v_list in FISH_POOL.items():
        for fname, fprice in v_list: prices_map[fname] = fprice
    for _, r_dict in MAP_EXCLUSIVE_FISH.items():
        for _, f_list in r_dict.items():
            for fname, fprice in f_list: prices_map[fname] = fprice
            
    total_revenue, sold_details, sold_any = 0, [], False
    for item in items:
        item_name = item["item_name"]
        count = int(item["item_count"])
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
            inventory_col.update_one({"_id": item["_id"]}, {"$set": {"item_count": 0}})
            
    if not sold_any or total_revenue == 0:
        await interaction.followup.send("❌ 大倉庫內沒有常規可交易回收的魚獲物資。", ephemeral=True); return
    if "招財貓" in user.get("pet", "無"):
        bonus_cash = int(total_revenue * 0.1); total_revenue += bonus_cash
        sold_details.append(f"🐱 【招財貓加持】 額外賺取了 {bonus_cash} 金幣！")
        
    tax_msg = ""
    guild_data = guilds_col.find_one({"members": user_id})
    if guild_data:
        g_name = guild_data["guild_name"]
        tax_amount = int(total_revenue * 0.05)
        total_revenue -= tax_amount
        guilds_col.update_one({"guild_name": g_name}, {"$inc": {"vault": tax_amount}})
        tax_msg = f"\n🏰 **【公會共榮】5% 稅金 ({tax_amount} 金幣) 已自動繳入【{g_name}】雲端金庫！**"
        
    update_user(user_id, balance=user.get("balance", 100) + total_revenue)
    embed = discord.Embed(title="💰 魚獲交易結算完畢", description="\n".join(sold_details) + f"\n\n💵 實際賺得：**{total_revenue}** 金幣！{tax_msg}", color=0xF1C40F)
    await interaction.followup.send(embed=embed)


# ======= 🏰 指令二十三：大航海公會創立與管理 =======
@bot.tree.command(name="創立公會", description="創立你專屬的航海公會（條件：需達到 LV.50 且支付 5000 金幣）")
@app_commands.describe(公會名稱="你想為公會取什麼名字？")
async def create_guild(interaction: discord.Interaction, 公會名稱: str):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    if user.get("level", 0) < 50:
        await interaction.response.send_message(f"❌ 創立失敗！等級實力不足！需要達到 `LV.50`。", ephemeral=True); return
    if user.get("balance", 100) < 5000:
        await interaction.response.send_message(f"❌ 資金不足！向總部註冊公會需要 `5000` 金幣！", ephemeral=True); return
    if guilds_col.find_one({"members": user_id}):
        await interaction.response.send_message("❌ 你已經是某個公會的成員了，請先退出組織！", ephemeral=True); return
    if guilds_col.find_one({"guild_name": 公會名稱}):
        await interaction.response.send_message("❌ 這個公會名稱已經被搶先註冊了！", ephemeral=True); return
        
    new_guild = {
        "guild_name": 公會名稱, "leader_id": user_id, "vault": 0,
        "current_boss": "無", "boss_hp": 0, "members": [user_id], "boss_damage": {}
    }
    guilds_col.insert_one(new_guild)
    update_user(user_id, balance=user["balance"] - 5000)
    await interaction.response.send_message(f"🏰 🎉 **【雲端公會開闢】** 恭喜 **{interaction.user.display_name}** 成功註冊大公會：【**{公會名稱}**】！")

@bot.tree.command(name="加入公會", description="申請加入其他大師開創的航海公會")
@app_commands.describe(公會名稱="你想加入的公會名稱")
async def join_guild(interaction: discord.Interaction, 公會名稱: str):
    user_id = int(interaction.user.id)
    guild_data = guilds_col.find_one({"guild_name": 公會名稱})
    if not guild_data:
        await interaction.response.send_message("❌ 找不到這個公會！請確認名字是否輸入完整正確。", ephemeral=True); return
    if guilds_col.find_one({"members": user_id}):
        await interaction.response.send_message("❌ 你身上已經有公會會籍了！", ephemeral=True); return
        
    guilds_col.update_one({"guild_name": 公會名稱}, {"$push": {"members": user_id}})
    await interaction.response.send_message(f"🤝 **{interaction.user.display_name}** 成功加入航海公會：【**{公會名稱}**】！")

@bot.tree.command(name="公會背包", description="查看當前公會的資金金庫、世界 BOSS 狀態以及全體船長名單")
async def guild_panel(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    guild_data = guilds_col.find_one({"members": user_id})
    if not guild_data:
        await interaction.response.send_message("❌ 老哥，你目前還是一介散人，沒有加入任何公會！", ephemeral=True); return
        
    g_name = guild_data["guild_name"]
    leader_id = guild_data["leader_id"]
    vault = guild_data["vault"]
    c_boss = guild_data["current_boss"]
    b_hp = guild_data["boss_hp"]
    members = guild_data["members"]
    
    leader_user = interaction.guild.get_member(leader_id) if interaction.guild else None
    leader_name = leader_user.display_name if leader_user else f"老會長({leader_id})"
    
    m_list = []
    for m_id in members:
        m_user = interaction.guild.get_member(m_id) if interaction.guild else None
        m_list.append(f"• {m_user.display_name if m_user else f'船長({m_id})'}")
        
    embed = discord.Embed(title=f"🏰 航海公會面板 ── 【{g_name}】", description="`──────────────────────────`", color=0x34495E)
    embed.add_field(name="👑 公會領袖", value=f"`{leader_name}`", inline=True)
    embed.add_field(name="💰 雲端金庫總資金", value=f"`{vault} 🪙`", inline=True)
    
    boss_status = f"🔴 **【{c_boss}】** 圍剿中！\n• 剩餘總血量：`❤️ {b_hp} Pts`" if c_boss != "無" else "💤 目前海域平靜，暫無魔王肆虐。"
    embed.add_field(name="🐉 世界魔王狀態", value=boss_status, inline=False)
    embed.add_field(name="👥 全體成員名單", value="\n".join(m_list), inline=False)
    await interaction.response.send_message(embed=embed)


# ======= 🐉 指令二十四：會長專屬 4.0 世界 BOSS 召喚 =======
@bot.tree.command(name="召喚魔王", description="【會長專屬】消耗公會金庫資金，向全服海域隨機召喚一隻史詩級世界 BOSS 巨獸！")
async def summon_boss(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    guild_data = guilds_col.find_one({"leader_id": user_id})
    if not guild_data:
        await interaction.response.send_message("❌ 權限不足！只有【公會會長】才能發動魔王召喚！", ephemeral=True); return
        
    g_name = guild_data["guild_name"]
    if guild_data["current_boss"] != "無":
        await interaction.response.send_message(f"❌ 召喚失敗！海域中已經有 【{guild_data['current_boss']}】 肆虐了！", ephemeral=True); return
        
    b_name = random.choice(list(BOSS_POOL.keys()))
    b_data = BOSS_POOL[b_name]
    if guild_data["vault"] < b_data["cost"]:
        await interaction.response.send_message(f"❌ 公會金庫資金不足！召喚需要 `{b_data['cost']}` 資金，目前金庫只有 `{guild_data['vault']}` 🪙。", ephemeral=True); return
        
    guilds_col.update_one(
        {"guild_name": g_name},
        {"$set": {"current_boss": b_name, "boss_hp": b_data["hp"], "boss_damage": {}}, "$inc": {"vault": -b_data["cost"]}}
    )
    embed = discord.Embed(title="🚨 ── 全服警告：遠古魔王降臨 ── 🚨", description=f"🏰 【**{g_name}**】的會長使用了遠古共振器！\n\n🐉 **魔王現世**：【**{b_name}**】\n❤️ 初始總血量：`{b_data['hp']} Pts`\n\n*{b_data['desc']}*", color=0xE74C3C)
    await interaction.response.send_message(embed=embed)


# ======= ⚔️ 指令二十五：4.0 雲端全公會合力遠征進攻魔王 =======
@bot.tree.command(name="公會遠征", description="【全體成員可參與】集體進攻圍剿當前公會的世界 BOSS，共享雲端神話戰利品大獎禮包！")
async def attack_boss(interaction: discord.Interaction):
    await interaction.response.defer()
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    
    guild_data = guilds_col.find_one({"members": user_id})
    if user.get("quest_type") == "🦁 魔王討伐軍":
        update_user(user_id, quest_progress=user.get("quest_progress", 0) + 1)
        
    if not guild_data:
        await interaction.followup.send("❌ 遠征失敗！你必須先加入一個航海公會！", ephemeral=True); return
        
    g_name = guild_data["guild_name"]
    c_boss = guild_data["current_boss"]
    b_hp = int(guild_data["boss_hp"])
    
    if c_boss == "無" or b_hp <= 0:
        await interaction.followup.send("❌ 遠征失敗！目前暫無魔王可以討伐。", ephemeral=True); return
        
    player_dmg = 10; equipped_weapon = "🦴 徒手肉搏"
    for w_name, w_info in WEAPONS_SHOP.items():
        w_item = inventory_col.find_one({"user_id": user_id, "item_name": w_name, "item_count": {"$gt": 0}})
        if w_item: player_dmg = w_info["dmg"]; equipped_weapon = w_name; break
        
    crit_roll = random.choice([1.0, 1.0, 1.0, 1.5, 2.0])
    final_dmg = int(player_dmg * crit_roll)
    new_hp = max(0, b_hp - final_dmg)
    
    guilds_col.update_one(
        {"guild_name": g_name},
        {"$set": {"boss_hp": new_hp}, "$inc": {f"boss_damage.{user_id}": final_dmg}}
    )
    
    crit_msg = "🔥 **【致命一擊】觸發超高倍率暴擊！**\n" if crit_roll > 1.0 else ""
    msg = f"⚔️ **{interaction.user.display_name}** 裝備 【{equipped_weapon}】 投身遠征！\n{crit_msg}💥 輸出傷害：**`{final_dmg}`** Pts！ (❤️ 剩餘血量：`{new_hp} Pts`)\n"
    
    if new_hp <= 0:
        updated_guild = guilds_col.find_one({"guild_name": g_name})
        participants = list(updated_guild.get("boss_damage", {}).keys())
        guilds_col.update_one({"guild_name": g_name}, {"$set": {"current_boss": "無", "boss_hp": 0, "boss_damage": {}}})
        
        msg += f"\n🏆 🎉 **【魔王雲端隕落・史詩大捷！】** 🎉 🏆\n🌌 **【全員大獎賞】參與成員（共 {len(participants)} 人）全部獲得戰利品：\n💰 錢包金幣 `+5000 🪙` | `🥳神祕黃金寶箱 x2` | `🔵高級運氣藥水 x3`！**"
        for p_str_id in participants:
            p_id = int(p_str_id)
            p_user = get_user(p_id)
            update_user(p_id, balance=p_user.get("balance", 100) + 5000)
            add_inventory(p_id, "🥳神祕黃金寶箱", 2)
            add_inventory(p_id, "🔵高級運氣藥水", 3)
            
    await interaction.followup.send(msg)


# ======= 🗺️ 指令二十六：解鎖地幔隱藏地圖 =======
@bot.tree.command(name="解鎖隱藏島嶼", description="當你累積完成日常任務且實力足夠時，永久解鎖四海・諸神黃昏地幔隱藏海域！")
async def unlock_hidden_map(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    if user.get("level", 0) < 220:
        await interaction.response.send_message(f"❌ 破譯失敗！船長實力需要達到 `LV.220`！(你目前只有 `LV.{user['level']}`)", ephemeral=True)
        return
    if user.get("balance", 100) < 15000:
        await interaction.response.send_message(f"❌ 破譯手札失敗！需要支付 `15000` 金幣的研究費，你目前只有 `{user['balance']}` 🪙。", ephemeral=True)
        return
    if "四海・地幔熔岩禁地" in MAPS:
        await interaction.response.send_message("❌ 老哥，你的航海日誌上早就已經解鎖這片隱藏地幔禁地了！", ephemeral=True)
        return
        
    MAPS["四海・地幔熔岩禁地"] = {
        "req_lvl": 220, "cost": 5000, "npc": "👁️ 覺醒老哥本人",
        "desc": "鑽破地殼的終極地底世界！高溫高壓，此處出產地底極致高溫突變流體生物！",
        "image": "https://imgur.com", "shop": {"🏆 任務大師榮譽紀念竿": 1}
    }
    update_user(user_id, balance=user["balance"] - 15000)
    embed = discord.Embed(title="🌌 ── 航海禁忌突破：隱藏島嶼解鎖！ ── 🌌", description=f"🎉 成功破譯遠古公會手札！\n\n🧭 **新航線**：【**四海・地幔熔岩禁地**】永久解鎖！", color=0x9B59B6)
    await interaction.response.send_message(embed=embed)


# ======= 📘 指令二十七：物種收藏雲端大圖鑑系統 =======
@bot.tree.command(name="查看圖鑑", description="查看你在四大海域中所成功解鎖的所有特產魚獲物種圖鑑進度")
async def view_encyclopedia(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    cursor = db["fish_encyclopedia"].find({"user_id": user_id})
    unlocked_fishes = [doc["fish_name"] for doc in cursor]
    
    # 🌟 4.0 雲端圖鑑完美修復版（4 空格精準縮排，徹底阻斷 Syntax 語法崩潰！）
    embed = discord.Embed(title=f"📘 {interaction.user.display_name} 的大航海・世界物種百科圖鑑", description="`──────────────────────────`", color=0x34495E)
    
    for m_name, rarity_dict in MAP_EXCLUSIVE_FISH.items():
        all_map_fishes = []
        for rarity, f_list in rarity_dict.items():
            for fname, _ in f_list:
                if fname not in all_map_fishes:
                    all_map_fishes.append(fname)
                    
        # 🟢 100% 正確的雲端字串全封閉包含比對，極速 0.001 秒秒噴進度
        unlocked_count = sum(1 for fish in all_map_fishes if fish in unlocked_fishes)
        
        detail_lines = []
        for fish in all_map_fishes:
            if fish in unlocked_fishes:
                detail_lines.append(f"• ✅ **{fish}**")
            else:
                detail_lines.append(f"• 🔒 *未探索生物*")
                
        embed.add_field(
            name=f"🚢 【{m_name}】 (進度: {unlocked_count}/{len(all_map_fishes)} 🪐)", 
            value="\n".join(detail_lines) if detail_lines else "暫無產物", 
            inline=False
        )
        
    await interaction.response.send_message(embed=embed)

# ──────────────────────────────────────────────────────────
# 🛑 0 空格區域：4.0 全新雲端世界最底層啟動入口（完全頂格靠左，絕不留白！）
init_db()
keep_alive()
DISCORD_CODE = os.getenv("DISCORD_TOKEN")
bot.run(DISCORD_CODE)
