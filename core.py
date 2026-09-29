import os
import sys
import datetime
import sqlite3
import random
from flask import Flask
from threading import Thread
import requests
from dotenv import load_dotenv

load_dotenv()

DB_FILE = "user_usage.db"
OFFICIAL_GUILD_ID = 1546517053719060642

# 全服每日總上限解放至 99,999 次（體感無限用量）
GLOBAL_DAILY_LIMIT = 99999
USER_DAILY_LIMIT = 40

# ==================== 🌐 Flask 24h 不休息監聽 ====================
app = Flask('')

@app.route('/')
def home():
    return "貓貓 AI 四核心負載平衡安全閥版正在 24h 穩定運作中喵！"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ==================== 💾 資料庫核心 ====================
def init_usage_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_usage (
        user_id INTEGER, log_date TEXT, count INTEGER DEFAULT 0, PRIMARY KEY (user_id, log_date)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS global_usage (
        log_date TEXT PRIMARY KEY, used_count INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_stats (
        user_id PRIMARY KEY, affection INTEGER DEFAULT 0, last_feed_date TEXT DEFAULT ''
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS channel_lock (
        guild_id INTEGER PRIMARY KEY, channel_id INTEGER
    )''')
    conn.commit()
    conn.close()

def get_quota_status(user_id):
    today = datetime.date.today().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("SELECT used_count FROM global_usage WHERE log_date=?", (today,))
    g_res = c.fetchone()
    g_used = g_res[0] if g_res else 0
    g_remain = max(0, GLOBAL_DAILY_LIMIT - g_used)
    
    c.execute("SELECT count FROM user_usage WHERE user_id=? AND log_date=?", (user_id, today))
    u_res = c.fetchone()
    u_used = u_res[0] if u_res else 0
    u_remain = max(0, USER_DAILY_LIMIT - u_used)
    
    conn.close()
    return g_remain, u_remain, g_used, u_used

def check_and_update_dual_usage(user_id):
    today = datetime.date.today().isoformat()
    g_remain, u_remain, g_used, u_used = get_quota_status(user_id)
    
    if u_remain <= 0 or g_remain <= 0:
        return False, g_remain, u_remain
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO user_usage (user_id, log_date, count) VALUES (?, ?, 1)
                 ON CONFLICT(user_id, log_date) DO UPDATE SET count = count + 1''', (user_id, today))
    c.execute('''INSERT INTO global_usage (log_date, used_count) VALUES (?, 1)
                 ON CONFLICT(log_date) DO UPDATE SET used_count = used_count + 1''', (today,))
    conn.commit()
    conn.close()
    return True, g_remain - 1, u_remain - 1

def is_safety_valve_triggered(user_id):
    g_remain, u_remain, _, _ = get_quota_status(user_id)
    return u_remain >= g_remain

def update_user_affection_and_get_action(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT affection FROM user_stats WHERE user_id=?", (user_id,))
    res = c.fetchone()
    current_aff = res[0] if res else 0
    
    new_aff = current_aff + 1
    c.execute('''INSERT INTO user_stats (user_id, affection) VALUES (?, 1)
                 ON CONFLICT(user_id) DO UPDATE SET affection=?''', (user_id, new_aff, new_aff))
    conn.commit()
    conn.close()
    
    if new_aff >= 100:
        return "(興奮地狂搖尾巴)❤ (用頭用力蹭奴才的腳) (舒服到發出巨大的呼嚕聲) 喵嗚❤"
    elif new_aff >= 40:
        return "(高興地搖尾巴) (輕輕走到奴才身邊蹭一下) 喵～"
    else:
        return "(微幅搖尾巴) (慵懶地舔了舔毛) (傲嬌地稍微轉過頭) 喵。"

def feed_cat_canned(user_id):
    today = datetime.date.today().isoformat()
    
    if is_safety_valve_triggered(user_id):
        return False, "MEOW"

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT last_feed_date, affection FROM user_stats WHERE user_id=?", (user_id,))
    res = c.fetchone()
    
    last_feed = res[0] if res else ""
    current_aff = res[1] if res else 0
    
    if last_feed == today:
        conn.close()
        return False, "今天餵過罐罐了喵！本喵吃太飽小肚肚會撐壞的喵！"
        
    bonus_quota = random.randint(1, 3)
    new_aff = current_aff + 5
    c.execute('''INSERT INTO user_stats (user_id, affection, last_feed_date) VALUES (?, 5, ?)
                 ON CONFLICT(user_id) DO UPDATE SET affection=?, last_feed_date=?''', (user_id, today, new_aff, today))
    
    c.execute("SELECT used_count FROM global_usage WHERE log_date=?", (today,))
    usage_res = c.fetchone()
    current_used = usage_res[0] if usage_res else 0
    
    new_used = max(0, current_used - bonus_quota)
    c.execute('''INSERT INTO global_usage (log_date, used_count) VALUES (?, 0)
                 ON CONFLICT(log_date) DO UPDATE SET used_count=?''', (today, new_used, new_used))
    
    conn.commit()
    conn.close()
    return True, f"美味的罐罐！(大口大口嚼) 好感度提升了 **5** 點喵！全服對話池成功擴充了 **{bonus_quota}** 次喵嗚❤！"

def get_user_affection_score(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT affection FROM user_stats WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0

def get_channel_lock():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT channel_id FROM channel_lock WHERE guild_id=?", (OFFICIAL_GUILD_ID,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

# ==================== 🧠 跨公司 AI 四核心智能調度引擎 ====================
def ask_hybrid_ai(user_message, cat_action_prompt=None):
    api_pool = []

    # 核心 1. Groq (Llama 3.3)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and groq_key.strip():
        api_pool.append({
            "type": "standard_openai",
            "url": "https://groq.com",
            "key": groq_key.strip(),
            "model": "llama-3.3-70b-versatile"
        })

    # 核心 2. OpenRouter (Auto Free Pool)
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key and openrouter_key.strip():
        api_pool.append({
            "type": "standard_openai",
            "url": "https://openrouter.ai",
            "key": openrouter_key.strip(),
            "model": "openrouter/auto"
        })

    # 核心 3. GitHub Models (GPT-4o-mini)
    github_key = os.getenv("GITHUB_TOKEN")
    if github_key and github_key.strip():
        api_pool.append({
            "type": "standard_openai",
            "url": "https://azure.com",
            "key": github_key.strip(),
            "model": "gpt-4o-mini"
        })

    # 核心 4. Pollinations AI (無金鑰保底通道)
    api_pool.append({
        "type": "pollinations_anonymous",
        "url": "https://pollinations.ai",
        "model": "openai"
    })

    provider = random.choice(api_pool)
    
    action_str = f"你這次講話必須融入以下的動作表情特徵：{cat_action_prompt}。" if cat_action_prompt else "此時流量吃緊，你目前是高冷完全省流量聊天狀態，請回答得非常精煉簡短。"
    
    cat_system_prompt = (
        "進階調教規則：你是一隻住在 Discord 伺服器裡的智慧聊天小貓咪助理。\n"
        "1. 請完全以一隻傲嬌、可愛、有活力的貓咪視角 and 語氣來說話。\n"
        "2. 你的自我稱呼必須是「本喵」或「本貓」，稱呼使用者為「人類」或「奴才」。\n"
        "3. 你的每句話（或是多數句子）的結尾，都必須加上「喵」、「～喵」或「喵嗚❤」。\n"
        f"4. {action_str}\n"
        "5. 請使用繁體中文（台灣習慣用語）回答。"
    )

    try:
        if provider["type"] == "standard_openai":
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {provider['key']}"}
            payload = {
                "model": provider["model"],
                "messages": [
                    {"role": "system", "content": cat_system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.85
            }
            response = requests.post(provider["url"], json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                return response.json()["choices"]["message"]["content"]
        
        elif provider["type"] == "pollinations_anonymous":
            headers = {"Content-Type": "application/json"}
            payload = {
                "messages": [
                    {"role": "system", "content": cat_system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "model": provider["model"],
                "jsonMode": False
            }
            response = requests.post(provider["url"], json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                return response.text
        
        return "MEOW"
    except Exception:
        return "MEOW"