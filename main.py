# ======= 🪐 組一：核心環境依賴與雲端 MongoDB Atlas 連線防線（第 1 ~ 95 行） =======
from dotenv import load_dotenv
load_dotenv()  # 自動打開環境變數檔案讀取 Token
import os
import time
import random
import asyncio
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient, ReturnDocument

# 🌐 Flask 網頁製造機（保持 24h 不休息，防止 Render 免費版睡眠）
app = Flask('')

@app.route('/')
def home():
    return "歡樂釣魚場 5.5.5 諸神黃昏雲端連線中心已全線大開綠燈！"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 1. Discord 機器人基礎意圖設定 (Intents)
intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        try:
            await self.tree.sync()
            print("連線成功：歡樂釣魚場 5.5.5 雲端斜線指令已完全實時同步！")
        except Exception as e:
            print(f"指令同步提示: {e}")

bot = MyBot()

# 🌟 官方支援群 ID 設定（已完美對齊老哥的 Discord 伺服器！）
SUPPORT_GUILD_ID = 1546517053719060642

# ======= 🍀 MongoDB 雲端保險箱架構 =======
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("🚨 警告：Render 後台未偵測到 MONGO_URI 環境變數！將自動建立本地虛擬 Fallback 連線。")
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
else:
    client = MongoClient(MONGO_URI)

# 選定資料庫與四大雲端數據集合（徹底砸碎舊 SQLite 殘留）
db = client["fishing_game_555"]
users_col = db["users"]
inventory_col = db["inventory"]
guilds_col = db["guilds"]
settings_col = db["guild_settings"]

def init_db():
    try:
        # 測試雲端握手
        client.admin.command('ping')
        print("🟢 諸神黃昏防線：歡樂釣魚場與 MongoDB Atlas 雲端資料庫 24h 永久連線成功！玩家存檔已鎖死！")
    except Exception as e:
        print(f"🚨 雲端連線提示: {e}")
# ======= 📊 組二：JSON 文件型資料庫安全讀寫工具組（第 96 ~ 185 行） =======
def get_user(user_id):
    user_id = int(user_id)
    user = users_col.find_one({"user_id": user_id})
    if not user:
        # 船新玩家初始化一整包精美的 5.5 歷史物件結構
        default_user = {
            "user_id": user_id, "name": f"船長({user_id})", "balance": 100, "rod": "新手魚竿", "bait_count": 5,
            "level": 0, "xp": 0, "current_map": "一海・新手小池塘", "pet": "無 (徒手素釣)",
            "last_daily": "2000-01-01", "daily_streak": 0, "enchant": "無", "bait_type": "無 (徒手肉搏)",
            "quest_type": "無", "quest_target": 0, "quest_progress": 0, "quest_reward": 0,
            "afk_save_hours": 1, "last_active_time": time.time(),
            "tutorial_completed": False, "tutorial_step": 0,
            "race_type": "👤 常規人類", "race_version": 1, "world_boss_damage": 0  # 🌟 新架構欄位
        }
        users_col.insert_one(default_user)
        return default_user
        
    # 🛠️ 雲端自動熱修補機制：老玩家如果缺 5.5 的新欄位，在讀取的 0.01 秒內自動在雲端補齊預設值！
    updates = {}
    defaults = {
        "name": f"船長({user_id})", "balance": 100, "rod": "新手魚竿", "bait_count": 5, "level": 0, "xp": 0,
        "current_map": "一海・新手小池塘", "pet": "無 (徒手素釣)", "last_daily": "2000-01-01", "daily_streak": 0,
        "enchant": "無", "bait_type": "無 (徒手肉搏)", "quest_type": "無", "quest_target": 0,
        "quest_progress": 0, "quest_reward": 0, "afk_save_hours": 1, "last_active_time": time.time(),
        "tutorial_completed": True, "tutorial_step": 0, "race_type": "👤 常規人類", "race_version": 1, "world_boss_damage": 0
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
    # 雲端一鍵更新欄位，最頂級型態安全
    users_col.update_one({"user_id": user_id}, {"$set": kwargs}, upsert=True)

def add_inventory(user_id, item_name, amount=1):
    user_id = int(user_id)
    amount = int(amount)
    inventory_col.update_one(
        {"user_id": user_id, "item_name": item_name},
        {"$inc": {"item_count": amount}}, 
        upsert=True
    )
    inventory_col.update_one(
        {"user_id": user_id, "item_name": item_name, "is_favorite": {"$exists": False}},
        {"$set": {"is_favorite": 0}}
    )
# ======= 🏪 組三：全球普通商店物資庫與 10 大極端天氣池定義（第 186 ~ 275 行） =======
BAITS_SHOP = {
    # 🐛 Fisch 風格硬核消耗魚餌
    "普通魚餌": 15, "稀有魚餌 (x1)": 45, "神話魚餌 (x1)": 150, "傳說魚餌 (x1)": 350, 
    "海藻餌": 25, "磁鐵重餌": 45, "🔋 彈性奈米反覆餌": 4999,
    
    # 🧪 截圖全套 11 款珍稀魔法藥水
    "幸運藥水1級 (x3)": 100, "幸運藥水2級 (x10)": 400, "幸運藥水3級 (x2)": 600, 
    "超級幸運藥水 (x2)": 800, "天體幸運藥水 (x2)": 1500, "彩虹藥水 (x1)": 2000, 
    "泰坦藥水 (x3)": 1200, "變異藥水 (x2)": 500, "閃亮藥水 (x4)": 450, 
    "雙倍活動幣藥水 (x1)": 700, "黃金藥水 (x2)": 650, "⚡閃電速度藥水": 250, "💗性慾藥水": 150,
    
    # 🧰 藥水與盲盒寶箱
    "🎁 基礎藥水寶箱": 250, "🎁 稀原藥水寶箱": 600, "🎁 傳奇藥水寶箱": 1500,
    "寵物禮包小 (x2)": 300, "寵物禮包大 (x76)": 2500, "夏日水餃禮包 (x7)": 500,
    "🥳神祕黃金寶箱": 500, "🌌轉生神仙水": 99999,
    
    # 🪝 消耗性功能型高階浮標
    "🟢 綠光電子浮標": 150, "🔵 藍海震盪浮標": 500, "🔴 狂暴重力浮標": 1200
}

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
# ======= 🎣 組四：四大地理隔離海域與 15 大被動技能神竿圖鑑（第 276 ~ 370 行） =======
MAPS = {
    "一海・新手小池塘": {"req_lvl": 0, "cost": 0, "npc": "👴 隔壁張老頭", "desc": "新手起步的溫馨池塘，平靜安全。", "image": "https://imgur.com", "shop": {"初級魚竿": 200, "高級魚竿": 1000, "穩健之竿 (Steady Rod)": 1500, "長線之竿 (Long Rod)": 2200}},
    "二海・黃金珊瑚礁": {"req_lvl": 80, "cost": 500, "npc": "🦈 魚人阿龍", "desc": "高壓的水下珊瑚礁世界，魚獲斑斕色彩。", "image": "https://imgur.com", "shop": {"深海魚竿": 3500, "珊瑚礁共振竿": 6000, "霓虹之竿 (Neon Rod)": 7500, "黃金之竿 (Golden Rod)": 12000, "幸運之竿 (Lucky Rod)": 18000}},
    "三海_馬里亞娜海溝深淵": {"req_lvl": 160, "cost": 2500, "npc": "🔱 大祭司波賽頓", "desc": "漆黑萬丈的馬里亞娜海溝底部，充斥未知巨獸與零件。", "image": "https://imgur.com", "shop": {"量子魚竿": 8000, "暗夜之竿 (Nocturnal Rod)": 15000, "外星干擾重型桿": 25000, "ADMIN魚桿": 500000}}
}

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
# ======= 🔮 組五：遠古附魔特效、與 100% 補齊四大隔離海域特產魚池（第 371 ~ 485 行） =======
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
        "作者級": [("💻 作者的未編譯源代碼", 100000), ("🤨神秘的SIGMAFACE", 3000030)]
    },
    "四海・地幔熔岩禁地": {
        "傳奇": [("🌋 熔岩火靈魚", 3500)],
        "神話": [("🔥 煉獄不死鳥之眼", 12000), ("💎 熔岩核心巨鑽", 25000), ("👑 萬物主宰聖石 (Overlord Stone)", 66666)],
        "秘密": [("🌋 古星核熱熔高壓液體", 55000)],
        "作者級": [("🌌 SIGMA的熔岩超燃雪茄", 3333333)]
    }
}
# ======= 🎫 組六：製作者特殊公告 CODE 破譯、與全服動態幫助手冊 =======
@bot.tree.command(name="兌換碼", description="輸入官方禮包碼兌換物資，製作者輸入超難加密 CODE 可發動全服智慧公告廣播功能")
@app_commands.describe(code="請輸入你要兌換的代碼")
async def redeem_code(interaction: discord.Interaction, code: str):
    user_id = int(interaction.user.id)
    
    # 📢 1. 製作者極致難度特殊公告密鑰判定
    if code.startswith("GODFREY_ADMIN_MATRIX_CODE_2026_BY_SIGMA::"):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ 權限不足！此特殊神級密鑰只有製作者兼最高管理員才能破譯！", ephemeral=True)
            return
            
        announcement_content = code.replace("GODFREY_ADMIN_MATRIX_CODE_2026_BY_SIGMA::", "")
        await interaction.response.send_message("🚀 密鑰破譯成功！正在啟動跨服智慧頻道過濾，準備發動大廣播...", ephemeral=True)
        
        embed = discord.Embed(title="📢 ── 歡樂釣魚場・官方製作者廣播公告 ── 📢", description=f"\n{announcement_content}\n", color=0x9B59B6)
        embed.set_footer(text=f"⚙️ 雲端總控制台發布 • 管理員: {interaction.user.display_name}")
        
        # 🌍 跨服智慧過濾與公告頻道精準導流
        for guild in bot.guilds:
            target_channel = None
            current_setting = db["guild_settings"].find_one({"guild_id": int(guild.id)})
            if current_setting and "announcement_channel_id" in current_setting:
                configured_channel_id = int(current_setting["announcement_channel_id"])
                target_channel = guild.get_channel(configured_channel_id)
                
            if not target_channel:
                for channel in guild.text_channels:
                    c_name = channel.name.lower()
                    if any(keyword in c_name for keyword in ["聊天頻道", "chat", "general", "main", "聊天"]):
                        if channel.permissions_for(guild.me).send_messages:
                            target_channel = channel
                            break
                            
            if not target_channel:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        target_channel = channel
                        break
                        
            if target_channel:
                try: await target_channel.send(embed=embed)
                except: pass
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

# ======= 📋 指令：5.0 諸神黃昏黑曜石互動式幫助手冊 =======
@bot.tree.command(name="幫助", description="【5.0 核心手冊】詳細查詢歡樂釣魚場全服 15 大限購神竿、10 大天氣加成與公會天梯機制")
async def help_manual(interaction: discord.Interaction):
    embed = discord.Embed(title="🎣 歡樂釣魚場 5.5 ── 諸神黃昏全功能大百科", description="`──────────────────────────`", color=0x2ECC71)
    embed.add_field(name="🎮 1. 核心垂釣與裝備防呆", value="• `/釣魚` : 融入 10 大天氣與高階浮標單次消耗。最低冷卻防線 1.5 秒。\n• `/裝備` : 綠格子黑曜石面板，一鍵下拉選單秒切右手魚竿與副手武器。\n• `/背包` : 內建❤️下拉最愛防呆鎖的大倉庫。上鎖物資執行 `/全賣` 時 100% 絕對跳過保護！", inline=False)
    embed.add_field(name="🎰 2. 三選一星級懸賞與掛機", value="• `/刷新任務` : 每日(24h)可刷新 3 個 **1⭐~5⭐ 星級委託**，雲端留存 12 小時任選其一。\n• `/大賭局` : 投入 5000 金幣對對碰幸運號碼，豪賭稀有、傳奇藥水寶箱！\n• `💤 自動 AFK 掛機` : 10分鐘未使用指令自動開啟！幸運-300%背景自動盲釣，未升級魚獲留存1h！", inline=False)
    embed.add_field(name="🏰 3. 公會共榮與世界 BOSS 團戰", value="• `/創立公會` : 需達 LV.50 並支付 5000 金幣。\n• `/全賣` : 自動將收益之 5% 抽稅上繳公會雲端金庫，並**實時折算公會總天梯積分**！\n• `/公會排行榜` : 查看全服打海獸、釣魚、衝懸賞累加出來的**最強公會天梯榜**！", inline=False)
    embed.set_footer(text="💡 提示：大倉庫資料廖已 24h 與 MongoDB 雲端保險箱鎖死，重啟伺服器絕對不回檔！")
    await interaction.response.send_message(embed=embed)
# ======= 📢 組七：管理員自訂公告區、與實體按鈕控制台綁定 =======
class AnnounceSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # 永不逾時

    @discord.ui.button(label="📢 一鍵綁定：將當前頻道設定為公告區", style=discord.ButtonStyle.green, custom_id="set_announce_channel_btn")
    async def set_channel_callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ 權限被攔截！老哥，此實體控制台按鈕只有【最高管理員】才能點擊配置！", ephemeral=True)
            return
            
        guild_id = int(interaction.guild_id) if interaction.guild_id else 0
        channel_id = int(interaction.channel_id) if interaction.channel_id else 0
        
        db["guild_settings"].update_one(
            {"guild_id": guild_id},
            {"$set": {
                "guild_name": interaction.guild.name if interaction.guild else "未知群組",
                "announcement_channel_id": channel_id,
                "configured_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }},
            upsert=True
        )
        await interaction.response.send_message(f"✅ **配置成功！** 已成功將 <#{channel_id}> 鎖定為官方製作者廣播的唯一指定綠燈通道！", ephemeral=True)

@bot.tree.command(name="公告配置", description="【群主/管理員專屬】呼叫出官方公告實體按鈕控制台，方便在任意頻道一鍵點擊鎖定")
async def show_announce_panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 權限不足！只有最高管理員才能呼叫此引導面板。", ephemeral=True); return
        
    guild_id = int(interaction.guild_id) if interaction.guild_id else 0
    current_setting = db["guild_settings"].find_one({"guild_id": guild_id})
    status_str = f"🔒 唯一指定通道：<#{current_setting['announcement_channel_id']}>" if current_setting else "⚠️ 目前尚未配置（目前走預設聊天頻道智慧導流）"
    
    embed = discord.Embed(title="⚙️ 航海大世紀 ── 官方廣播總主機配置面板", description="`──────────────────────────`", color=0x9B59B6)
    embed.add_field(name="📊 當前群組設定狀態", value=status_str, inline=False)
    embed.add_field(name="🛠️ 點擊下方綠色按鈕", value="將會把**目前你正在說話的這一個頻道**，直接與官方製作者（老哥）的全服大廣播進行物理對齊綁定！", inline=False)
    await interaction.response.send_message(embed=embed, view=AnnounceSetupView())
# ======= 📅 組八：連續簽到天數疊加、與 5.5.5 指數級暴增全服大賭局 =======
@bot.tree.command(name="簽到", description="【連續簽到加成】每日簽到領獎，連續天數越多，獲得的金幣與魚餌補給越豐厚！")
async def daily_cmd(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    if user.get("last_daily", "2000-01-01") == today_str:
        await interaction.response.send_message("❌ 老哥，你今天已經簽到隔天再來吧！", ephemeral=True); return
        
    last_daily_str = user.get("last_daily", "2000-01-01")
    current_streak = int(user.get("daily_streak", 0))
    
    try:
        last_date = datetime.strptime(last_daily_str, "%Y-%m-%d")
        today_date = datetime.strptime(today_str, "%Y-%m-%d")
        if today_date - last_date == timedelta(days=1): current_streak = min(current_streak + 1, 7)
        else: current_streak = 1
    except: current_streak = 1
        
    base_money = 200 + (current_streak - 1) * 50
    base_bait = 3 + (current_streak - 1) * 1
    
    update_user(user_id, balance=user.get("balance", 100) + base_money, bait_count=user.get("bait_count", 5) + base_bait, last_daily=today_str, daily_streak=current_streak, name=interaction.user.display_name)
    
    embed = discord.Embed(title="📅 ── 航海大世紀・雲端連續簽到 ── 📅", description=f"船長 **{interaction.user.display_name}** 今日報到成功！", color=0x3498DB)
    embed.add_field(name=f"🔥 當前連續簽到進度：`【 {current_streak} / 7 天 】`", value=f"• 獲得基礎金幣：`{base_money} 🪙`\n• 獲得儲備普通餌：`+{base_bait} 個`", inline=False)
    await interaction.response.send_message(embed=embed)

# ======= 🎰 組八・補完：每週大賭局計數器自動雲端重置防線（4 空格精準縮排） =======
def check_and_reset_gamble_week(user_id):
    user = get_user(user_id)
    now = datetime.now()
    
    # 讀取玩家上一次下注的年份與週數
    last_gamble_time_str = user.get("last_gamble_date", "2000-01-01")
    try:
        last_date = datetime.strptime(last_gamble_time_str, "%Y-%m-%d")
        # 如果今年或這週已經跟上一次不同，自動在雲端將本週賭局次數「重置歸零」！
        if now.isocalendar() != last_date.isocalendar() or now.year != last_date.year:
            users_col.update_one({"user_id": int(user_id)}, {"$set": {"weekly_gamble_count": 0, "last_gamble_date": now.strftime("%Y-%m-%d")}})
    except:
        users_col.update_one({"user_id": int(user_id)}, {"$set": {"weekly_gamble_count": 0, "last_gamble_date": now.strftime("%Y-%m-%d")}})

@bot.tree.command(name="大賭局", description="【5.5.5 指數博弈】本週賭局次數越高，賭資指數級暴增！但中大獎機率也會瘋狂暴增！")
async def crazy_gamble(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    check_and_reset_gamble_week(user_id) # 🟢 完美對齊 4 空格靠左，徹底除雷！
    
    # 🌟 1. 從雲端讀取或初始化本週玩家的下注次數 (每週重置欄位)
    gamble_count = int(user.get("weekly_gamble_count", 0)) + 1
    
    # 🌟 2. 核心公式：根據當前輪次，精準計算出需要花費的金幣（指數級通膨）
    if gamble_count == 1:
        cost = 0  # 第一輪完全免費
    elif gamble_count == 2:
        cost = 5000  # 第二輪收 5000 
    else:
        cost = 5000 * (3 ** (gamble_count - 2))  # 第三輪 15000, 第四輪 45000, 第五輪 135000...
        
    if user.get("balance", 100) < cost:
        await interaction.response.send_message(f"❌ 賭資不足！老哥，第 **{gamble_count}** 輪大賭局需要支付 `{cost}` 🪙 金幣，你目前只有 `{user.get('balance', 100)}`。", ephemeral=True)
        return
        
    # 扣除賭資並同步更新下注次數
    update_user(user_id, balance=user["balance"] - cost, weekly_gamble_count=gamble_count)
    
    # 🌟 3. 機率增加機制：每多下一輪，搖出三個相同數字的機率就會瘋狂往上拉
    # 免費輪中獎率 10%，第二輪 25%，之後每多一輪中獎率多加 20%，直到 95% 封頂
    if gamble_count == 1: win_chance = 10
    elif gamble_count == 2: win_chance = 25
    else: win_chance = min(25 + (gamble_count - 2) * 20, 95)
    
    # 進行純數字隨機落點大搖號
    roll = random.uniform(0, 100)
    embed = discord.Embed(title=f"🎰 ── 諸神黃昏・指數級星運大賭局 [第 {gamble_count} 輪] ── 🎰", color=0xF1C40F)
    
    if roll < win_chance:
        # 🎉 恭喜中大獎！根據輪次發放對應的大盲盒
        roll_1 = roll_2 = roll_3 = random.randint(1, 3)
        if gamble_count == 1:
            prize = random.choice(["🟢普通運氣藥水", "⚡閃電速度藥水", "💗性慾藥水"])
            add_inventory(user_id, prize, 1)
            embed.description = f"🎰 搖號結果 ➔ `[ {roll_1} ]` `[ {roll_2} ]` `[ {roll_3} ]` (中獎率: `{win_chance}%`)\n\n🎉 **免費輪連線成功！** 天降保底好運，你獲得了：【**{prize}**】 x1！"
        elif gamble_count == 2:
            add_inventory(user_id, "🎁 稀有藥水寶箱", 1)
            embed.description = f"🎰 搖號結果 ➔ `[ {roll_1} ]` `[ {roll_2} ]` `[ {roll_3} ]` (中獎率: `{win_chance}%`)\n\n🏆 **高級輪大暴擊！** 恭喜老哥，你成功抱走大獎：【**🎁 稀有藥水寶箱**】 x1！"
        else:
            add_inventory(user_id, "🎁 傳奇藥水寶箱", 1)
            embed.description = f"🎰 搖號結果 ➔ `[ {roll_1} ]` `[ {roll_2} ]` `[ {roll_3} ]` (中獎率: `{win_chance}%`)\n\n🌌 🔥 **【諸神領域・終極豹子連線！】** 🔥 🌌\n指數級機率大突破！老哥你成功抱走至高戰略盲盒：【**🎁 傳奇藥水寶箱**】 x1！"
    else:
        # 😢 槓龜了
        roll_1, roll_2, roll_3 = random.randint(1, 3), random.randint(1, 3), random.randint(1, 3)
        if roll_1 == roll_2 == roll_3: roll_3 = (roll_3 % 3) + 1  # 強制防呆錯位
        
        # 指數級賭局即使槓龜，也保底退還 20% 的安慰獎金
        pity_cash = int(cost * 0.2)
        update_user(user_id, balance=get_user(user_id)["balance"] + pity_cash)
        
        embed.description = f"🎰 搖號結果 ➔ `[ {roll_1} ]` `[ {roll_2} ]` `[ {roll_3} ]` (中獎率: `{win_chance}%`)\n\n😢 **槓龜了老哥！數字未能連線！**\n投入的金幣已被市場回收。總控制台啟動低保機制，保底退還 20% 安慰金 `+{pity_cash} 🪙`！"
        embed.set_footer(text=f"💡 老哥提示：下一輪 [第 {gamble_count+1} 輪] 的開獎機率將直接提高到 {min(win_chance+20, 95)}%！要再搏一把嗎？")
        
    await interaction.response.send_message(embed=embed)
# ======= 🎰 組九：5.5 隨機 3選1 星級任務刷新、與 12h 雲端留存鎖 =======
@bot.tree.command(name="刷新任務", description="【每日 24h 限制】依據權限機率在雲端生成 3 個隨機趣味日常星級懸賞，越高級星機率越低！")
async def refresh_daily_quests(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    
    # 🌟 5.5 全方位擴充：15 大日常任務庫
    quest_database = {
        1: [
            {"name": "🎣 基礎池塘清道夫 (1⭐)", "target": 5, "reward": 350, "crystal": 2},
            {"name": "👟 海域垃圾清除兵 (1⭐)", "target": 2, "reward": 300, "crystal": 2},
            {"name": "🛍️ 碼頭揮金如土商 (1⭐)", "target": 2, "reward": 250, "crystal": 1}
        ],
        2: [
            {"name": "🦀 珊瑚礁淺灘採集 (2⭐)", "target": 4, "reward": 600, "crystal": 5},
            {"name": "🐟 綠頭擬鯉圍捕令 (2⭐)", "target": 3, "reward": 550, "crystal": 4},
            {"name": "🧪 簽到小福星累積 (2⭐)", "target": 1, "reward": 400, "crystal": 3}
        ],
        3: [
            {"name": "⚙️ 廢棄外星遺跡回收 (3⭐)", "target": 3, "reward": 950, "crystal": 9},
            {"name": "🔮 遠古附魔台共振 (3⭐)", "target": 2, "reward": 850, "crystal": 8},
            {"name": "📦 補給箱快遞速遞 (3⭐)", "target": 1, "reward": 750, "crystal": 7}
        ],
        4: [
            {"name": "🦈 二海巨鯊深海獵殺 (4⭐)", "target": 2, "reward": 1500, "crystal": 15},
            {"name": "🧬 基因奇蹟驚天異變 (4⭐)", "target": 1, "reward": 1800, "crystal": 18},
            {"name": "🦁 公會遠征重裝討伐 (4⭐)", "target": 3, "reward": 1600, "crystal": 16}
        ],
        5: [
            {"name": "🌋 地幔核心熔岩碎裂 (5⭐)", "target": 2, "reward": 3500, "crystal": 30},
            {"name": "🌌 終極星空奇點共振 (5⭐)", "target": 1, "reward": 5000, "crystal": 45},
            {"name": "👑 捕獲珊瑚礁之王 (5⭐)", "target": 1, "reward": 4500, "crystal": 40}
        ]
    }
    
    chosen_3 = []
    random.seed(int(time.time() / 86400) + user_id)
    for _ in range(3):
        roll_star = random.uniform(0, 100)
        if roll_star < 40: star_level = 1
        elif roll_star < 65: star_level = 2
        elif roll_star < 83: star_level = 3
        elif roll_star < 95: star_level = 4
        else: star_level = 5
        selected_q = random.choice(quest_database[star_level]).copy()
        chosen_3.append(selected_q)
    random.seed()
    
    db["quest_temp_locks"].update_one(
        {"user_id": user_id},
        {"$set": {"quests": chosen_3, "generated_at": time.time()}},
        upsert=True
    )
    
    embed = discord.Embed(title="🎰 ── 航海公會・全服星級權重懸賞令 ── 🎰", description="此批懸賞已在雲端安全留存 12h，星級越高機率越低！請輸入 `/接取任務 序號` 鎖定其一！", color=0xF39C12)
    for idx, q in enumerate(chosen_3):
        embed.add_field(name=f"【序號 {idx+1}】 {q['name']}", value=f"• 需求次數：`{q['target']}` 次\n• 賞金金幣：`{q['reward']} 🪙`\n• 榮譽結晶：`🌟 {q['crystal']} 個遠古星願晶石`", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="接取任務", description="從雲端留存的 3 個不對等權重星級任務中，精準挑選其中一個鎖定開刷")
@app_commands.describe(序號="請輸入你想接取的任務序號（1、2 或 3）")
async def choose_quest_index(interaction: discord.Interaction, 序號: int):
    # 🌟 5.5.5 鐵壁語法修復：補齊當初漏字與陣列攔截，100% 綠燈秒過！
    if 序號 not in [1, 2, 3]:
            await interaction.response.send_message("❌ 序號錯誤！老哥，只能挑選 1、2 或 3 號日常懸賞！", ephemeral=True)
            return
        
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    
    if user.get("quest_type", "無") != "無":
        await interaction.response.send_message("❌ 你身上已經掛著任務進度了，請先 `/回報任務` 領賞！", ephemeral=True)
        return
        
    lock_data = db["quest_temp_locks"].find_one({"user_id": user_id})
    if not lock_data or time.time() - lock_data.get("generated_at", 0) > 43200:
        await interaction.response.send_message("❌ 留存逾時或名冊為空！這批任務在雲端已經超過 12h 蒸發了，請重新 `/刷新任務`！", ephemeral=True)
        return
        
    q = lock_data["quests"][序號 - 1]
    update_user(user_id, quest_type=q["name"], quest_target=q["target"], quest_progress=0, quest_reward=q["reward"], quest_reward_crystal=q["crystal"])
    await interaction.response.send_message(f"🎯 **懸賞鎖定！** 你已成功接取：【**{q['name']}**】！衝吧老哥！")

# ======= 💤 組十：10 分鐘未使用自動切入 AFK 掛機、及 1hr 雲端大倉庫覆蓋防爆 =======
def process_afk_fishing(user_id):
    user = get_user(user_id)
    now = time.time()
    last_active = user.get("last_active_time", now)
    
    if now - last_active >= 600:
        elapsed_seconds = now - last_active
        fish_caught = int(elapsed_seconds / 30)
        if fish_caught > 0:
            max_hours = int(user.get("afk_save_hours", 1))
            allowed_max_fish = max_hours * 120  
            final_fish_count = min(fish_caught, allowed_max_fish)
            
            afk_pool = [("🐟 吳郭魚", 1), ("🐠 小丑魚", 1), ("👟 舊鞋子", 1)]
            for _ in range(final_fish_count):
                chosen_f, _ = random.choice(afk_pool)
                add_inventory(user_id, f"[💤掛機殘留] {chosen_f}", 1)
                
            users_col.update_one({"user_id": user_id}, {"$set": {"last_active_time": now}})
            return final_fish_count
    return 0

@bot.tree.command(name="任務進度", description="查詢目前身上接取的日常星級任務進度")
async def check_quest_flow(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    update_user(user_id, last_active_time=time.time())  
    
    if user.get("quest_type", "無") == "無":
        await interaction.response.send_message("🔍 你目前身上空空如也！請先輸入 `/刷新任務` 吧！", ephemeral=True)
    else:
        status = "✅ 可回報" if user["quest_progress"] >= user["quest_target"] else "⏳ 進行中"
        await interaction.response.send_message(f"📋 **日常星級進度卡槽**：\n🎯 當前任務：【{user['quest_type']}】({status})\n• 目前數量：`{user['quest_progress']} / {user['quest_target']}`\n• 達成金幣：`{user['quest_reward']} 🪙`\n• 獲得星願石：`🌟 {user.get('quest_reward_crystal', 0)} 個遠古星願晶石`")
# ======= 🧬 組十一：5.5.5 魚竿 V1~V3 覺醒、遠古種族血脈加成工具組（第 916 ~ 1010 行） =======
def get_player_modifiers(user_id):
    user = get_user(user_id)
    
    # 🌟 1. 讀取遠古種族等級（人類、鯊魚、海妖最高到 V3，亞特蘭提斯神族最高可衝到 V4）
    race = user.get("race_type", "👤 常規人類")
    race_v = int(user.get("race_version", 1))
    
    race_luck = 0.0
    race_money = 0.0
    
    if "鯊魚" in race:
        race_luck = 0.15 * race_v; race_money = 0.10 * race_v
    elif "海妖" in race:
        race_luck = 0.25 * race_v; race_money = 0.15 * race_v
    elif "亞特蘭提斯" in race:
        race_luck = 0.35 * race_v; race_money = 0.25 * race_v # 🌟 V4 時可達運氣+140%, 金幣+100%
        
    # 🌟 2. 遍歷雲端裝備卡槽中所有的多重寵物加成（動態累加，完美復刻截圖屬性鏈）
    cursor = inventory_col.find({"user_id": int(user_id), "is_equipped_pet": 1})
    equipped_pets = list(cursor)
    
    pet_luck_bonus = 0.0
    pet_money_bonus = 0.0
    pet_ids_str = []
    
    for p in equipped_pets:
        p_name = p["item_name"]
        pet_ids_str.append(str(p.get("pet_uid", random.randint(50, 65))))
        if "招財貓" in p_name: pet_money_bonus += 0.15
        elif "獵鷹" in p_name: pet_luck_bonus += 0.20
        elif "小青龍" in p_name: pet_luck_bonus += 0.35; pet_money_bonus += 0.20
        
    final_luck = 1.0 + race_luck + pet_luck_bonus
    final_money = 1.0 + race_money + pet_money_bonus
    
    return {
        "luck_multiplier": final_luck,
        "money_multiplier": final_money,
        "pet_chain": ",".join(pet_ids_str) if pet_ids_str else "無裝備寵物",
        "race_display": f"{race} V{race_v}"
    }

# ======= 🔄 指令三十一：滿級船長跨世代重生轉生系統 =======
@bot.tree.command(name="轉生", description="【滿級極致突破】當前等級達到 LV.100 時可消耗所有金幣，換取 1 枚至高重復幣並覺醒高階種族！")
async def reset_for_rebirth(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    
    if user.get("level", 0) < 100:
        await interaction.response.send_message(f"❌ 轉生失敗！老哥，你的修為實力不足，需要達到 `LV.100` 滿級大關才能突破！（你目前：`LV.{user.get('level', 0)}`）", ephemeral=True)
        return
        
    # 搖號覺醒全新遠古種族（有 15% 機率直接暴擊覺醒最高階的亞特蘭提斯神族！）
    race_roll = random.random()
    if race_roll < 0.15: new_race = "🔱 亞特蘭提斯神族"
    elif race_roll < 0.50: new_race = "🦈 鯊魚血脈族"
    else: new_race = "撕裂者海妖族"
    
    # 累加重生幣，並將等級金幣一鍵回歸起航點，保存時數永久增強
    current_resets = int(user.get("reset_coins", 0)) + 1
    
    update_user(
        user_id,
        level=0, xp=0, balance=100,
        reset_coins=current_resets,
        race_type=new_race,
        race_version=1,
        rod="新手魚竿",
        name=interaction.user.display_name
    )
    
    embed = discord.Embed(title="🔄 ── 諸神黃昏・靈魂涅槃轉生成功 ── 🔄", description=f"船長 **{interaction.user.display_name}** 破繭重生，跨入高階血脈紀元！", color=0x9B59B6)
    embed.add_field(name="✨ 轉生資產與血脈宣告", value=f"• 獲得至高重生幣：`{current_resets} 枚 🔄`\n• 覺醒遠古血脈：**{new_race} V1**\n• 錢包與漁具：重置回起航點，但你已獲得不可直視的被動複利！", inline=False)
    await interaction.response.send_message(embed=embed)
# ======= 🎣 組十二：4.0/5.5.5 核心完全體釣魚指令（前半段）（第 1011 ~ 1110 行） =======
cooldowns = {}

@bot.tree.command(name="釣魚", description="拋出釣竿！引進真實時間等待咬竿、種族加成與 10 大極端天氣共振異變！")
async def fish(interaction: discord.Interaction):
    # 🌟 1. 第一步 0.001 秒內完成預留應答，徹底封死未回應錯誤！
    await interaction.response.defer()
    import asyncio
    
    try:
        user_id = int(interaction.user.id)
        user = get_user(user_id)
        
        # 實時同步最新 Discord 使用者真實名字
        update_user(user_id, name=interaction.user.display_name, last_active_time=time.time())
        
        current_map = user.get("current_map", "一海・新手小池塘")
        current_rod = user.get("rod", "新手魚竿")
        current_enchant = user.get("enchant", "無")
        
        if not current_map or current_map == "None": current_map = "一海・新手小池塘"
        if not current_rod or current_rod == "None": current_rod = "新手魚竿"
        if not current_enchant or current_enchant == "None": current_enchant = "無"
        
        # 🌟 2. 獲取老哥截圖指定的：種族加成、多寵物加成、以及寵物裝備鏈數據
        mods = get_player_modifiers(user_id)
        race_luck_mod = float(mods["luck_multiplier"])
        pet_chain_display = mods["pet_chain"]
        
        weather_name, weather_info = get_global_weather()
        rod_stat = ROD_STATS.get(current_rod, {"luck": 1.0, "speed_bonus": 0.0, "mutation": 0.05, "desc": "無"})
        enc_stat = ENCHANT_POOL.get(current_enchant, {"luck_mod": 1.0, "speed_mod": 0.0, "mutate_mod": 0.0})
        
        enc_speed = enc_stat.get("speed_mod", 0.0) if enc_stat else 0.0
        enc_luck = enc_stat.get("luck_mod", 1.0) if enc_stat else 1.0
        enc_mutate = enc_stat.get("mutate_mod", 0.0) if enc_stat else 0.0
        
        # 🌟 3. 全新冷卻倒數公式：被動武器與種族大洗鍊
        current_time = time.time()
        base_cooldown = 10.0 - float(rod_stat.get("speed_bonus", 0.0)) - float(enc_speed)
        w_speed = float(weather_info.get("speed_mod", 0.0))
        base_cooldown += w_speed
        
        # 暗夜之竿 (Nocturnal Rod) 暴雨被動：冷卻直接強行砍半
        if current_rod == "暗夜之竿 (Nocturnal Rod)" and weather_name in ["🌧️ 狂風暴雨", "🌌 蝕日奇點 (Solar Eclipse)", "⚡ 萬雷轟頂 (Thunderstorm)"]:
            base_cooldown *= 0.5
        if base_cooldown < 1.5: base_cooldown = 1.5  # 最低不允許低於 1.5 秒
        
        if user_id in cooldowns and current_time - cooldowns[user_id] < base_cooldown:
            remaining = round(base_cooldown - (current_time - cooldowns[user_id]), 1)
            await interaction.followup.send(f"🚨 拋竿速度太快了！手拉得好酸...再等 {remaining} 秒。(當前冷卻: {round(base_cooldown, 1)}秒)", ephemeral=True)
            return
        cooldowns[user_id] = current_time

        # 智慧浮標載入：自動優先挑選最高階的消耗性浮標
        player_bobbers = {}
        for b_name in ['🔴 狂暴重力浮標', '🔵 藍海震盪浮標', '🟢 綠光電子浮標']:
            b_rec = inventory_col.find_one({"user_id": user_id, "item_name": b_name, "item_count": {"$gt": 0}})
            if b_rec: player_bobbers[b_name] = int(b_rec.get("item_count", 0))
            
        if player_bobbers.get('🔴 狂暴重力浮標', 0) > 0: bobber_name = '🔴 狂暴重力浮標'
        elif player_bobbers.get('🔵 藍海震盪浮標', 0) > 0: bobber_name = '🔵 藍海震盪浮標'
        elif player_bobbers.get('🟢 綠光電子浮標', 0) > 0: bobber_name = '🟢 綠光電子浮標'
        else: bobber_name = '⚪ 常規軟木浮標'
            
        bobber_stat = BOBBER_POOL[bobber_name]
        
        await interaction.edit_original_response(content=f"🪝 **{interaction.user.display_name}** 裝配著【**{bobber_name}**】在【{current_map}】拋出釣竿...\n🧬 當前血脈：`{mods['race_display']}` | 寵物鏈：`[{pet_chain_display}]` 加持中... 🌊")
# ======= 🎣 組十三：核心釣魚指令後半段與 15 大任務自動計數（第 1111 ~ 1210 行） =======
        wait_seconds = random.randint(2, 3)
        await asyncio.sleep(wait_seconds)
        
        cursor = inventory_col.find({"user_id": user_id, "item_count": {"$gt": 0}})
        inv_data = {doc["item_name"]: int(doc["item_count"]) for doc in cursor}
        
        # 載入消耗物資
        has_nano_bait = inv_data.get('🔋 彈性奈米反覆餌', 0) > 0
        has_star_pot = inv_data.get('天體幸運藥水 (x2)', 0) > 0
        has_rainbow_pot = inv_data.get('彩虹藥水 (x1)', 0) > 0
        has_high_pot = inv_data.get('🔵高級運氣藥水', 0) > 0
        has_normal_pot = inv_data.get('🟢普通運氣藥水', 0) > 0
        
        is_supported = (interaction.guild_id == SUPPORT_GUILD_ID) if interaction.guild_id else False
        guild_bonus = 1.2 if is_supported else 1.0
        
        # 🌟 5.5.5 終極氣運共振：魚竿幸運 x 天氣幸運 x 附魔幸運 x 支援群加成 x 遠古種族血脈加成倍率！
        w_luck = float(weather_info.get("luck_bonus", 1.0))
        luck_multiplier = float(rod_stat.get("luck", 1.0)) * w_luck * float(enc_luck) * guild_bonus * race_luck_mod
        
        # 🌟 天氣環境限定突變率乘積
        weather_mutate_mod = 1.0
        if weather_name in ["⚡ 萬雷轟頂 (Thunderstorm)", "🌌 蝕日奇點 (Solar Eclipse)", "🌀 終極風暴 (Maelstrom)", "🌋 熔岩噴發 (Eruption)"]:
            weather_mutate_mod = 2.5
            
        bait_msg = f"🌍 **全服實時氣象：【{weather_name}】** (*{weather_info['desc']}*)\n"
        if current_enchant != "無": bait_msg += f"🔮 🔮漁具灌注附魔：**【{current_enchant}】** 加持中\n"
        
        # 消耗判定
        if has_nano_bait:
            luck_multiplier *= 2.0; bait_msg += "🔋 **[神級奈米反覆餌] 裝備了彈性反覆餌，本竿不消耗任何材料，且幸運值x2.0！**\n"
        elif has_star_pot:
            luck_multiplier *= 5.0; inventory_col.update_one({"user_id": user_id, "item_name": "天體幸運藥水 (x2)"}, {"$inc": {"item_count": -1}})
            bait_msg += "✨ **[天體共鳴]** 你飲用了天體幸運藥水，爆率暴增 x5.0！\n"
        elif has_rainbow_pot:
            luck_multiplier *= 7.0; inventory_col.update_one({"user_id": user_id, "item_name": "彩虹藥水 (x1)"}, {"$inc": {"item_count": -1}})
            bait_msg += "🌈 **[彩虹極光]** 飲用彩虹藥水，全卡槽品階大飛升 x7.0！！\n"
        elif user.get("bait_count", 0) > 0:
            update_user(user_id, bait_count=int(user["bait_count"]) - 1); bait_msg += "🐛 你消耗了 1 個 **普通魚餌**！\n"
        else: bait_msg += "🪝 無魚餌素釣，全憑直覺！\n"
        
        if has_high_pot: inventory_col.update_one({"user_id": user_id, "item_name": "🔵高級運氣藥水"}, {"$inc": {"item_count": -1}}); luck_multiplier *= 2.0
        elif has_normal_pot: inventory_col.update_one({"user_id": user_id, "item_name": "🟢普通運氣藥水"}, {"$inc": {"item_count": -1}}); luck_multiplier *= 1.3
        if bobber_name != '⚪ 常規軟木浮標':
            inventory_col.update_one({"user_id": user_id, "item_name": bobber_name}, {"$inc": {"item_count": -1}})
            bait_msg += f"🚨 本竿自動消耗了 1 個 **{bobber_name}**！\n"

        # 🌟 5.5.5 天降寶箱機制：只要玩家有使用任何魚餌或奈米餌，就有 0.5% 的極致機率直接從海裡拉起藥水/魚餌寶箱！
        if user.get("bait_count", 0) > 0 or has_nano_bait:
            if random.random() < 0.005:
                chest_gift = random.choice(["🎁 基礎藥水寶箱", "🎁 稀有藥水寶箱", "🎁 傳奇藥水寶箱", "稀有魚餌 (x1)", "神話魚餌 (x1)"])
                add_inventory(user_id, chest_gift, 1)
                bait_msg += f"📦 **【⚠️ 天降橫財 ── 意外收穫！】** 拋竿激盪中，你竟然從海底漩渦順帶扯起了一個 【**{chest_gift}**】 塞進大倉庫！\n"

        roll = random.uniform(0, 100)
        luck_score = 10.0 * luck_multiplier
        if luck_score >= 500000: chosen_rarity = "作者級" if roll < 40 else "秘密" if roll < 80 else "神話"
        elif luck_score >= 150: chosen_rarity = "作者級" if roll < 1 else "秘密" if roll < 5 else "神話" if roll < 20 else "傳奇" if roll < 60 else "稀有"
        elif luck_score >= 50: chosen_rarity = "神話" if roll < 2 else "傳奇" if roll < 15 else "稀有" if roll < 50 else "普通"
        else: chosen_rarity = "傳奇" if roll < 1 else "稀有" if roll < 20 else "普通"

        base_success = 95 - bobber_stat["success_rate"]
        if current_rod == "穩健之竿 (Steady Rod)": base_success += 15
        if base_success > 98: base_success = 98

        if random.uniform(0, 100) > base_success:
            await interaction.followup.send(f"🦈 **{interaction.user.display_name} 拉扯失敗！** 一隻極其巨大的 **【{chosen_rarity}】** 級生物猛烈咬線，扯斷了你的 【{bobber_name}】 吐信逃跑了...（拉竿成功率：`{int(base_success)}%`）")
            return

        available_fish = []
        if current_map in MAP_EXCLUSIVE_FISH and chosen_rarity in MAP_EXCLUSIVE_FISH[current_map]:
            available_fish = MAP_EXCLUSIVE_FISH[current_map][chosen_rarity]
        if not available_fish: available_fish = FISH_POOL.get(chosen_rarity, FISH_POOL["普通"])
        
        fish_item = random.choice(available_fish)
        fish_name, _ = fish_item
        
        # 🌟 天氣限定隱藏魚大暴動
        if current_map == "一海・新手小池塘":
            if weather_name == "⚡ 萬雷轟頂 (Thunderstorm)" and random.random() < 0.40: fish_name = "⚡ 電光電鰻 (Electric Eel)"
            elif weather_name == "❄️ 冰天雪地 (Blizzard)" and random.random() < 0.45: fish_name = "❄️ 寒冬北極鱈 (Arctic Cod)"
        elif current_map == "二海・黃金珊瑚礁":
            if weather_name == "🌌 蝕日奇點 (Solar Eclipse)" and random.random() < 0.35: fish_name = "🌌 幽冥鬼蝠魟 (Ghost Ray)"
            elif weather_name == "🎰 歐皇狂歡 (🎰 Super Lucky)" and random.random() < 0.50: fish_name = "🎰 命運幻彩錦鯉"

        final_mutation_chance = (float(rod_stat.get("mutation", 0.05)) + float(enc_mutate) + float(bobber_stat.get("mutate_bonus", 0.0))) * weather_mutate_mod
        if current_rod == "霓虹之竿 (Neon Rod)": final_mutation_chance += 0.25
            
        if random.random() < final_mutation_chance:
            fish_name = f"{random.choice(['[🟢毒性突變]', '[🔵晶螢閃耀]', '[👑極致黃金]', '[🔴血色異變]', '[🌌星空突變]'])} {fish_name}"
            
        # 寫入雲端大倉庫
        add_inventory(user_id, fish_name, 1)
        register_fish_discovery(user_id, fish_name)
        
        # 🌟 15 大日常星級任務進度全自動過濾計數
        q_type = user.get("quest_type", "無")
        q_prog = int(user.get("quest_progress", 0))
        if q_type != "無":
            if q_type.startswith("🎣 出海大豐收"): update_user(user_id, quest_progress=q_prog + 1)
            elif q_type.startswith("🪙 財氣東來") and chosen_rarity in ["稀有", "傳奇", "神話", "秘密", "作者級"]: update_user(user_id, quest_progress=q_prog + 1)
            elif q_type.startswith("👟 海域垃圾") and "舊鞋子" in fish_name: update_user(user_id, quest_progress=q_prog + 1)
            elif q_type.startswith("🧬 基因奇蹟") and any(p in fish_name for p in ["[🟢毒性]", "[🔵晶螢]", "[👑極致]", "[🔴血色]", "[🌌星空]"]): update_user(user_id, quest_progress=q_prog + 1)
            elif q_type.startswith("🦀 珊瑚礁") and current_map == "二海・黃金珊瑚礁": update_user(user_id, quest_progress=q_prog + 1)
            elif q_type.startswith("🦈 二海巨鯊") and "鯊魚" in fish_name: update_user(user_id, quest_progress=q_prog + 1)

        # 經驗升級
        xp_gained = int(random.randint(15, 30) * guild_bonus)
        new_xp = int(user.get("xp", 0)) + xp_gained
        current_lvl = int(user.get("level", 0))
        xp_needed = (current_lvl + 1) * 50
        lvl_up_msg = ""
        while new_xp >= xp_needed:
            new_xp -= xp_needed; current_lvl += 1; xp_needed = (current_lvl + 1) * 50
            lvl_up_msg = f"\n⚡ **【LEVEL UP！】恭喜你升級到了 🌟 LV.{current_lvl} 🌟！！**"
        update_user(user_id, level=current_lvl, xp=new_xp)

        icons = {"普通": "⚪", "稀有": "🔵", "傳奇": "🟡", "神話": "🔴", "秘密": "🟣", "作者級": "🌌"}
        embed = discord.Embed(title=f"🎣 拉竿成功！ ── 【{icons.get(chosen_rarity, '⚪')} {chosen_rarity}】", description=f"{bait_msg}🧬 順利捕捉：**{fish_name}**！ (成功率: `{int(base_success)}%`)\n🏆 獲得經驗：`+{xp_gained}xp` | 當前進度：`🧬 {new_xp}/{xp_needed} XP`{lvl_up_msg}", color=0x27AE60)
        await interaction.followup.send(embed=embed)
        
    except Exception as error:
        print(f"釣魚背景報錯日誌: {error}")
        try:
            add_inventory(interaction.user.id, "🐟 吳郭魚", 1)
            await interaction.followup.send(f"🎣 系統提示：海流產生輕微波盪，**{interaction.user.display_name}** 順利收竿，釣到了一隻 **🐟 吳郭魚**！(報錯類型: {error})")
        except: pass

# ======= 🎒 組十三·五：Fisch 風格玩家背包面板 =======
def format_compact_gold(value):
    value = int(value)
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def get_backpack_items(user_id):
    cursor = inventory_col.find(
        {"user_id": int(user_id), "item_count": {"$gt": 0}},
        {"item_name": 1, "item_count": 1, "is_favorite": 1, "_id": 0}
    ).sort("item_name", 1)
    return list(cursor)


def classify_inventory_item(item_name):
    equip_words = [
        "魚竿", "魚叉", "巨弩", "破滅戟", "弒神劍", "潛水服", "潛水艇", "鑽探機", "Rod"
    ]
    if any(word in item_name for word in equip_words):
        return "equipment"
    if item_name.startswith(("🐟", "🐠", "🦈", "🐡", "🦑", "🦀", "🐙", "🐋", "🐬", "🐳", "🪼", "👟", "🐉", "🔥", "🌋", "🌌", "[")):
        return "fish"
    if any(word in item_name for word in ["魚餌", "餌", "浮標", "藥水", "寶箱", "禮包", "晶石"]):
        return "consumable"
    return "other"


def create_backpack_embed(user_id, display_name):
    user = get_user(user_id)
    mods = get_player_modifiers(user_id)
    items = get_backpack_items(user_id)

    level = int(user.get("level", 0))
    xp = int(user.get("xp", 0))
    xp_need = (level + 1) * 50
    balance = int(user.get("balance", 100))
    current_rod = user.get("rod") or "新手魚竿"
    current_map = user.get("current_map") or "一海・新手小池塘"
    enchant = user.get("enchant") or "無"
    bait_type = user.get("bait_type") or "無 (徒手肉搏)"
    pet = user.get("pet") or "無 (徒手素釣)"
    race_display = mods.get("race_display", "👤 常規人類 V1")
    pet_chain = mods.get("pet_chain", "無裝備寵物")

    fish_lines = []
    consumable_lines = []
    equipment_lines = []
    other_lines = []

    for item in items:
        name = str(item.get("item_name", "未知物品"))
        count = int(item.get("item_count", 0))
        favorite = " ❤️" if int(item.get("is_favorite", 0)) == 1 else ""
        line = f"• {name} ×`{count}`{favorite}"
        group = classify_inventory_item(name)
        if group == "fish":
            fish_lines.append(line)
        elif group == "consumable":
            consumable_lines.append(line)
        elif group == "equipment":
            equipment_lines.append(line)
        else:
            other_lines.append(line)

    total_count = sum(int(item.get("item_count", 0)) for item in items)

    embed = discord.Embed(
        title=f"🎒 ── {display_name} 的黑曜石背包 ── 🎒",
        description=(
            f"💰 錢包：**`{format_compact_gold(balance)} 🪙`** 　"
            f"📦 物品總數：**`{total_count}`**\n"
            "`────────────────────────────────`"
        ),
        color=0x34495E
    )

    embed.add_field(
        name="📊 船長狀態",
        value=(
            f"🌟 等級：**LV.{level}**\n"
            f"✨ 經驗：`{xp}/{xp_need}`\n"
            f"🧬 血脈：**{race_display}**\n"
            f"🍀 綜合幸運：`x{mods.get('luck_multiplier', 1.0):.2f}`\n"
            f"💸 金幣倍率：`x{mods.get('money_multiplier', 1.0):.2f}`"
        ),
        inline=True
    )
    embed.add_field(
        name="🎣 當前裝備",
        value=(
            f"🎣 魚竿：**{current_rod}**\n"
            f"✨ 附魔：**{enchant}**\n"
            f"🪱 魚餌：**{bait_type}**\n"
            f"🚢 載具／副裝：**{pet}**"
        ),
        inline=True
    )
    embed.add_field(
        name="🐾 寵物裝備鏈",
        value=f"`[{pet_chain}]`",
        inline=False
    )

    def add_inventory_section(title, lines, empty_text):
        if not lines:
            embed.add_field(name=title, value=empty_text, inline=False)
            return
        # Discord Embed field value 最多 1024 字元，超過時只切本頁顯示，避免指令直接報錯。
        text = "\n".join(lines)
        if len(text) > 1000:
            text = text[:997] + "..."
        embed.add_field(name=title, value=text, inline=False)

    add_inventory_section("🐟 魚獲", fish_lines, "目前沒有魚獲。")
    add_inventory_section("🧪 消耗品／道具", consumable_lines, "目前沒有消耗品。")
    add_inventory_section("🛠️ 裝備", equipment_lines, "目前沒有額外裝備。")
    if other_lines:
        add_inventory_section("📦 其他物資", other_lines, "目前沒有其他物資。")

    embed.set_footer(text="❤️ 被鎖定的最愛物資會在 /全賣 時自動跳過。下方選單可直接切換裝備與保護鎖。")
    return embed


class BackpackView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=180)
        items = get_backpack_items(user_id)
        user_items = {str(item["item_name"]): int(item.get("item_count", 0)) for item in items}
        self.add_item(EquipmentSelect(user_items))
        self.add_item(FavoriteFishSelect(user_items))


@bot.tree.command(name="背包", description="查看玩家黑曜石背包、屬性、裝備與最愛保護鎖")
async def backpack_cmd(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    afk_count = process_afk_fishing(user_id)
    user = get_user(user_id)
    update_user(user_id, name=interaction.user.display_name, last_active_time=time.time())

    embed = create_backpack_embed(user_id, interaction.user.display_name)
    if afk_count > 0:
        embed.description += f"\n💤 本次回歸已結算掛機殘留：**`{afk_count}`** 條。"
    await interaction.response.send_message(
        embed=embed,
        view=BackpackView(user_id)
    )

# ======= 🦾 組十四：黑曜石主副手裝備選單、與背包下掛喜愛鎖控制類別 =======
class EquipmentSelect(discord.ui.Select):
    def __init__(self, user_items):
        options = []
        # Fisch 15 大被動神竿與重型武器名冊，自動掃描大倉庫
        all_equipable = {
            "初級魚竿": "🎣", "高級魚竿": "🎣", "深海魚竿": "🎣", "珊瑚礁共振竿": "🎣", "量子魚竿": "🎣", 
            "穩健之竿 (Steady Rod)": "🎣", "長線之竿 (Long Rod)": "🎣", "霓虹之竿 (Neon Rod)": "🎣", 
            "黃金之竿 (Golden Rod)": "🎣", "幸運之竿 (Lucky Rod)": "🎣", "暗夜之竿 (Nocturnal Rod)": "🎣",
            "外星干擾重型桿": "🎣", "🔥 地心重型鑽探機": "🔥", "🔥 地心熔岩流體竿": "🎣", "諸神黃昏湮滅劫桿": "🎣",
            "🤿 科技耐壓潛水服": "🤿", "🚢 量子核能潛水艇": "🚢", "⚔️ 鐵製魚叉": "⚔️", "⚔️ 精鋼巨弩": "⚔️",
            "🔱 海神破滅戟": "🔱", "🌌 ADMIN破碼弒神劍": "🌌"
        }
        for item, emoji in all_equipable.items():
            if user_items.get(item, 0) > 0:
                options.append(discord.SelectOption(label=item, description="一鍵點擊穿戴切換此武裝", emoji=emoji))
        if not options:
            options.append(discord.SelectOption(label="無可用武裝", description="老哥，你的雲端大倉庫裡沒有多餘備用漁具"))
        super().__init__(placeholder="點擊此處展開大倉庫，一鍵挑選並切換穿戴武裝...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = int(interaction.user.id)
        chosen_item = self.values[0]
        if chosen_item == "無可用武裝":
            await interaction.response.send_message("❌ 你大倉庫裡沒有其他備用漁具可以更換！", ephemeral=True); return
        user = get_user(user_id)
        if "魚竿" in chosen_item or "桿" in chosen_item or "竿" in chosen_item or "Rod" in chosen_item:
            update_user(user_id, rod=chosen_item)
            msg = f"🟢 **主漁具穿戴成功！** 右手持竿已切換為：【**{chosen_item}**】！"
        elif any(v in chosen_item for v in ["潛水服", "潛水艇", "鑽探機"]):
            update_user(user_id, pet=chosen_item)
            msg = f"🟢 **探險載具變更！** 已成功更換駕駛載具為：【**{chosen_item}**】！"
        else:
            update_user(user_id, bait_type=chosen_item)
            msg = f"🟢 **遠征副手武器變更！** 已成功裝備武器為：【**{chosen_item}**】！"
        await interaction.response.send_message(msg, ephemeral=True)

class EquipmentView(discord.ui.View):
    def __init__(self, user_items):
        super().__init__(timeout=60)
        self.add_item(EquipmentSelect(user_items))

class FavoriteFishSelect(discord.ui.Select):
    def __init__(self, user_items):
        options = []
        for item_name, item_count in user_items.items():
            if item_count > 0 and not any(v in item_name for v in ["魚竿", "魚叉", "巨弩", "戟", "劍", "潛水", "鑽探", "Rod"]):
                if len(options) < 25:
                    options.append(discord.SelectOption(label=f"{item_name} (x{item_count})", value=item_name, description="一鍵點擊：[❤️ 上鎖保護 / 🔓 解除保護鎖]", emoji="🐟"))
        if not options:
            options.append(discord.SelectOption(label="大倉庫目前無可用魚獲", description="老哥，你倉庫裡沒有可以標記最愛的物資物資"))
        super().__init__(placeholder="❤️ 點擊選單鎖定魚獲：全賣時會自動完美跳過保護鎖...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = int(interaction.user.id)
        chosen_fish = self.values[0]
        if chosen_fish == "大倉庫目前無可用魚獲":
            await interaction.response.send_message("❌ 背包內沒有可用魚獲可以鎖定！", ephemeral=True); return
        
        is_fav = inventory_col.find_one({"user_id": user_id, "item_name": chosen_fish})
        current_fav = int(is_fav.get("is_favorite", 0)) if is_fav else 0
        new_fav = 1 if current_fav == 0 else 0
        inventory_col.update_one({"user_id": user_id, "item_name": chosen_fish}, {"$set": {"is_favorite": new_fav}})
        
        msg = f"❤️ **【喜愛鎖定成功】** 【{chosen_fish}】已打上防呆鋼印！執行 `/全賣` 時將**絕對跳過保護**！" if new_fav == 1 else f"🔓 **【保護安全解除】** 【{chosen_fish}】已回到常規名冊，現在可以全賣變現了。"
        await interaction.response.send_message(msg, ephemeral=True)

class FavoriteFishView(discord.ui.View):
    def __init__(self, user_items):
        super().__init__(timeout=60)
        self.add_item(FavoriteFishSelect(user_items))
        # ======= 🏪 組十四・補完：5.5.5 全球商店、自適應海域限定店與附魔洗鍊台 =======
@bot.tree.command(name="普通商店", description="顯示豐收漁具物資與神奇藥水大名冊")
async def shop_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🏪 5.5.5 全球聯網普通物資商店", description="`──────────────────────────`", color=0x2ECC71)
    shop_lines = [f"• {k}: `{v} 🪙`" for k, v in BAITS_SHOP.items()]
    embed.add_field(name="🐛 全套消耗物資、魔法藥水與盲盒寶箱", value="\n".join(shop_lines), inline=False)
    embed.set_footer(text="💡 提示：每個海域的專屬限定魚竿，必須前往該海域並向當地的駐島 NPC 購買！")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="海域商店", description="向目前所在的島嶼駐島 NPC 採購限定高階漁具與神竿")
async def island_shop_cmd(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    current_map = user.get("current_map", "一海・新手小池塘")
    if current_map not in MAPS:
        await interaction.response.send_message("❌ 當前所處海域島嶼沒有登記的 NPC 商店商販！", ephemeral=True); return
    m_data = MAPS[current_map]
    embed = discord.Embed(title=f"🏝️ 【{current_map}】 ── 限定專屬店", description=f"駐島 NPC 商販：**{m_data['npc']}**\n`──────────────────────────`", color=0x1ABC9C)
    rod_lines = [f"• {k}: `{v} 🪙`" for k, v in m_data["shop"].items()]
    embed.add_field(name="🎣 限定魚竿清單 (具備海域幸運與專屬被動共振)", value="\n".join(rod_lines), inline=False)
    await interaction.response.send_message(embed=embed)

@app_commands.describe(item_name="物品或限定魚竿名稱", quantity="數量")
@bot.tree.command(name="購買", description="採購普通商店物資，或採購目前海域的限定魚竿（魚竿每人限制購置一根）")
async def buy_cmd(interaction: discord.Interaction, item_name: str, quantity: int = 1):
    if quantity <= 0: return
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    current_map = user.get("current_map", "一海・新手小池塘")
    price, is_rod = None, False
    
    if item_name in BAITS_SHOP: price = BAITS_SHOP[item_name]
    elif current_map in MAPS and item_name in MAPS[current_map]["shop"]: price = MAPS[current_map]["shop"][item_name]; is_rod = True
    if not price:
        await interaction.response.send_message("❌ 找不到該商品！特定海域限定竿要在該海域才能購得。", ephemeral=True); return
        
    if is_rod:
        if quantity > 1:
            await interaction.response.send_message("❌ 貪心了老哥！魚竿極其珍稀，每人右手限握一根，不准多買！", ephemeral=True); return
        existing_rod = inventory_col.find_one({"user_id": user_id, "item_name": item_name, "item_count": {"$gt": 0}})
        if existing_rod or user.get("rod") == item_name:
            await interaction.response.send_message(f"❌ 購買攔截！你的大倉庫裡早已登記了【{item_name}】的資產，不准重複浪費金幣！", ephemeral=True); return
            
    total_cost = price * quantity
    if user.get("balance", 100) < total_cost:
        await interaction.response.send_message("❌ 你的錢包金幣不足！", ephemeral=True); return
        
    update_user(user_id, balance=user["balance"] - total_cost)
    if is_rod:
        update_user(user_id, rod=item_name)
        add_inventory(user_id, item_name, 1)
        await interaction.response.send_message(f"🛍️ 採購成功！你向島嶼 NPC 購置並裝備了 Fisch 珍稀魚竿：**{item_name}**！(資產已鎖定)")
    else:
        add_inventory(user_id, item_name, quantity)
        await interaction.response.send_message(f"🛍️ 採購成功！你將 {quantity} 個 **{item_name}** 收進雲端大倉庫！")

@bot.tree.command(name="附魔", description="投入 500 金幣對你的右手主魚竿洗鍊洗鍊永久守護詞條")
async def enchant_rod_cmd(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    if user.get("balance", 100) < 500:
        await interaction.response.send_message("❌ 金幣不足 500！無法啟動遠古附魔洗鍊台！", ephemeral=True); return
    chosen_enchant = random.choice(list(ENCHANT_POOL.keys()))
    update_user(user_id, balance=user["balance"] - 500, enchant=chosen_enchant)
    await interaction.response.send_message(f"🔮 遠古附魔台共振成功！魚竿獲得永久屬性：**【{chosen_enchant}】** (*{ENCHANT_POOL[chosen_enchant]['desc']}*)")
# ======= 🏰 公會系統核心一：創立與加入組織 (4 空格精準縮排) =======
@bot.tree.command(name="創立公會", description="創立你專屬的航海公會（條件：需達到 LV.50 且支付 5000 金幣）")
@app_commands.describe(公會名稱="你想為公會取什麼名字？")
async def create_guild(interaction: discord.Interaction, 公會名稱: str):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    if user.get("level", 0) < 50:
        await interaction.response.send_message(f"❌ 創立失敗！等級實力不足！需要達到 `LV.50`。", ephemeral=True)
        return
    if user.get("balance", 100) < 5000:
        await interaction.response.send_message(f"❌ 資金不足！向總部註冊公會需要 `5000` 金幣！", ephemeral=True)
        return
    if guilds_col.find_one({"members": user_id}):
        await interaction.response.send_message("❌ 你已經是某個公會的成員了，請先退出組織！", ephemeral=True)
        return
    if guilds_col.find_one({"guild_name": 公會名稱}):
        await interaction.response.send_message("❌ 這個公會名稱已經被搶先註冊了！", ephemeral=True)
        return
        
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
        await interaction.response.send_message("❌ 找不到這個公會！請確認名字是否輸入完整正確。", ephemeral=True)
        return
    if guilds_col.find_one({"members": user_id}):
        await interaction.response.send_message("❌ 你身上已經有公會會籍了！", ephemeral=True)
        return
        
    guilds_col.update_one({"guild_name": 公會名稱}, {"$push": {"members": user_id}})
    await interaction.response.send_message(f"🤝 **{interaction.user.display_name}** 成功加入航海公會：【**{公會名稱}**】！")
# ======= 🏰 公會系統核心二：公會背包面板與軍火庫商店 =======
@bot.tree.command(name="公會背包", description="查看當前公會的資金金庫、世界 BOSS 狀態以及全體船長名單")
async def guild_panel(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    guild_data = guilds_col.find_one({"members": user_id})
    if not guild_data:
        await interaction.response.send_message("❌ 老哥，你目前還是一介散人，沒有加入任何公會！", ephemeral=True)
        return
        
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


@bot.tree.command(name="武器商店", description="向航海公會軍火庫採購討伐世界 BOSS 的重型武器裝備")
async def weapon_shop(interaction: discord.Interaction):
    embed = discord.Embed(title="⚔️ 遠古重型武器軍火庫", description="`──────────────────────────`", color=0xC0392B)
    for k, v in WEAPONS_SHOP.items():
        embed.add_field(name=k, value=f"• 採購費用：`{v['cost']} 🪙`\n• 討伐魔王基礎傷害：`💥 {v['dmg']} Pts`", inline=True)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="購買武器", description="向軍火庫支付金幣採購並裝備重型武器")
@app_commands.describe(武器名稱="請輸入完整的武器裝備名稱")
async def buy_weapon(interaction: discord.Interaction, 武器名稱: str):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    if 武器名稱 not in WEAPONS_SHOP:
        await interaction.response.send_message("❌ 軍火庫裡找不到這把武器！", ephemeral=True)
        return
    w_data = WEAPONS_SHOP[武器名稱]
    if user.get("balance", 100) < w_data["cost"]:
        await interaction.response.send_message(f"❌ 金幣不足！需要 `{w_data['cost']}` 金幣！", ephemeral=True)
        return
        
    # 一鍵清空以前所擁有的所有舊武器標記
    for old_w in WEAPONS_SHOP.keys():
        inventory_col.update_one({"user_id": user_id, "item_name": old_w}, {"$set": {"item_count": 0}})
        
    update_user(user_id, balance=user["balance"] - w_data["cost"])
    add_inventory(user_id, 武器名稱, 1)
    await interaction.response.send_message(f"🛍️ 裝備成功！**{interaction.user.display_name}** 成功裝備了重型殺器：【**{武器名稱}**】！")
# ======= 🏰 公會系統核心三：世界 BOSS 召喚、與公會全員遠征圍剿副本 =======
WEAPONS_SHOP = {
    "⚔️ 鐵製魚叉": {"cost": 500, "dmg": 85}, "⚔️ 精鋼巨弩": {"cost": 2500, "dmg": 260},
    "🔱 海神破滅戟": {"cost": 8500, "dmg": 680}, "🌌 ADMIN破碼弒神劍": {"cost": 99999, "dmg": 9999}
}
BOSS_POOL = {
    "🐙 北海深淵巨怪・克拉肯": {"hp": 12000, "cost": 1000, "desc": "揮舞著千米觸手的遠古海怪，能輕易拍碎一整支遠征艦隊！"},
    "🐉 滅世混亂巨龍・利維坦": {"hp": 25000, "cost": 2500, "desc": "沉睡在海底火山的熔岩魔龍，吐息能將整片海域化為灰燼！"}
}

@bot.tree.command(name="召喚魔王", description="【會長專屬】消耗公會金庫資金，向全服海域隨機召喚一隻史詩級世界 BOSS 巨獸！")
async def summon_boss(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    guild_data = guilds_col.find_one({"leader_id": user_id})
    if not guild_data:
        await interaction.response.send_message("❌ 權限不足！只有【公會會長】才能發動魔王召喚！", ephemeral=True)
        return
        
    g_name = guild_data["guild_name"]
    if guild_data["current_boss"] != "無":
        await interaction.response.send_message(f"❌ 召喚失敗！海域中已經有 【{guild_data['current_boss']}】 肆虐了！", ephemeral=True)
        return
        
    b_name = random.choice(list(BOSS_POOL.keys()))
    b_data = BOSS_POOL[b_name]
    if guild_data["vault"] < b_data["cost"]:
        await interaction.response.send_message(f"❌ 公會金庫資金不足！召喚需要 `{b_data['cost']}` 資金，目前金庫只有 `{guild_data['vault']}` 🪙。", ephemeral=True)
        return
        
    guilds_col.update_one(
        {"guild_name": g_name},
        {"$set": {"current_boss": b_name, "boss_hp": b_data["hp"], "boss_damage": {}}, "$inc": {"vault": -b_data["cost"]}}
    )
    embed = discord.Embed(title="🚨 ── 全服警告：遠古魔王降臨 ── 🚨", description=f"🏰 【**{g_name}**】的會長使用了遠古共振器！\n\n🐉 **魔王現世**：【**{b_name}**】\n❤️ 初始總血量：`{b_data['hp']} Pts`\n\n*{b_data['desc']}*", color=0xE74C3C)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="公會遠征", description="【全體成員可參與】集體進攻圍剿當前公會的世界 BOSS，共享雲端神話戰利品大獎禮包！")
async def attack_boss(interaction: discord.Interaction):
    await interaction.response.defer()
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    
    guild_data = guilds_col.find_one({"members": user_id})
    
    # 🟢 完美補齊變數前置加載，徹底防範 NameError 未定義死鎖！
    q_type = user.get("quest_type", "無")
    q_prog = int(user.get("quest_progress", 0))
    
    if q_type.startswith("🦁 魔王討伐軍"):
        update_user(user_id, quest_progress=q_prog + 1)
        
    if not guild_data:
        await interaction.followup.send("❌ 遠征失敗！你必須先加入一個航海公會！", ephemeral=True)
        return
        
    g_name = guild_data["guild_name"]
    c_boss = guild_data["current_boss"]
    b_hp = int(guild_data["boss_hp"])
    if c_boss == "無" or b_hp <= 0:
        await interaction.followup.send("❌ 遠征失敗！目前暫無魔王可以討伐。", ephemeral=True)
        return
        
    player_dmg = 10
    equipped_weapon = "🦴 徒手肉搏"
    for w_name, w_info in WEAPONS_SHOP.items():
        w_item = inventory_col.find_one({"user_id": user_id, "item_name": w_name, "item_count": {"$gt": 0}})
        if w_item:
            player_dmg = w_info["dmg"]
            equipped_weapon = w_name
            break
        
    crit_roll = random.choice([1.0, 1.0, 1.0, 1.5, 2.0])
    final_dmg = int(player_dmg * crit_roll)
    new_hp = max(0, b_hp - final_dmg)
    
    guilds_col.update_one({"guild_name": g_name}, {"$set": {"boss_hp": new_hp}, "$inc": {f"boss_damage.{user_id}": final_dmg}})
    
    crit_msg = "🔥 **【致命一擊】觸發超高倍率暴擊！**\n" if crit_roll > 1.0 else ""
    msg = f"⚔️ **{interaction.user.display_name}** 裝備 【{equipped_weapon}】 投身遠征！\n{crit_msg}💥 輸出傷害：**`{final_dmg}`** Pts！ (❤️ 剩餘血量：`{new_hp} Pts`)\n"
    
    if new_hp <= 0:
        updated_guild = guilds_col.find_one({"guild_name": g_name})
        participants = list(updated_guild.get("boss_damage", {}).keys())
        guilds_col.update_one({"guild_name": g_name}, {"$set": {"current_boss": "無", "boss_hp": 0, "boss_damage": {}}})
        
        msg += f"\n🏆 🎉 **【魔王雲端隕落・史詩大捷！】** 🎉 🏆\n🌌 **【全員大獎賞】參與成員（共 {len(participants)} 人）全部獲得戰利品：\n💰 錢包金幣 `+5000 🪙` | `🥳神祕黃金寶箱 x2` | `🔵高級運氣藥水 x3`！**"
        for p_str_id in participants:
            p_id = int(p_str_id)
            update_user(p_id, balance=get_user(p_id).get("balance", 100) + 5000)
            add_inventory(p_id, "🥳神祕黃金寶箱", 2)
            add_inventory(p_id, "🔵高級運氣藥水", 3)
            
    await interaction.followup.send(msg)
@bot.tree.command(name="全賣", description="一鍵清空大倉庫物資（❤️ 被打上最愛保護鎖的珍稀魚獲將被絕對跳過保護！）")
async def sell_all(interaction: discord.Interaction):
    await interaction.response.defer()
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    
    cursor = inventory_col.find({"user_id": user_id, "item_count": {"$gt": 0}, "is_favorite": {"$ne": 1}})
    items = list(cursor)
    if not items:
        await interaction.followup.send("📭 雲端大倉庫內沒有可回收的常規魚獲（或者你所有的突變神魚都已上鎖 ❤️ 保護中）。", ephemeral=True); return
        
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
        
    # 🌟 5.5.5 被動：如果是「黃金之竿 (Golden Rod)」全賣回收金幣永久享有 1.5 倍複利加成！
    if user.get("rod") == "黃金之竿 (Golden Rod)":
        total_revenue = int(total_revenue * 1.5)
        sold_details.append("🔱 **【黃金之竿・點石成金】觸發 1.5 倍全服金幣回收增幅！**")
        
    # 城堡公會自動抽稅 5% 存入金庫
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

# ======= 📚 組十六：5.5.5 全新互動世界圖鑑 + 玩家交易所 =======
# 魚類圖鑑：未發現魚種會隱藏名稱、代碼、售價、稀有度與條件；成功釣到後自動解鎖。
# 工具圖鑑：直接讀取現有 ROD_STATS / BAITS_SHOP / WEAPONS_SHOP / ENCHANT_POOL / BOBBER_POOL。
# 交易所：玩家魚獲掛單、官方 10% 稅、依稀有度限制最低售價、原子扣庫存。

ENCYCLOPEDIA_COL = db["fish_encyclopedia"]
MARKET_COL = db["fish_market"]

RARITY_ORDER = ["普通", "稀有", "傳奇", "神話", "秘密", "作者級"]
RARITY_ICONS = {
    "普通": "⚪", "稀有": "🔵", "傳奇": "🟡",
    "神話": "🔴", "秘密": "🟣", "作者級": "🌌"
}

# 玩家最低掛單價格 = 魚類正常售價 × 稀有度倍率。
MARKET_FLOOR_MULTIPLIER = {
    "普通": 2.5,
    "稀有": 3.0,
    "傳奇": 3.5,
    "神話": 5.0,
    "秘密": 5.5,
    "作者級": 6.0,
}
MARKET_TAX_RATE = 0.10

# 特殊魚可補充更詳細的指定魚餌、指定魚竿與特殊條件。
# code 是「魚類內部產出代碼」，只在玩家已發現該魚後顯示。
FISH_INFO = {
    "🐉 東方青龍": {
        "code": "F031",
        "bait": ["深海魚餌", "神話魚餌"],
        "rods": ["暗夜之竿 (Nocturnal Rod)", "諸神黃昏湮滅劫桿"],
        "conditions": ["三海・馬里亞娜海溝深淵", "高幸運／特殊天氣時更容易出現"],
    },
    "🔥 諸神湮滅核心 (Abyss Core)": {
        "code": "F032",
        "bait": ["神話魚餌"],
        "rods": ["諸神黃昏湮滅劫桿"],
        "conditions": ["三海・馬里亞娜海溝深淵", "極高幸運條件"],
    },
    "🌋 熔岩火靈魚": {
        "code": "F040",
        "bait": ["熔岩魚餌", "神話魚餌"],
        "rods": ["🔥 地心熔岩流體竿", "諸神黃昏湮滅劫桿"],
        "conditions": ["四海・地幔熔岩禁地"],
    },
}


def build_fish_catalog():
    """將現有 FISH_POOL / MAP_EXCLUSIVE_FISH 統一成可供圖鑑與交易所使用的資料表。"""
    catalog = {}
    generated_index = 1

    for rarity, fish_list in FISH_POOL.items():
        for fish_name, price in fish_list:
            if fish_name not in catalog:
                catalog[fish_name] = {
                    "code": f"F{generated_index:03d}",
                    "name": fish_name,
                    "rarity": rarity,
                    "price": int(price),
                    "maps": [],
                    "rarities": [],
                }
                generated_index += 1
            if rarity not in catalog[fish_name]["rarities"]:
                catalog[fish_name]["rarities"].append(rarity)

    for map_name, rarity_dict in MAP_EXCLUSIVE_FISH.items():
        for rarity, fish_list in rarity_dict.items():
            for fish_name, price in fish_list:
                if fish_name not in catalog:
                    catalog[fish_name] = {
                        "code": f"F{generated_index:03d}",
                        "name": fish_name,
                        "rarity": rarity,
                        "price": int(price),
                        "maps": [],
                        "rarities": [],
                    }
                    generated_index += 1
                info = catalog[fish_name]
                if map_name not in info["maps"]:
                    info["maps"].append(map_name)
                if rarity not in info["rarities"]:
                    info["rarities"].append(rarity)
                info["rarity"] = rarity
                info["price"] = int(price)

    for fish_name, extra in FISH_INFO.items():
        if fish_name not in catalog:
            continue
        for key, value in extra.items():
            if key != "code":
                catalog[fish_name][key] = value
        catalog[fish_name]["code"] = extra["code"]

    for fish_name, info in catalog.items():
        info.setdefault("bait", ["普通魚餌"])
        info.setdefault("rods", ["任意可用魚竿"])
        info.setdefault("conditions", [])
        info.setdefault("rarities", [info["rarity"]])
        if not info["maps"]:
            info["maps"] = ["一般魚池"]
        info["discovery_index"] = info["code"].replace("F", "")
    return catalog


def get_fish_catalog():
    return build_fish_catalog()


def get_fish_by_code(code):
    code = str(code).strip().upper()
    for fish in get_fish_catalog().values():
        if fish["code"].upper() == code:
            return fish
    return None


def is_fish_discovered(user_id, fish_name):
    return ENCYCLOPEDIA_COL.find_one({
        "user_id": int(user_id),
        "fish_name": fish_name,
        "discovered": True
    }) is not None


def register_fish_discovery(user_id, fish_name):
    """成功捕獲後解鎖原始魚種；突變前綴不會污染圖鑑。"""
    base_name = str(fish_name)
    mutation_prefixes = [
        "[🟢毒性突變] ", "[🔵晶螢閃耀] ", "[👑極致黃金] ",
        "[🔴血色異變] ", "[🌌星空突變] "
    ]
    for prefix in mutation_prefixes:
        if base_name.startswith(prefix):
            base_name = base_name[len(prefix):]

    fish = get_fish_catalog().get(base_name)
    if not fish:
        return

    ENCYCLOPEDIA_COL.update_one(
        {"user_id": int(user_id), "fish_name": base_name},
        {"$set": {
            "fish_name": base_name,
            "fish_code": fish["code"],
            "discovered": True,
            "unlocked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }},
        upsert=True
    )


def fish_market_floor(fish_data):
    multiplier = MARKET_FLOOR_MULTIPLIER.get(fish_data.get("rarity"), 2.5)
    return int(fish_data.get("price", 0) * multiplier)


def format_market_price(value):
    return f"{int(value):,}"


def chunk_lines(lines, max_chars=950):
    chunks, current = [], []
    current_len = 0
    for line in lines:
        line_len = len(line) + 1
        if current and current_len + line_len > max_chars:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += line_len
    if current:
        chunks.append("\n".join(current))
    return chunks


def get_discovered_fish_set(user_id):
    return set(
        doc.get("fish_name")
        for doc in ENCYCLOPEDIA_COL.find(
            {"user_id": int(user_id), "discovered": True},
            {"fish_name": 1, "_id": 0}
        )
        if doc.get("fish_name")
    )


def create_encyclopedia_home_embed(user_id, display_name):
    catalog = get_fish_catalog()
    discovered = get_discovered_fish_set(user_id)
    total = len(catalog)
    found = sum(1 for name in catalog if name in discovered)
    percent = (found / total * 100) if total else 0

    embed = discord.Embed(
        title=f"📚 {display_name} 的世界圖鑑",
        description=(
            f"🐟 魚類發現度：**{found}/{total}**（`{percent:.1f}%`）\n"
            f"🔓 已解鎖：**{found}**　🔒 未發現：**{total - found}**\n\n"
            "🐟 **魚類圖鑑**：依地圖、稀有度、全部魚類或搜尋。\n"
            "🛠️ **工具圖鑑**：魚竿、魚餌、武器、載具、寵物、附魔、浮標。\n\n"
            "🔐 未發現的魚不會透露名稱、代碼、稀有度、正常售價、指定魚竿、指定魚餌與特殊條件。\n"
            "🎣 第一次成功捕獲該魚後，圖鑑會自動完整解鎖。"
        ),
        color=0x34495E
    )
    for rarity in RARITY_ORDER:
        fishes = [f for f in catalog.values() if f.get("rarity") == rarity]
        if not fishes:
            continue
        found_count = sum(1 for f in fishes if f["name"] in discovered)
        embed.add_field(
            name=f"{RARITY_ICONS[rarity]} {rarity}",
            value=f"`{found_count}/{len(fishes)}` 已發現",
            inline=True
        )
    return embed


class EncyclopediaMainSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🐟 魚類圖鑑", value="fish", description="地圖、稀有度、搜尋與完整收藏進度"),
            discord.SelectOption(label="🛠️ 工具圖鑑", value="tools", description="魚竿、魚餌、武器、載具、寵物、附魔、浮標"),
        ]
        super().__init__(placeholder="選擇圖鑑大分類……", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "fish":
            await interaction.response.edit_message(
                embed=create_fish_index_embed(interaction.user.id),
                view=FishIndexView()
            )
        else:
            await interaction.response.edit_message(
                embed=create_tool_index_embed(interaction.user.id),
                view=ToolIndexView()
            )


class EncyclopediaMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(EncyclopediaMainSelect())


class FishIndexSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🗺️ 依地圖", value="map", description="查看各海域魚種與地圖完成度"),
            discord.SelectOption(label="⭐ 依稀有度", value="rarity", description="查看不同稀有度收藏進度"),
            discord.SelectOption(label="📖 全部魚類", value="all", description="查看所有魚種的發現狀態"),
        ]
        super().__init__(placeholder="選擇魚類圖鑑瀏覽方式……", options=options)

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        if choice == "map":
            embed = create_fish_map_embed(interaction.user.id)
        elif choice == "rarity":
            embed = create_fish_rarity_embed(interaction.user.id)
        else:
            embed = create_fish_list_embed(interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=FishIndexView())


class BackToEncyclopediaButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="返回圖鑑首頁", emoji="📚", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=create_encyclopedia_home_embed(interaction.user.id, interaction.user.display_name),
            view=EncyclopediaMainView()
        )


class FishSearchModal(discord.ui.Modal, title="🔎 搜尋魚類"): 
    keyword = discord.ui.TextInput(
        label="輸入已知魚名或產出代碼",
        placeholder="例如：青龍、鯊魚、F031",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=create_fish_search_embed(interaction.user.id, str(self.keyword).strip()),
            view=FishIndexView()
        )


class FishSearchButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="搜尋魚類", emoji="🔎", style=discord.ButtonStyle.primary, row=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(FishSearchModal())


class FishIndexView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(FishIndexSelect())
        self.add_item(FishSearchButton())
        self.add_item(BackToEncyclopediaButton())


def fish_display_line(user_id, fish):
    discovered = is_fish_discovered(user_id, fish["name"])
    if not discovered:
        return "• 🔒 **未知魚種** — 尚未發現"
    return (
        f"• {RARITY_ICONS.get(fish['rarity'], '⚪')} **{fish['name']}** "
        f"`{fish['code']}` — `{format_market_price(fish['price'])} 🪙`"
    )


def create_fish_index_embed(user_id):
    catalog = get_fish_catalog()
    discovered = get_discovered_fish_set(user_id)
    embed = discord.Embed(
        title="🐟 魚類世界圖鑑",
        description=(
            f"已發現：**{len(discovered & set(catalog))}/{len(catalog)}**\n\n"
            "🗺️ 依地圖｜⭐ 依稀有度｜📖 全部魚類｜🔎 搜尋\n\n"
            "🔒 未發現魚種只顯示『未知魚種』，完整情報會在首次捕獲後公開。"
        ),
        color=0x3498DB
    )
    return embed


def create_fish_list_embed(user_id):
    catalog = get_fish_catalog()
    embed = discord.Embed(
        title="📖 全部魚類",
        description="已發現會顯示完整資訊；未發現不透露內部代碼與任何稀有度情報。",
        color=0x3498DB
    )
    for rarity in RARITY_ORDER:
        fishes = [fish for fish in catalog.values() if fish.get("rarity") == rarity]
        if not fishes:
            continue
        lines = [fish_display_line(user_id, fish) for fish in fishes]
        found = sum(1 for fish in fishes if is_fish_discovered(user_id, fish["name"]))
        chunks = chunk_lines(lines)
        for idx, chunk in enumerate(chunks):
            suffix = f"・{idx + 1}" if len(chunks) > 1 else ""
            embed.add_field(
                name=f"{RARITY_ICONS[rarity]} {rarity} ({found}/{len(fishes)}){suffix}",
                value=chunk,
                inline=False
            )
    return embed


def create_fish_map_embed(user_id):
    catalog = get_fish_catalog()
    embed = discord.Embed(
        title="🗺️ 魚類圖鑑・依地圖",
        description="各海域的魚種會依發現狀態顯示。",
        color=0x1ABC9C
    )
    for map_name in MAP_EXCLUSIVE_FISH.keys():
        fishes = [fish for fish in catalog.values() if map_name in fish.get("maps", [])]
        if not fishes:
            continue
        found = sum(1 for fish in fishes if is_fish_discovered(user_id, fish["name"]))
        lines = [fish_display_line(user_id, fish) for fish in fishes]
        text = "\n".join(lines)
        if len(text) > 950:
            text = text[:947] + "..."
        embed.add_field(
            name=f"🚢 {map_name} ({found}/{len(fishes)})",
            value=text,
            inline=False
        )
    return embed


def create_fish_rarity_embed(user_id):
    catalog = get_fish_catalog()
    embed = discord.Embed(
        title="⭐ 魚類圖鑑・依稀有度",
        description="稀有度總覽只對已發現魚種公開；未發現魚種統一顯示未知。",
        color=0x9B59B6
    )
    for rarity in RARITY_ORDER:
        fishes = [fish for fish in catalog.values() if fish.get("rarity") == rarity]
        if not fishes:
            continue
        found = sum(1 for fish in fishes if is_fish_discovered(user_id, fish["name"]))
        lines = [fish_display_line(user_id, fish) for fish in fishes]
        text = "\n".join(lines)
        if len(text) > 950:
            text = text[:947] + "..."
        embed.add_field(
            name=f"{RARITY_ICONS[rarity]} {rarity} ({found}/{len(fishes)})",
            value=text,
            inline=False
        )
    return embed


def create_fish_search_embed(user_id, keyword):
    catalog = get_fish_catalog()
    key = str(keyword).strip().lower()
    results = []
    for fish in catalog.values():
        # 搜尋名稱只為玩家方便；不會因搜尋而直接解鎖資料。
        if key in fish["name"].lower() or key in fish["code"].lower():
            results.append(fish)

    embed = discord.Embed(title=f"🔎 搜尋結果：{keyword}", color=0x2980B9)
    if not results:
        embed.description = "❌ 沒有符合條件的魚類。"
        return embed

    lines = []
    for fish in results[:25]:
        if is_fish_discovered(user_id, fish["name"]):
            lines.append(
                f"{RARITY_ICONS.get(fish['rarity'], '⚪')} **{fish['name']}** `{fish['code']}`\n"
                f"稀有度：**{fish['rarity']}**　正常售價：`{format_market_price(fish['price'])} 🪙`\n"
                f"指定魚餌：{', '.join(fish.get('bait', ['普通魚餌']))}\n"
                f"指定魚竿：{', '.join(fish.get('rods', ['任意可用魚竿']))}\n"
                f"特殊條件：{'；'.join(fish.get('conditions', [])) or '無特殊條件'}"
            )
        else:
            lines.append("🔒 **未知魚種**\n尚未解鎖任何情報。")
    embed.description = "\n\n".join(lines)
    return embed


class ToolCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🎣 魚竿", value="rods", description="查看全部魚竿能力"),
            discord.SelectOption(label="🪱 魚餌", value="bait", description="查看商店魚餌與價格"),
            discord.SelectOption(label="🗡️ 武器", value="weapons", description="查看遠征與公會武器"),
            discord.SelectOption(label="🚗 載具", value="vehicles", description="查看現有載具裝備"),
            discord.SelectOption(label="🐾 寵物", value="pets", description="查看目前寵物效果"),
            discord.SelectOption(label="✨ 附魔", value="enchant", description="查看附魔能力"),
            discord.SelectOption(label="🎈 浮標", value="bobber", description="查看浮標能力"),
        ]
        super().__init__(placeholder="選擇工具圖鑑分類……", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=create_tool_detail_embed(self.values[0]),
            view=ToolIndexView()
        )


class ToolIndexView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(ToolCategorySelect())
        self.add_item(BackToEncyclopediaButton())


def create_tool_index_embed(user_id):
    return discord.Embed(
        title="🛠️ 工具圖鑑",
        description=(
            "這裡集中整理目前遊戲中的主要工具資料。\n\n"
            "🎣 魚竿　🪱 魚餌　🗡️ 武器　🚗 載具\n"
            "🐾 寵物　✨ 附魔　🎈 浮標\n\n"
            "資料直接讀取遊戲內現有設定，避免商店價格與圖鑑分離。"
        ),
        color=0xE67E22
    )


def create_tool_detail_embed(category):
    embed = discord.Embed(title="🛠️ 工具圖鑑", color=0xE67E22)
    if category == "rods":
        for name, data in ROD_STATS.items():
            embed.add_field(
                name=f"🎣 {name}",
                value=(
                    f"🍀 Luck：`{data.get('luck', 1)}`\n"
                    f"⚡ Speed：`+{data.get('speed_bonus', 0)}`\n"
                    f"🧬 Mutation：`{data.get('mutation', 0)}`\n"
                    f"{data.get('desc', '無特殊描述')}"
                ),
                inline=True
            )
    elif category == "bait":
        lines = [f"• **{name}** — `{price:,} 🪙`" for name, price in BAITS_SHOP.items()]
        chunks = chunk_lines(lines)
        for idx, chunk in enumerate(chunks[:4]):
            embed.add_field(name=f"🪱 魚餌 {idx + 1}", value=chunk, inline=False)
    elif category == "enchant":
        lines = []
        for name, data in ENCHANT_POOL.items():
            lines.append(
                f"• ✨ **{name}**\n"
                f"{data.get('desc', '無')}\n"
                f"Luck `x{data.get('luck_mod', 1)}`｜Speed `+{data.get('speed_mod', 0)}`｜Mutation `+{data.get('mutate_mod', 0)}"
            )
        for idx, chunk in enumerate(chunk_lines(lines)[:4]):
            embed.add_field(name=f"✨ 附魔 {idx + 1}", value=chunk, inline=False)
    elif category == "bobber":
        for name, data in BOBBER_POOL.items():
            embed.add_field(
                name=f"🎈 {name}",
                value=(
                    f"成功率：`+{data.get('success_rate', 0)}%`\n"
                    f"異變：`+{data.get('mutate_bonus', 0)}`"
                ),
                inline=True
            )
    elif category == "weapons":
        for name, data in WEAPONS_SHOP.items():
            embed.add_field(
                name=f"🗡️ {name}",
                value=f"傷害：`{data.get('dmg', 0)}`",
                inline=True
            )
    elif category == "vehicles":
        embed.description = (
            "🚗 目前載具共用玩家裝備欄位；現有資料可直接從玩家的 `pet` 欄位辨識。\n\n"
            "已知載具：科技耐壓潛水服、量子核能潛水艇、地心重型鑽探機等。"
        )
    elif category == "pets":
        embed.description = (
            "🐾 寵物效果目前由 `get_player_modifiers()` 統一計算。\n\n"
            "常見效果：招財貓＝金幣加成、獵鷹＝幸運加成、小青龍＝幸運＋金幣加成。"
        )
    return embed


@bot.tree.command(name="查看圖鑑", description="開啟全新的互動式魚類與工具圖鑑")
async def view_encyclopedia(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    await interaction.response.send_message(
        embed=create_encyclopedia_home_embed(user_id, interaction.user.display_name),
        view=EncyclopediaMainView()
    )


# ======= 🏪 組十七：玩家交易所 =======
def generate_market_code():
    """生成玩家可讀的 8 碼掛單代碼，避免直接暴露 Mongo ObjectId。"""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(30):
        code = "".join(random.choice(alphabet) for _ in range(8))
        if MARKET_COL.find_one({"listing_code": code}) is None:
            return code
    return f"{random.randint(10000000, 99999999)}"


def get_market_listings(limit=10, keyword=None, seller_id=None):
    query = {"status": "active", "quantity": {"$gt": 0}}
    if keyword:
        safe_keyword = str(keyword).strip()
        if safe_keyword:
            # Regex 特殊字元轉義，避免搜尋框內容干擾 Mongo 查詢。
            import re
            query["item_name"] = {"$regex": re.escape(safe_keyword), "$options": "i"}
    if seller_id is not None:
        query["seller_id"] = int(seller_id)
    return list(MARKET_COL.find(query).sort([("unit_price", 1), ("created_at", 1)]).limit(limit))


def create_market_embed(user_id, keyword=None, mine=False):
    listings = get_market_listings(12, keyword, int(user_id) if mine else None)
    embed = discord.Embed(
        title="🏪 歡樂交易所",
        description=(
            f"🏛️ 官方交易稅：**{MARKET_TAX_RATE * 100:.0f}%**\n"
            "💰 掛單最低售價：普通 2.5×｜稀有 3×｜傳奇 3.5×｜神話 5×｜秘密 5.5×｜作者級 6×\n"
            "📦 目前僅開放魚類玩家掛單交易。"
        ),
        color=0xF1C40F
    )
    if keyword:
        embed.description += f"\n🔎 搜尋：`{keyword}`"
    if mine:
        embed.description += "\n👤 目前顯示：**我的掛單**"

    if not listings:
        embed.add_field(
            name="📭 沒有符合條件的掛單",
            value="可以稍後再來看看，或使用 `/上架交易所` 建立第一筆掛單。",
            inline=False
        )
        return embed

    for listing in listings:
        fish = get_fish_catalog().get(listing.get("item_name"))
        if not fish:
            continue
        rarity = fish["rarity"]
        floor = fish_market_floor(fish)
        total_example = int(listing["unit_price"]) * min(1, int(listing["quantity"]))
        seller_name = f"<@{int(listing['seller_id'])}>"
        embed.add_field(
            name=f"{RARITY_ICONS.get(rarity, '⚪')} {fish['name']}",
            value=(
                f"數量：`{int(listing['quantity'])}`\n"
                f"單價：`{format_market_price(listing['unit_price'])} 🪙`\n"
                f"起跳：`{format_market_price(floor)} 🪙`\n"
                f"賣家：{seller_name}\n"
                f"掛單：`{listing.get('listing_code', str(listing['_id'])[-8:])}`\n"
                f"買 1 件：`{format_market_price(total_example)} 🪙`"
            ),
            inline=True
        )
    embed.set_footer(text="購買：/購買交易品 listing_id 數量　｜　上架：/上架交易所　｜　下架：/下架交易品")
    return embed


class MarketSearchModal(discord.ui.Modal, title="🔎 搜尋交易商品"):
    keyword = discord.ui.TextInput(
        label="商品名稱（可留空）",
        placeholder="例如：青龍、鯊魚",
        required=False,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        keyword = str(self.keyword).strip()
        await interaction.response.edit_message(
            embed=create_market_embed(interaction.user.id, keyword or None),
            view=MarketView()
        )


class MarketSearchButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="搜尋", emoji="🔎", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(MarketSearchModal())


class MarketRefreshButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="刷新", emoji="🔄", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=create_market_embed(interaction.user.id),
            view=MarketView()
        )


class MarketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(MarketSearchButton())
        self.add_item(MarketRefreshButton())


@bot.tree.command(name="交易所", description="查看玩家交易所掛單與市場價格")
async def market_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=create_market_embed(interaction.user.id),
        view=MarketView()
    )


@bot.tree.command(name="上架交易所", description="將已發現的魚類掛到玩家交易所")
@app_commands.describe(fish_name="要出售的魚名", quantity="出售數量", unit_price="單條售價")
async def market_list_cmd(interaction: discord.Interaction, fish_name: str, quantity: int, unit_price: int):
    await interaction.response.defer(ephemeral=True)
    user_id = int(interaction.user.id)
    fish = get_fish_catalog().get(fish_name)

    if not fish:
        await interaction.followup.send("❌ 找不到這條魚。請使用 `/查看圖鑑` 或 `/交易所` 確認名稱。", ephemeral=True)
        return
    if not is_fish_discovered(user_id, fish_name):
        await interaction.followup.send("❌ 你尚未發現這條魚，不能上架交易所。", ephemeral=True)
        return
    if quantity <= 0 or quantity > 999:
        await interaction.followup.send("❌ 數量必須介於 1～999。", ephemeral=True)
        return
    if unit_price <= 0:
        await interaction.followup.send("❌ 售價必須大於 0。", ephemeral=True)
        return

    floor = fish_market_floor(fish)
    if unit_price < floor:
        mult = MARKET_FLOOR_MULTIPLIER.get(fish["rarity"], 2.5)
        await interaction.followup.send(
            f"❌ 低於官方最低掛單價！\n"
            f"{fish['name']}（{fish['rarity']}）最低：`{floor:,} 🪙`\n"
            f"計算：正常售價 `{fish['price']:,}` × `{mult:g}`",
            ephemeral=True
        )
        return

    consumed = inventory_col.update_one(
        {"user_id": user_id, "item_name": fish_name, "item_count": {"$gte": quantity}},
        {"$inc": {"item_count": -quantity}}
    )
    if consumed.modified_count != 1:
        await interaction.followup.send("❌ 你的背包沒有足夠數量，或庫存剛剛已變更。", ephemeral=True)
        return

    listing_code = generate_market_code()
    try:
        result = MARKET_COL.insert_one({
            "listing_code": listing_code,
            "seller_id": user_id,
            "item_name": fish_name,
            "quantity": int(quantity),
            "unit_price": int(unit_price),
            "floor_price": int(floor),
            "rarity": fish["rarity"],
            "status": "active",
            "created_at": datetime.now(),
        })
    except Exception as exc:
        # 掛單建立失敗時把魚退回背包，避免物品憑空消失。
        add_inventory(user_id, fish_name, quantity)
        print(f"[MARKET] insert listing failed: {exc}")
        await interaction.followup.send("❌ 建立掛單失敗，魚獲已退回背包，請稍後再試。", ephemeral=True)
        return

    await interaction.followup.send(
        f"✅ 上架成功！\n"
        f"📦 {fish_name} ×`{quantity}`\n"
        f"💰 單價：`{unit_price:,} 🪙`\n"
        f"🏛️ 成交後官方抽取 `{MARKET_TAX_RATE * 100:.0f}%` 稅金\n"
        f"🆔 掛單代碼：`{listing_code}`",
        ephemeral=True
    )


@bot.tree.command(name="購買交易品", description="購買玩家交易所中的魚類")
@app_commands.describe(listing_id="交易所顯示的 8 碼掛單代碼", quantity="購買數量")
async def market_buy_cmd(interaction: discord.Interaction, listing_id: str, quantity: int):
    await interaction.response.defer(ephemeral=True)
    buyer_id = int(interaction.user.id)
    listing_id = str(listing_id).strip().upper()

    if quantity <= 0 or quantity > 999:
        await interaction.followup.send("❌ 數量必須介於 1～999。", ephemeral=True)
        return

    listing = MARKET_COL.find_one({
        "listing_code": listing_id,
        "status": "active",
        "quantity": {"$gt": 0}
    })
    if not listing:
        await interaction.followup.send("❌ 找不到有效掛單，可能已售罄或已下架。", ephemeral=True)
        return

    seller_id = int(listing["seller_id"])
    if seller_id == buyer_id:
        await interaction.followup.send("❌ 不能購買自己的掛單。", ephemeral=True)
        return
    available = int(listing["quantity"])
    if quantity > available:
        await interaction.followup.send(f"❌ 該掛單目前只有 `{available}` 件。", ephemeral=True)
        return

    total = int(listing["unit_price"]) * int(quantity)
    buyer = get_user(buyer_id)
    buyer_balance = int(buyer.get("balance", 100))
    if buyer_balance < total:
        await interaction.followup.send(f"❌ 金幣不足！需要 `{total:,} 🪙`。", ephemeral=True)
        return

    # 先搶到掛單庫存，避免多人同時購買造成超賣。
    reserved = MARKET_COL.update_one(
        {
            "_id": listing["_id"],
            "status": "active",
            "quantity": {"$gte": quantity}
        },
        {"$inc": {"quantity": -int(quantity)}}
    )
    if reserved.modified_count != 1:
        await interaction.followup.send("❌ 這筆掛單剛被其他玩家買走或數量不足，請刷新交易所。", ephemeral=True)
        return

    tax = int(total * MARKET_TAX_RATE)
    seller_revenue = total - tax

    # 交易結算採用可回滾流程：任何一步失敗都嘗試恢復掛單、買家金幣與庫存。
    buyer_debited = False
    seller_credited = False
    try:
        buyer_changed = users_col.update_one(
            {"user_id": buyer_id, "balance": {"$gte": total}},
            {"$inc": {"balance": -total}}
        )
        if buyer_changed.modified_count != 1:
            raise RuntimeError("buyer balance changed")
        buyer_debited = True

        seller_changed = users_col.update_one(
            {"user_id": seller_id},
            {"$inc": {"balance": seller_revenue}}
        )
        if seller_changed.modified_count != 1:
            raise RuntimeError("seller balance update failed")
        seller_credited = True

        add_inventory(buyer_id, listing["item_name"], quantity)
    except Exception as exc:
        MARKET_COL.update_one(
            {"_id": listing["_id"]},
            {"$inc": {"quantity": int(quantity)}, "$set": {"status": "active"}}
        )
        if buyer_debited:
            users_col.update_one(
                {"user_id": buyer_id},
                {"$inc": {"balance": total}}
            )
        if seller_credited:
            users_col.update_one(
                {"user_id": seller_id},
                {"$inc": {"balance": -seller_revenue}}
            )
        print(f"[MARKET] transaction rollback: {exc}")
        await interaction.followup.send("❌ 交易結算發生錯誤，系統已嘗試自動回滾。請稍後再試。", ephemeral=True)
        return

    remaining = int(listing["quantity"]) - int(quantity)
    if remaining <= 0:
        MARKET_COL.update_one(
            {"_id": listing["_id"], "quantity": 0},
            {"$set": {"status": "sold", "closed_at": datetime.now()}}
        )

    await interaction.followup.send(
        f"✅ 交易成功！\n"
        f"📦 **{listing['item_name']}** ×`{quantity}`\n"
        f"💰 成交總價：`{total:,} 🪙`\n"
        f"🏛️ 官方 10% 稅：`{tax:,} 🪙`\n"
        f"💵 賣家實收：`{seller_revenue:,} 🪙`",
        ephemeral=True
    )


@bot.tree.command(name="下架交易品", description="下架自己的交易所掛單並取回剩餘魚獲")
@app_commands.describe(listing_id="自己的 8 碼掛單代碼")
async def market_cancel_cmd(interaction: discord.Interaction, listing_id: str):
    await interaction.response.defer(ephemeral=True)
    user_id = int(interaction.user.id)
    listing_id = str(listing_id).strip().upper()

    listing = MARKET_COL.find_one_and_update(
        {
            "listing_code": listing_id,
            "seller_id": user_id,
            "status": "active",
            "quantity": {"$gt": 0}
        },
        {"$set": {"status": "cancelled", "closed_at": datetime.now()}},
        return_document=True
    )
    if not listing:
        await interaction.followup.send("❌ 找不到你名下的有效掛單。", ephemeral=True)
        return

    remaining = int(listing.get("quantity", 0))
    if remaining > 0:
        add_inventory(user_id, listing["item_name"], remaining)

    await interaction.followup.send(
        f"✅ 已下架掛單 `{listing_id}`。\n"
        f"📦 取回：**{listing['item_name']} ×{remaining}**",
        ephemeral=True
    )


# ======= 🧭 新架構 V6：新手教學 + 鍛造 + 探險 + 世界BOSS + 血脈 + 拍賣場 =======
# 這一區全部使用 MongoDB 持久化；新增資料不會依賴 Render 本地磁碟。
TUTORIAL_STEPS = [
    {
        "title": "🎣 ① 認識魚竿",
        "desc": "歡迎來到歡樂釣魚場！你的第一支魚竿是【新手魚竿】。",
        "reward": {"balance": 100},
    },
    {
        "title": "🎒 ② 認識背包",
        "desc": "背包會顯示你的金幣、魚竿、魚獲、消耗品與裝備。",
        "reward": {"item": "普通魚餌", "amount": 3},
    },
    {
        "title": "📘 ③ 認識圖鑑",
        "desc": "成功捕獲魚種後，會自動加入雲端圖鑑；未發現的魚不會洩漏敏感資料。",
        "reward": {"item": "🎁 基礎藥水寶箱", "amount": 1},
    },
    {
        "title": "🏪 ④ 認識交易",
        "desc": "交易所可以直接掛單；拍賣場則採競標制，最高出價者得標。",
        "reward": {"balance": 500},
    },
    {
        "title": "🧭 ⑤ 完成啟航",
        "desc": "你已經掌握基本系統，可以解鎖鍛造、探險、世界 Boss、血脈與拍賣場。",
        "reward": {"item": "海藻餌", "amount": 5},
    },
]

FORGE_RECIPES = {
    "🪝 強化鋼鉤": {
        "materials": {"🐟 吳郭魚": 5, "普通魚餌": 10},
        "cost": 1000,
        "reward_item": "🪝 強化鋼鉤",
        "desc": "基礎鍛造材料製成的強化魚鉤。",
    },
    "⚙️ 深海合金核心": {
        "materials": {"🐡 黃金河豚": 2, "🪝 強化鋼鉤": 1},
        "cost": 5000,
        "reward_item": "⚙️ 深海合金核心",
        "desc": "可作為高階裝備與未來神竿進化的核心材料。",
    },
    "🌌 星海神性核心": {
        "materials": {"⚙️ 深海合金核心": 2, "🎁 傳奇藥水寶箱": 1, "🌟 遠古星願晶石": 5},
        "cost": 25000,
        "reward_item": "🌌 星海神性核心",
        "desc": "極低產量的神性鍛造材料。",
    },
}

ADVENTURE_TABLE = [
    {"name": "🌿 近海遺跡", "minutes": 10, "weight": 45, "rewards": [("普通魚餌", 5), ("🐟 吳郭魚", 3), ("海藻餌", 4)], "gold": (100, 400)},
    {"name": "🌊 深海裂谷", "minutes": 20, "weight": 30, "rewards": [("稀有魚餌 (x1)", 3), ("🐡 黃金河豚", 1), ("🎁 稀原藥水寶箱", 1)], "gold": (500, 1500)},
    {"name": "🌌 星穹遺跡", "minutes": 30, "weight": 18, "rewards": [("傳說魚餌 (x1)", 2), ("🎁 傳奇藥水寶箱", 1), ("🌟 遠古星願晶石", 3)], "gold": (1200, 4500)},
    {"name": "👑 諸神禁域", "minutes": 45, "weight": 7, "rewards": [("神話魚餌 (x1)", 2), ("🌌 星海神性核心", 1), ("🌟 遠古星願晶石", 8)], "gold": (3000, 12000)},
]

BLOODLINES = {
    "👤 常規人類": {
        "max_version": 1,
        "unlock_cost": 0,
        "requirements": "初始血脈",
        "desc": "均衡且沒有額外偏科的基礎血脈。",
    },
    "🦈 深海鯊皇": {
        "max_version": 3,
        "unlock_cost": 5000,
        "requirements": "LV.20",
        "desc": "偏向幸運與金幣，適合長期農場。",
    },
    "🧜 海妖": {
        "max_version": 3,
        "unlock_cost": 15000,
        "requirements": "LV.60",
        "desc": "偏向高稀有度捕獲與突變。",
    },
    "🔱 亞特蘭提斯神族": {
        "max_version": 4,
        "unlock_cost": 60000,
        "requirements": "LV.160 + 三海",
        "desc": "最終階血脈，可成長至 V4。",
    },
}

WORLD_BOSS_DEFAULT = {
    "boss_id": "global_01",
    "name": "🌊 深海古神・利維坦",
    "max_hp": 10000000,
    "hp": 10000000,
    "active": True,
    "created_at": time.time(),
    "last_reset": time.time(),
    "rewarded": False,
    "round": 1,
}

forge_col = db["forge_history"]
adventure_col = db["adventure_sessions"]
world_boss_col = db["world_boss"]
auction_col = db["auction_house"]


def get_item_count(user_id, item_name):
    doc = inventory_col.find_one({"user_id": int(user_id), "item_name": item_name})
    return int(doc.get("item_count", 0)) if doc else 0


def consume_item_atomic(user_id, item_name, amount):
    amount = int(amount)
    if amount <= 0:
        return True
    result = inventory_col.update_one(
        {"user_id": int(user_id), "item_name": item_name, "item_count": {"$gte": amount}},
        {"$inc": {"item_count": -amount}}
    )
    return result.modified_count == 1


def apply_tutorial_reward(user_id, reward):
    if not reward:
        return ""
    parts = []
    if "balance" in reward:
        amount = int(reward["balance"])
        users_col.update_one({"user_id": int(user_id)}, {"$inc": {"balance": amount}})
        parts.append(f"💰 +{amount:,} 金幣")
    if reward.get("item"):
        amount = int(reward.get("amount", 1))
        add_inventory(user_id, reward["item"], amount)
        parts.append(f"📦 {reward['item']} ×{amount}")
    return "；".join(parts)


async def tutorial_gate(interaction: discord.Interaction):
    """全域新手鎖：完成教學前只允許新手教學與幫助。"""
    user = get_user(int(interaction.user.id))
    if bool(user.get("tutorial_completed", False)):
        return True
    command_name = interaction.command.name if interaction.command else ""
    allowed = {"新手教學", "幫助"}
    if command_name in allowed:
        return True
    step = int(user.get("tutorial_step", 0))
    step = max(0, min(step, len(TUTORIAL_STEPS)))
    await interaction.response.send_message(
        f"🔒 **新手保護鎖啟用中**\n\n"
        f"你目前尚未完成新手教學。\n"
        f"📖 目前進度：`{step}/{len(TUTORIAL_STEPS)}`\n"
        f"請先使用 `/新手教學` 完成啟航流程。",
        ephemeral=True
    )
    return False


class TutorialNextButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="下一步", style=discord.ButtonStyle.primary, emoji="➡️")

    async def callback(self, interaction: discord.Interaction):
        user_id = int(interaction.user.id)
        user = get_user(user_id)
        step = int(user.get("tutorial_step", 0))
        if step >= len(TUTORIAL_STEPS):
            update_user(user_id, tutorial_completed=True)
            await interaction.response.edit_message(content="✅ 新手教學已完成！現在可以自由使用所有遊戲功能。", embed=None, view=None)
            return
        reward_text = apply_tutorial_reward(user_id, TUTORIAL_STEPS[step]["reward"])
        step += 1
        completed = step >= len(TUTORIAL_STEPS)
        update_user(user_id, tutorial_step=step, tutorial_completed=completed, last_active_time=time.time())
        if completed:
            embed = discord.Embed(
                title="🎉 新手教學完成！",
                description="你已成功完成啟航流程。\n\n🔓 **鍛造、探險、世界 Boss、血脈、交易所、拍賣場等系統全部解鎖！**",
                color=0x2ECC71,
            )
            if reward_text:
                embed.add_field(name="🎁 最終獎勵", value=reward_text, inline=False)
            await interaction.response.edit_message(embed=embed, view=None)
            return
        next_step = TUTORIAL_STEPS[step]
        embed = discord.Embed(title=next_step["title"], description=next_step["desc"], color=0x3498DB)
        embed.set_footer(text=f"教學進度：{step}/{len(TUTORIAL_STEPS)}")
        if reward_text:
            embed.add_field(name="🎁 上一步獎勵", value=reward_text, inline=False)
        await interaction.response.edit_message(embed=embed, view=TutorialView())


class TutorialView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=900)
        self.add_item(TutorialNextButton())


@bot.tree.command(name="新手教學", description="完成強制新手教學後解鎖完整遊戲功能")
async def new_player_tutorial(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    step = int(user.get("tutorial_step", 0))
    if bool(user.get("tutorial_completed", False)):
        await interaction.response.send_message("✅ 你已經完成新手教學，所有系統均已解鎖。", ephemeral=True)
        return
    if step >= len(TUTORIAL_STEPS):
        update_user(user_id, tutorial_completed=True)
        await interaction.response.send_message("✅ 新手教學已完成，所有系統已解鎖。", ephemeral=True)
        return
    step_data = TUTORIAL_STEPS[step]
    embed = discord.Embed(title=step_data["title"], description=step_data["desc"], color=0x3498DB)
    embed.add_field(name="📖 教學規則", value="完成全部步驟後才會解除遊戲功能鎖。此進度永久儲存在 MongoDB。", inline=False)
    embed.set_footer(text=f"教學進度：{step}/{len(TUTORIAL_STEPS)}")
    await interaction.response.send_message(embed=embed, view=TutorialView(), ephemeral=True)


def get_or_create_world_boss():
    boss = world_boss_col.find_one({"boss_id": "global_01"})
    if boss:
        return boss
    world_boss_col.insert_one(dict(WORLD_BOSS_DEFAULT))
    return world_boss_col.find_one({"boss_id": "global_01"})


def reset_world_boss_if_needed():
    boss = get_or_create_world_boss()
    if int(boss.get("hp", 0)) <= 0:
        now = time.time()
        world_boss_col.update_one(
            {"boss_id": "global_01"},
            {"$set": {"hp": int(boss["max_hp"]), "active": True, "rewarded": False, "last_reset": now}}
        )
        boss = world_boss_col.find_one({"boss_id": "global_01"})
    return boss


def get_world_boss_top(limit=10):
    boss = get_or_create_world_boss()
    round_id = int(boss.get("round", 1))
    docs = list(world_boss_col.find({"boss_id": "global_01", "type": "damage", "round": round_id}).sort("damage", -1).limit(limit))
    return docs


@bot.tree.command(name="鍛造", description="消耗魚獲與材料製作鍛造物品")
@app_commands.describe(配方="輸入要鍛造的配方名稱")
async def forge_cmd(interaction: discord.Interaction, 配方: str = ""):
    user_id = int(interaction.user.id)
    if not 配方:
        lines = []
        for name, recipe in FORGE_RECIPES.items():
            mat = "、".join(f"{k}×{v}" for k, v in recipe["materials"].items())
            lines.append(f"**{name}**\n材料：{mat}\n金幣：`{recipe['cost']:,}` 🪙\n{recipe['desc']}")
        embed = discord.Embed(title="⚒️ 鍛造工坊", description="\n\n".join(lines), color=0x8E44AD)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    recipe = FORGE_RECIPES.get(配方.strip())
    if not recipe:
        await interaction.response.send_message("❌ 找不到這個鍛造配方，請再次使用 `/鍛造` 查看配方。", ephemeral=True)
        return
    user = get_user(user_id)
    cost = int(recipe["cost"])
    if int(user.get("balance", 0)) < cost:
        await interaction.response.send_message(f"❌ 金幣不足，需要 `{cost:,}` 🪙。", ephemeral=True)
        return

    consumed = []
    try:
        for item_name, amount in recipe["materials"].items():
            if not consume_item_atomic(user_id, item_name, amount):
                raise RuntimeError(f"材料不足：{item_name}")
            consumed.append((item_name, amount))
        balance_result = users_col.update_one(
            {"user_id": user_id, "balance": {"$gte": cost}},
            {"$inc": {"balance": -cost}}
        )
        if balance_result.modified_count != 1:
            raise RuntimeError("扣款失敗")
        add_inventory(user_id, recipe["reward_item"], 1)
        forge_col.insert_one({"user_id": user_id, "recipe": 配方.strip(), "created_at": time.time()})
    except Exception as exc:
        for item_name, amount in consumed:
            add_inventory(user_id, item_name, amount)
        await interaction.response.send_message(f"❌ 鍛造失敗：{exc}", ephemeral=True)
        return

    await interaction.response.send_message(
        f"✅ **鍛造成功！**\n⚒️ 產物：**{recipe['reward_item']} ×1**\n💰 消耗：`{cost:,}` 🪙",
        ephemeral=True
    )


@bot.tree.command(name="探險", description="派出探險隊前往隨機海域，完成後領取金幣與材料")
async def adventure_cmd(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    active = adventure_col.find_one({"user_id": user_id, "status": "active"})
    now = time.time()
    if active:
        remaining = max(0, int(active["finish_at"] - now))
        if remaining > 0:
            await interaction.response.send_message(f"🧭 你目前正在探險中，剩餘約 `{remaining//60} 分 {remaining%60} 秒`。", ephemeral=True)
            return

    # 逾時完成的舊探險先自動結算
    if active and active.get("finish_at", 0) <= now:
        reward = active["reward"]
        add_inventory(user_id, reward["item"], int(reward["amount"]))
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": int(reward["gold"])}})
        adventure_col.update_one({"_id": active["_id"], "status": "active"}, {"$set": {"status": "completed", "completed_at": now}})
        await interaction.response.send_message(
            f"🎉 上次探險完成！\n📦 {reward['item']} ×{reward['amount']}\n💰 +{reward['gold']:,} 🪙\n\n再次使用 `/探險` 可出發新的旅程。",
            ephemeral=True
        )
        return

    total_weight = sum(x["weight"] for x in ADVENTURE_TABLE)
    roll = random.uniform(0, total_weight)
    selected = ADVENTURE_TABLE[-1]
    cursor = 0
    for area in ADVENTURE_TABLE:
        cursor += area["weight"]
        if roll <= cursor:
            selected = area
            break
    reward_item, reward_amount = random.choice(selected["rewards"])
    gold = random.randint(*selected["gold"])
    started = now
    finish = now + selected["minutes"] * 60
    adventure_col.insert_one({
        "user_id": user_id,
        "status": "active",
        "area": selected["name"],
        "start_at": started,
        "finish_at": finish,
        "reward": {"item": reward_item, "amount": int(reward_amount), "gold": int(gold)},
    })
    await interaction.response.send_message(
        f"🧭 **探險出發！**\n\n"
        f"地點：**{selected['name']}**\n"
        f"⏱️ 時間：`{selected['minutes']} 分鐘`\n"
        f"🎁 預計獎勵：{reward_item} ×{reward_amount}\n"
        f"💰 預計金幣：`{gold:,}`\n\n"
        f"完成後再次使用 `/探險` 即可領取。",
        ephemeral=True
    )


@bot.tree.command(name="世界boss", description="查看全服世界 Boss、傷害榜並進行一次攻擊")
async def world_boss_cmd(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    boss = reset_world_boss_if_needed()
    hp = max(0, int(boss.get("hp", 0)))
    max_hp = max(1, int(boss.get("max_hp", 1)))
    user = get_user(user_id)
    weapon_name = user.get("bait_type", "")
    weapon = WEAPONS_SHOP.get(weapon_name, {}) if isinstance(WEAPONS_SHOP, dict) else {}
    base_damage = int(weapon.get("dmg", 10)) if weapon else 10
    level_bonus = max(0, int(user.get("level", 0)) * 2)
    suggested = base_damage + level_bonus
    boss_percent = hp / max_hp * 100
    embed = discord.Embed(
        title=f"👹 {boss['name']}",
        description=f"❤️ HP：`{hp:,} / {max_hp:,}` ({boss_percent:.2f}%)\n⚔️ 你的單次預估傷害：`{suggested:,}`",
        color=0xC0392B,
    )
    top = get_world_boss_top(5)
    if top:
        embed.add_field(name="🏆 全服傷害榜", value="\n".join(f"{i+1}. <@{d.get('user_id')}> — `{int(d.get('damage',0)):,}`" for i, d in enumerate(top)), inline=False)
    embed.add_field(name="⚔️ 攻擊方法", value="再次使用 `/世界boss` 即可進行一次攻擊。世界 Boss HP 使用 MongoDB 原子扣血，避免多人覆蓋傷害。", inline=False)

    if hp <= 0:
        embed.description = "🏆 **Boss 已被全服擊破！正在進入新一輪重生。**"
        reset_world_boss_if_needed()
        await interaction.response.send_message(embed=embed)
        return

    damage = max(1, int(suggested * random.uniform(0.85, 1.15)))
    before_hp = hp
    updated = world_boss_col.find_one_and_update(
        {"boss_id": "global_01", "hp": {"$gt": 0}},
        {"$inc": {"hp": -damage}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        await interaction.response.send_message("⚠️ Boss 剛好被其他玩家擊破，請刷新後再戰。", ephemeral=True)
        return

    actual_damage = min(damage, before_hp)
    world_boss_col.update_one(
        {"boss_id": "global_01"},
        {"$inc": {"total_damage": actual_damage}},
    )
    boss_round = int(updated.get("round", boss.get("round", 1)))
    world_boss_col.update_one(
        {"boss_id": "global_01", "type": "damage", "round": boss_round, "user_id": user_id},
        {"$inc": {"damage": actual_damage}, "$set": {"updated_at": time.time()}},
        upsert=True,
    )
    new_hp = max(0, int(updated.get("hp", 0)))
    users_col.update_one({"user_id": user_id}, {"$inc": {"world_boss_damage": actual_damage}})

    reward_msg = ""
    if new_hp <= 0:
        reward_gold = 5000
        add_inventory(user_id, "🎁 傳奇藥水寶箱", 1)
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": reward_gold}})
        world_boss_col.update_one({"boss_id": "global_01"}, {"$set": {"rewarded": True, "active": False, "defeated_by": user_id, "defeated_at": time.time()}})
        reward_msg = f"\n\n🏆 **你完成了終結一擊！**\n💰 +{reward_gold:,} 🪙\n🎁 傳奇藥水寶箱 ×1"

    await interaction.response.send_message(
        f"⚔️ 你對 **{boss['name']}** 造成了 `{actual_damage:,}` 傷害！\n"
        f"❤️ Boss 剩餘 HP：`{new_hp:,} / {max_hp:,}`{reward_msg}"
    )


@bot.tree.command(name="血脈", description="查看與覺醒你的遠古血脈")
@app_commands.describe(目標血脈="留空查看目前血脈；填入血脈名稱可嘗試覺醒")
async def bloodline_cmd(interaction: discord.Interaction, 目標血脈: str = ""):
    user_id = int(interaction.user.id)
    user = get_user(user_id)
    current = user.get("race_type", "👤 常規人類")
    version = int(user.get("race_version", 1))

    if not 目標血脈:
        lines = [f"🧬 當前血脈：**{current} V{version}**"]
        for name, data in BLOODLINES.items():
            lines.append(f"\n**{name}**\n• 最高 V{data['max_version']}\n• 解鎖條件：{data['requirements']}\n• 首次費用：`{data['unlock_cost']:,}` 🪙\n• {data['desc']}")
        embed = discord.Embed(title="🧬 血脈神殿", description="".join(lines), color=0x9B59B6)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    target = 目標血脈.strip()
    if target not in BLOODLINES:
        await interaction.response.send_message("❌ 找不到指定血脈。請先使用 `/血脈` 查看完整血脈名冊。", ephemeral=True)
        return
    data = BLOODLINES[target]
    level = int(user.get("level", 0))
    if target == "🦈 深海鯊皇" and level < 20:
        await interaction.response.send_message("❌ 需要 LV.20 才能覺醒深海鯊皇。", ephemeral=True)
        return
    if target == "🧜 海妖" and level < 60:
        await interaction.response.send_message("❌ 需要 LV.60 才能覺醒海妖。", ephemeral=True)
        return
    if target == "🔱 亞特蘭提斯神族" and (level < 160 or user.get("current_map") != "三海_馬里亞娜海溝深淵"):
        await interaction.response.send_message("❌ 需要 LV.160 且位於三海才能覺醒亞特蘭提斯神族。", ephemeral=True)
        return
    cost = int(data["unlock_cost"] if target != current else max(5000, data["unlock_cost"] // 2))
    current_version = version if current == target else 0
    next_version = 1 if current != target else current_version + 1
    if next_version > int(data["max_version"]):
        await interaction.response.send_message("✅ 你的這條血脈已達最高階。", ephemeral=True)
        return
    if int(user.get("balance", 0)) < cost:
        await interaction.response.send_message(f"❌ 金幣不足，需要 `{cost:,}` 🪙。", ephemeral=True)
        return
    changed = users_col.update_one(
        {"user_id": user_id, "balance": {"$gte": cost}},
        {"$inc": {"balance": -cost}, "$set": {"race_type": target, "race_version": next_version}}
    )
    if changed.modified_count != 1:
        await interaction.response.send_message("❌ 覺醒扣款失敗，這次操作未成立。", ephemeral=True)
        return
    await interaction.response.send_message(
        f"🧬 **血脈覺醒成功！**\n"
        f"{current} V{version} → **{target} V{next_version}**\n"
        f"💰 消耗：`{cost:,}` 🪙"
    )


def create_auction_embed():
    now = time.time()
    auctions = list(auction_col.find({"status": "active", "end_at": {"$gt": now}}).sort([("current_bid", 1), ("end_at", 1)]).limit(15))
    if not auctions:
        return discord.Embed(title="🔨 玩家拍賣場", description="目前沒有進行中的拍賣。\n使用 `/建立拍賣` 發起第一筆拍賣。", color=0xE67E22)
    lines = []
    for a in auctions:
        remain = max(0, int(a["end_at"] - now))
        bidder = f"<@{a['current_bidder']}>" if a.get("current_bidder") else "尚無出價"
        lines.append(
            f"`{a['auction_code']}` **{a['item_name']} ×{a['quantity']}**\n"
            f"起標：`{a['start_bid']:,}`｜目前：`{a['current_bid']:,}`｜最高出價者：{bidder}\n"
            f"剩餘：`{remain//60}分{remain%60}秒`｜賣家：<@{a['seller_id']}>"
        )
    return discord.Embed(title="🔨 玩家拍賣場", description="\n\n".join(lines), color=0xE67E22)


def generate_auction_code():
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(50):
        code = "A" + "".join(random.choice(chars) for _ in range(7))
        if auction_col.find_one({"auction_code": code}) is None:
            return code
    raise RuntimeError("無法產生拍賣代碼")


@bot.tree.command(name="拍賣場", description="查看玩家競標中的物品與剩餘時間")
async def auction_house_cmd(interaction: discord.Interaction):
    embed = create_auction_embed()
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="建立拍賣", description="把背包中的物品放入限時競標拍賣場")
@app_commands.describe(物品名稱="背包中的物品名稱", 數量="拍賣數量", 起標價="起標總價", 分鐘="拍賣持續時間，10~1440 分鐘")
async def create_auction_cmd(interaction: discord.Interaction, 物品名稱: str, 數量: int, 起標價: int, 分鐘: int = 60):
    user_id = int(interaction.user.id)
    item_name = 物品名稱.strip()
    數量 = int(數量)
    起標價 = int(起標價)
    分鐘 = max(10, min(int(分鐘), 1440))
    if 數量 < 1 or 起標價 < 1:
        await interaction.response.send_message("❌ 數量與起標價必須大於 0。", ephemeral=True)
        return
    if get_item_count(user_id, item_name) < 數量:
        await interaction.response.send_message("❌ 你的背包沒有足夠物品。", ephemeral=True)
        return
    if not consume_item_atomic(user_id, item_name, 數量):
        await interaction.response.send_message("❌ 物品剛被其他操作消耗，請刷新背包。", ephemeral=True)
        return
    code = generate_auction_code()
    now = time.time()
    try:
        auction_col.insert_one({
            "auction_code": code,
            "seller_id": user_id,
            "item_name": item_name,
            "quantity": 數量,
            "start_bid": 起標價,
            "current_bid": 起標價,
            "current_bidder": None,
            "status": "active",
            "created_at": now,
            "end_at": now + 分鐘 * 60,
        })
    except Exception:
        add_inventory(user_id, item_name, 數量)
        raise
    await interaction.response.send_message(
        f"✅ **拍賣建立成功！**\n🔨 代碼：`{code}`\n📦 {item_name} ×{數量}\n💰 起標價：`{起標價:,}`\n⏱️ 持續：`{分鐘} 分鐘`"
    )


@bot.tree.command(name="競標", description="對指定拍賣出價；前一位最高出價者會自動退回金幣")
@app_commands.describe(拍賣代碼="拍賣場中的 8 碼代碼", 出價="新的總出價，必須高於目前出價")
async def bid_auction_cmd(interaction: discord.Interaction, 拍賣代碼: str, 出價: int):
    user_id = int(interaction.user.id)
    code = 拍賣代碼.strip().upper()
    出價 = int(出價)
    now = time.time()
    auction = auction_col.find_one({"auction_code": code, "status": "active"})
    if not auction:
        await interaction.response.send_message("❌ 找不到有效拍賣。", ephemeral=True)
        return
    if auction["seller_id"] == user_id:
        await interaction.response.send_message("❌ 賣家不能自己競標自己的拍賣。", ephemeral=True)
        return
    if now >= float(auction["end_at"]):
        await interaction.response.send_message("❌ 拍賣已截止，請使用 `/結算拍賣`。", ephemeral=True)
        return
    current_bid = int(auction.get("current_bid", auction["start_bid"]))
    if 出價 <= current_bid:
        await interaction.response.send_message(f"❌ 你的出價必須高於目前 ` {current_bid:,} ` 🪙。", ephemeral=True)
        return
    user = get_user(user_id)
    if int(user.get("balance", 0)) < 出價:
        await interaction.response.send_message(f"❌ 你的金幣不足，需要至少 `{出價:,}` 🪙。", ephemeral=True)
        return

    # 原子地搶下最高出價欄位，避免兩名玩家同時覆蓋彼此。
    updated = auction_col.find_one_and_update(
        {"_id": auction["_id"], "status": "active", "current_bid": current_bid},
        {"$set": {"current_bid": 出價, "current_bidder": user_id, "last_bid_at": now}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        await interaction.response.send_message("❌ 有其他玩家同時出價成功，請重新查看拍賣場。", ephemeral=True)
        return

    charged = users_col.update_one({"user_id": user_id, "balance": {"$gte": 出價}}, {"$inc": {"balance": -出價}})
    if charged.modified_count != 1:
        auction_col.update_one(
            {"_id": auction["_id"], "current_bidder": user_id, "current_bid": 出價},
            {"$set": {"current_bid": current_bid, "current_bidder": auction.get("current_bidder")}},
        )
        await interaction.response.send_message("❌ 扣款失敗，這次競標未成立。", ephemeral=True)
        return

    previous_bidder = auction.get("current_bidder")
    if previous_bidder:
        users_col.update_one({"user_id": int(previous_bidder)}, {"$inc": {"balance": current_bid}})
    await interaction.response.send_message(
        f"✅ **競標成功！**\n🔨 `{code}`\n💰 你的最高出價：`{出價:,}` 🪙\n"
        f"前一位出價者已退回 `{current_bid:,}` 🪙。"
    )


@bot.tree.command(name="結算拍賣", description="結算已到期拍賣；得標者取得物品，賣家取得金幣")
@app_commands.describe(拍賣代碼="拍賣場中的 8 碼代碼")
async def settle_auction_cmd(interaction: discord.Interaction, 拍賣代碼: str):
    code = 拍賣代碼.strip().upper()
    auction = auction_col.find_one({"auction_code": code, "status": "active"})
    if not auction:
        await interaction.response.send_message("❌ 找不到有效拍賣。", ephemeral=True)
        return
    if time.time() < float(auction["end_at"]):
        await interaction.response.send_message("⏳ 拍賣尚未截止，還不能結算。", ephemeral=True)
        return
    closed = auction_col.find_one_and_update(
        {"_id": auction["_id"], "status": "active", "end_at": {"$lte": time.time()}},
        {"$set": {"status": "settled", "settled_at": time.time()}},
        return_document=ReturnDocument.AFTER,
    )
    if not closed:
        await interaction.response.send_message("❌ 這筆拍賣正在被其他人結算。", ephemeral=True)
        return

    bidder = closed.get("current_bidder")
    if bidder:
        final_bid = int(closed["current_bid"])
        auction_tax = int(final_bid * 0.10)
        seller_net = final_bid - auction_tax
        add_inventory(int(bidder), closed["item_name"], int(closed["quantity"]))
        users_col.update_one({"user_id": int(closed["seller_id"])}, {"$inc": {"balance": seller_net}})
        await interaction.response.send_message(
            f"🏆 **拍賣結算完成！**\n"
            f"📦 {closed['item_name']} ×{closed['quantity']} → <@{bidder}>\n"
            f"💰 成交價：`{final_bid:,}` 🪙\n"
            f"🏛️ 官方 10% 拍賣稅：`{auction_tax:,}` 🪙\n"
            f"💵 賣家實收：`{seller_net:,}` 🪙"
        )
    else:
        add_inventory(int(closed["seller_id"]), closed["item_name"], int(closed["quantity"]))
        await interaction.response.send_message("🔨 本次拍賣無人出價，物品已退回賣家背包。")


# 將所有現有 Slash Command 套上全域新手保護鎖。
# `/新手教學` 與 `/幫助` 永遠開放，其餘指令在 tutorial_completed=True 前會被阻擋。
def install_tutorial_gate():
    for cmd in bot.tree.get_commands():
        if getattr(cmd, "name", None) in {"新手教學", "幫助"}:
            continue
        try:
            cmd.add_check(tutorial_gate)
        except AttributeError:
            print(f"[TUTORIAL] 無法套用指令檢查：{getattr(cmd, 'name', 'unknown')}")


install_tutorial_gate()
# ======= 🧭 新架構 V6 結束 =======

keep_alive()
DISCORD_CODE = os.getenv("DISCORD_TOKEN")
bot.run(DISCORD_CODE)
