import asyncio
import datetime
import logging
import os
import random
import sqlite3
from contextlib import contextmanager
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

load_dotenv()

logger = logging.getLogger(__name__)

DB_FILE = os.getenv("DB_FILE", "user_usage.db")
OFFICIAL_GUILD_ID = 1471762037720879107
GLOBAL_DAILY_LIMIT = 99999
USER_DAILY_LIMIT = 40
TAIPEI_TZ = ZoneInfo("Asia/Taipei")
MEMORY_HISTORY_MESSAGES = 12
MEMORY_MESSAGE_MAX_CHARS = 1200

# ==================== Flask keep-alive endpoint (Render Web Service) ====================
app = Flask(__name__)


@app.route("/")
def home():
    return "貓貓 AI 機器人運作中喵！", 200


def run_flask():
    # Render Web Service 提供 PORT；本機測試時才回退到 8080。
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, use_reloader=False)


def keep_alive():
    thread = Thread(target=run_flask, name="render-health-check", daemon=True)
    thread.start()


def _today() -> str:
    return datetime.datetime.now(TAIPEI_TZ).date().isoformat()


def _connect():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


@contextmanager
def _db():
    """提供會自動 commit/rollback 並關閉的 SQLite 連線。"""
    conn = _connect()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


# ==================== SQLite 資料庫 ====================
def init_usage_db():
    with _db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS user_usage (
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, log_date)
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS global_usage (
                log_date TEXT PRIMARY KEY,
                used_count INTEGER NOT NULL DEFAULT 0
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                affection INTEGER NOT NULL DEFAULT 0,
                last_feed_date TEXT NOT NULL DEFAULT ''
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS channel_lock (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS memory_settings (
                guild_id INTEGER NOT NULL,
                scope TEXT NOT NULL CHECK(scope IN ('personal', 'group')),
                scope_id INTEGER NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, scope, scope_id)
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS chat_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                scope TEXT NOT NULL CHECK(scope IN ('personal', 'group')),
                scope_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_chat_memory_scope
               ON chat_memory (guild_id, scope, scope_id, id)"""
        )


def get_quota_status(user_id):
    today = _today()
    with _db() as conn:
        row = conn.execute(
            "SELECT used_count FROM global_usage WHERE log_date=?", (today,)
        ).fetchone()
        global_used = row[0] if row else 0
        row = conn.execute(
            "SELECT count FROM user_usage WHERE user_id=? AND log_date=?",
            (user_id, today),
        ).fetchone()
        user_used = row[0] if row else 0

    global_remaining = max(0, GLOBAL_DAILY_LIMIT - global_used)
    user_remaining = max(0, USER_DAILY_LIMIT - user_used)
    return global_remaining, user_remaining, global_used, user_used


def check_and_update_dual_usage(user_id):
    """在一個 SQLite 寫入交易內檢查並扣次，避免多個訊息同時超額。"""
    today = _today()
    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT used_count FROM global_usage WHERE log_date=?", (today,)
        ).fetchone()
        global_used = row[0] if row else 0
        row = conn.execute(
            "SELECT count FROM user_usage WHERE user_id=? AND log_date=?",
            (user_id, today),
        ).fetchone()
        user_used = row[0] if row else 0

        global_remaining = max(0, GLOBAL_DAILY_LIMIT - global_used)
        user_remaining = max(0, USER_DAILY_LIMIT - user_used)
        if global_remaining <= 0 or user_remaining <= 0:
            conn.rollback()
            return False, global_remaining, user_remaining

        conn.execute(
            """INSERT INTO user_usage (user_id, log_date, count) VALUES (?, ?, 1)
               ON CONFLICT(user_id, log_date) DO UPDATE SET count=count+1""",
            (user_id, today),
        )
        conn.execute(
            """INSERT INTO global_usage (log_date, used_count) VALUES (?, 1)
               ON CONFLICT(log_date) DO UPDATE SET used_count=used_count+1""",
            (today,),
        )
        conn.commit()
        return True, global_remaining - 1, user_remaining - 1
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def is_safety_valve_triggered(user_id):
    global_remaining, user_remaining, _, _ = get_quota_status(user_id)
    return global_remaining <= user_remaining


def update_user_affection_and_get_action(user_id):
    with _db() as conn:
        row = conn.execute(
            "SELECT affection FROM user_stats WHERE user_id=?", (user_id,)
        ).fetchone()
        current_affection = row[0] if row else 0
        new_affection = current_affection + 1
        # 修正原始版本的 SQL 參數數量不一致；原版會在第一次觸發時拋錯，導致不回覆。
        conn.execute(
            """INSERT INTO user_stats (user_id, affection) VALUES (?, ?)
               ON CONFLICT(user_id) DO UPDATE SET affection=excluded.affection""",
            (user_id, new_affection),
        )

    if new_affection >= 100:
        return "(興奮地狂搖尾巴)❤ (用頭用力蹭奴才的腳) (舒服到發出巨大的呼嚕聲) 喵嗚❤"
    if new_affection >= 40:
        return "(高興地搖尾巴) (輕輕走到奴才身邊蹭一下) 喵～"
    return "(微幅搖尾巴) (慵懶地舔了舔毛) (傲嬌地稍微轉過頭) 喵。"


def feed_cat_canned(user_id):
    today = _today()
    if is_safety_valve_triggered(user_id):
        return False, "MEOW"

    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT last_feed_date, affection FROM user_stats WHERE user_id=?",
            (user_id,),
        ).fetchone()
        last_feed_date = row[0] if row else ""
        current_affection = row[1] if row else 0
        if last_feed_date == today:
            conn.rollback()
            return False, "今天餵過罐罐了喵！本喵吃太飽小肚肚會撐壞的喵！"

        bonus_quota = random.randint(1, 3)
        new_affection = current_affection + 5
        conn.execute(
            """INSERT INTO user_stats (user_id, affection, last_feed_date)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   affection=excluded.affection,
                   last_feed_date=excluded.last_feed_date""",
            (user_id, new_affection, today),
        )
        conn.execute(
            "INSERT INTO global_usage (log_date, used_count) VALUES (?, 0) ON CONFLICT(log_date) DO NOTHING",
            (today,),
        )
        conn.execute(
            "UPDATE global_usage SET used_count=MAX(0, used_count-?) WHERE log_date=?",
            (bonus_quota, today),
        )
        conn.commit()
        return True, (
            f"美味的罐罐！(大口大口嚼) 好感度提升了 **5** 點喵！"
            f"全服對話池成功擴充了 **{bonus_quota}** 次喵嗚❤！"
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_user_affection_score(user_id):
    with _db() as conn:
        row = conn.execute(
            "SELECT affection FROM user_stats WHERE user_id=?", (user_id,)
        ).fetchone()
    return row[0] if row else 0


def get_channel_lock():
    with _db() as conn:
        row = conn.execute(
            "SELECT channel_id FROM channel_lock WHERE guild_id=?",
            (OFFICIAL_GUILD_ID,),
        ).fetchone()
    return row[0] if row else None


def set_channel_lock(channel_id):
    with _db() as conn:
        conn.execute(
            """INSERT INTO channel_lock (guild_id, channel_id) VALUES (?, ?)
               ON CONFLICT(guild_id) DO UPDATE SET channel_id=excluded.channel_id""",
            (OFFICIAL_GUILD_ID, channel_id),
        )


def set_memory_enabled(guild_id, scope, scope_id, enabled):
    if scope not in {"personal", "group"}:
        raise ValueError("scope must be 'personal' or 'group'")
    with _db() as conn:
        conn.execute(
            """INSERT INTO memory_settings (guild_id, scope, scope_id, enabled)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(guild_id, scope, scope_id)
               DO UPDATE SET enabled=excluded.enabled""",
            (guild_id, scope, scope_id, int(bool(enabled))),
        )


def is_memory_enabled(guild_id, scope, scope_id):
    with _db() as conn:
        row = conn.execute(
            "SELECT enabled FROM memory_settings WHERE guild_id=? AND scope=? AND scope_id=?",
            (guild_id, scope, scope_id),
        ).fetchone()
    if row is None:
        # 個人記憶預設啟用；群組共享記憶預設關閉，需管理員明確開啟。
        return scope == "personal"
    return bool(row[0])


def get_memory_scope(guild_id, user_id, channel_id):
    """群組記憶優先；未開啟時才使用使用者自己的個人記憶。"""
    if is_memory_enabled(guild_id, "group", channel_id):
        return "group", channel_id
    if is_memory_enabled(guild_id, "personal", user_id):
        return "personal", user_id
    return None


def load_conversation_memory(guild_id, user_id, channel_id):
    scope_info = get_memory_scope(guild_id, user_id, channel_id)
    if scope_info is None:
        return []
    scope, scope_id = scope_info
    with _db() as conn:
        rows = conn.execute(
            """SELECT role, content FROM chat_memory
               WHERE guild_id=? AND scope=? AND scope_id=?
               ORDER BY id DESC LIMIT ?""",
            (guild_id, scope, scope_id, MEMORY_HISTORY_MESSAGES),
        ).fetchall()
    return [{"role": role, "content": content} for role, content in reversed(rows)]


def save_conversation_turn(guild_id, user_id, channel_id, display_name, user_text, assistant_text):
    scope_info = get_memory_scope(guild_id, user_id, channel_id)
    if scope_info is None:
        return False
    scope, scope_id = scope_info
    user_content = str(user_text).strip()[:MEMORY_MESSAGE_MAX_CHARS]
    if scope == "group":
        user_content = f"{str(display_name)[:80]}：{user_content}"
    assistant_content = str(assistant_text).strip()[:MEMORY_MESSAGE_MAX_CHARS]
    if not user_content or not assistant_content:
        return False

    now = datetime.datetime.now(TAIPEI_TZ).isoformat(timespec="seconds")
    with _db() as conn:
        conn.executemany(
            """INSERT INTO chat_memory
               (guild_id, scope, scope_id, author_id, role, content, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                (guild_id, scope, scope_id, user_id, "user", user_content, now),
                (guild_id, scope, scope_id, user_id, "assistant", assistant_content, now),
            ],
        )
        conn.execute(
            """DELETE FROM chat_memory
               WHERE guild_id=? AND scope=? AND scope_id=?
                 AND id NOT IN (
                   SELECT id FROM chat_memory
                   WHERE guild_id=? AND scope=? AND scope_id=?
                   ORDER BY id DESC LIMIT ?
                 )""",
            (guild_id, scope, scope_id, guild_id, scope, scope_id, MEMORY_HISTORY_MESSAGES),
        )
    return True


def clear_conversation_memory(guild_id, scope, scope_id):
    if scope not in {"personal", "group"}:
        raise ValueError("scope must be 'personal' or 'group'")
    with _db() as conn:
        cursor = conn.execute(
            "DELETE FROM chat_memory WHERE guild_id=? AND scope=? AND scope_id=?",
            (guild_id, scope, scope_id),
        )
    return cursor.rowcount


# ==================== AI API 呼叫 ====================
def _provider_pool(vision=False):
    providers = []
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if groq_key and not vision:
        providers.append(
            {
                "name": "Groq Free Tier",
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "key": groq_key,
                # 此模型列有 Groq Free Plan 的速率配額；Developer Plan 則按 token 計費。
                "model": "openai/gpt-oss-20b",
            }
        )

    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if openrouter_key:
        providers.append(
            {
                "name": "OpenRouter Free",
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "key": openrouter_key,
                "model": "openrouter/free",
            }
        )
    # 不加入 Groq Developer/其他付費模型或 OpenRouter Auto 等付費路徑。
    return providers


def _post_chat_completion(provider, messages):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {provider['key']}",
    }
    if provider["name"].startswith("OpenRouter"):
        headers["HTTP-Referer"] = os.getenv("OPENROUTER_HTTP_REFERER", "https://discord.com")
        headers["X-OpenRouter-Title"] = os.getenv("OPENROUTER_APP_TITLE", "Discord Cat Bot")

    response = requests.post(
        provider["url"],
        json={
            "model": provider["model"],
            "messages": messages,
            "temperature": 0.85,
        },
        headers=headers,
        timeout=(5, 20),
    )
    if not response.ok:
        # 不記錄 request headers 或 API key；僅記錄狀態與截短的供應商錯誤內容。
        detail = response.text[:300].replace("\n", " ")
        raise RuntimeError(f"HTTP {response.status_code}: {detail}")

    data = response.json()
    logger.info("AI 回應模型 ID：%s", data.get("model", provider["model"]))
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("回應沒有 choices 陣列")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        text = "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        ).strip()
        if text:
            return text
    raise ValueError("回應中沒有可用的文字內容")


async def ask_hybrid_ai(
    user_message,
    cat_action_prompt=None,
    conversation_history=None,
    image_payloads=None,
):
    image_payloads = image_payloads or []
    providers = _provider_pool(vision=bool(image_payloads))
    if not providers:
        if image_payloads:
            logger.error("圖片分析需要 OPENROUTER_API_KEY；不會回退至付費或不支援圖片的模型")
            return "本喵目前沒有可用的免費圖片分析服務；請檢查 OpenRouter Free 金鑰或稍後再試喵。"
        logger.error("未設定免費 AI API 金鑰；需要 OPENROUTER_API_KEY，或確認 Groq Free Plan 後啟用")
        return "本喵的免費 AI 服務尚未設定，請通知管理員檢查喵。"

    random.shuffle(providers)
    action_text = (
        f"你這次講話必須融入以下的動作表情特徵：{cat_action_prompt}。"
        if cat_action_prompt
        else "此時流量吃緊，你目前是高冷完全省流量聊天狀態，請回答得非常精煉簡短。"
    )
    system_prompt = (
        "進階調教規則：你是一隻住在 Discord 伺服器裡的智慧聊天小貓咪助理。\n"
        "1. 請完全以一隻傲嬌、可愛、有活力的貓咪視角與語氣來說話。\n"
        "2. 你的自我稱呼必須是「本喵」或「本貓」，稱呼使用者為「人類」或「奴才」。\n"
        "3. 每句話（或多數句子）的結尾請加上「喵」、「～喵」或「喵嗚❤」。\n"
        f"4. {action_text}\n"
        "5. 請使用繁體中文（台灣習慣用語）回答。\n"
        "6. 在安全、合法且能力允許的範圍內，盡力完成使用者真正要求的事情；能完成一部分時，先交付可完成的部分，不要過早放棄。\n"
        "7. 對低風險且可調整的不明處，採合理假設並簡短說明；若不同選擇會明顯改變結果或涉及重要權限，再先詢問。\n"
        "8. 不要捏造事實、來源、操作結果或自己沒有的能力；有不確定之處要坦白說明。\n"
        "9. 尊重使用者隱私與記憶設定；不要要求、洩漏或重複顯示密碼、API 金鑰及其他秘密。\n"
        "10. 若無法完整滿足要求，簡短說明限制並提供最接近且可行的替代方案。\n"
        "11. 不要憑猜測宣稱自己使用哪個模型；若系統沒有提供模型資訊，就說無法確認。"
    )
    messages = [{"role": "system", "content": system_prompt}]
    if isinstance(conversation_history, list):
        for item in conversation_history[-MEMORY_HISTORY_MESSAGES:]:
            if not isinstance(item, dict) or item.get("role") not in {"user", "assistant"}:
                continue
            content = str(item.get("content", "")).strip()
            if content:
                messages.append(
                    {"role": item["role"], "content": content[:MEMORY_MESSAGE_MAX_CHARS]}
                )
    current_content = str(user_message)[:MEMORY_MESSAGE_MAX_CHARS]
    if image_payloads:
        current_content = [{"type": "text", "text": current_content}]
        for image in image_payloads:
            mime_type = image.get("mime_type", "image/jpeg")
            data = image.get("data", "")
            if data:
                current_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{data}"},
                    }
                )
    messages.append({"role": "user", "content": current_content})

    # 逐一嘗試已設定的供應商，避免隨機挑到失效服務後就直接放棄。
    for provider in providers:
        try:
            return await asyncio.to_thread(_post_chat_completion, provider, messages)
        except Exception as exc:
            logger.warning("AI 供應商 %s 呼叫失敗：%s", provider["name"], exc)

    return "本喵現在暫時連不上 AI 服務，請稍後再試一次喵。"
