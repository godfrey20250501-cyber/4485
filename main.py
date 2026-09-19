import asyncio
import re
import unicodedata
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands, tasks
from discord import app_commands
from pymongo import MongoClient


# ============================================================
# ======================== 基本設定 ==========================
# ============================================================

DISCORD_CODE = "YOUR_BOT_TOKEN"

MONGO_URI = "YOUR_MONGODB_ATLAS_URI"
DATABASE_NAME = "fishing_game"

# 指定「違規審核」頻道 ID
MODERATION_CHANNEL_ID = 123456789012345678

# 四種身份組 ID
WARNING_ROLE_ID = 123456789012345678
MINOR_ROLE_ID = 123456789012345678
MEDIUM_ROLE_ID = 123456789012345678
MAJOR_ROLE_ID = 123456789012345678

# 取得這個身份組後自動 BAN
BAN_ROLE_ID = 123456789012345678

# 管理員身份組
MODERATOR_ROLE_ID = 123456789012345678

# 是否偵測到違規後刪除原訊息
DELETE_VIOLATION_MESSAGE = False

# 處分等待時間
ACTION_DELAY = 60


# ============================================================
# ======================== MongoDB ===========================
# ============================================================

mongo = MongoClient(MONGO_URI)

db = mongo[DATABASE_NAME]

moderation_cases_col = db["moderation_cases"]
moderation_records_col = db["moderation_records"]
moderation_settings_col = db["moderation_settings"]


# ============================================================
# ======================== Discord ===========================
# ============================================================

intents = discord.Intents.default()

intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# ======================== 詞庫 ==============================
# ============================================================

PROFANITY_WORDS = {
    "幹",
    "操",
    "靠北",
    "媽的",
    "他媽的",
    "白癡",
    "智障",
}

SENSITIVE_WORDS = {
    "敏感詞",
    "違規詞",
}


# ============================================================
# ======================== 工具函數 ==========================
# ============================================================

def utc_now():
    return datetime.now(timezone.utc)


def normalize_text(text: str) -> str:
    """
    將文字標準化，降低使用者用特殊符號繞過偵測的機率。
    """

    text = unicodedata.normalize("NFKC", text)

    text = text.lower()

    # 移除常見空白
    text = re.sub(r"[\s\u200b\u200c\u200d]+", "", text)

    # 移除部分常見分隔符
    text = re.sub(r"[_\-~`*|｜·・]+", "", text)

    return text


def detect_violation(text: str):
    normalized = normalize_text(text)

    matched_profanity = []
    matched_sensitive = []

    for word in PROFANITY_WORDS:
        if word in normalized:
            matched_profanity.append(word)

    for word in SENSITIVE_WORDS:
        if word in normalized:
            matched_sensitive.append(word)

    if matched_profanity:
        return {
            "category": "profanity",
            "matched_words": matched_profanity
        }

    if matched_sensitive:
        return {
            "category": "sensitive",
            "matched_words": matched_sensitive
        }

    return None


def is_moderator(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True

    role = member.guild.get_role(MODERATOR_ROLE_ID)

    if role and role in member.roles:
        return True

    return False


# ============================================================
# ======================== MongoDB 使用者紀錄 ==============
# ============================================================

def get_user_record(guild_id: int, user_id: int):

    record = moderation_records_col.find_one({
        "guild_id": guild_id,
        "user_id": user_id
    })

    if record:
        return record

    new_record = {
        "guild_id": guild_id,
        "user_id": user_id,

        "warnings": [],

        "minor": 0,
        "medium": 0,
        "major": 0,

        "updated_at": utc_now()
    }

    moderation_records_col.insert_one(new_record)

    return new_record


def cleanup_expired_warnings(guild_id: int, user_id: int):

    record = get_user_record(guild_id, user_id)

    now = utc_now()

    warnings = record.get("warnings", [])

    active = []

    for warning in warnings:

        expires_at = warning.get("expires_at")

        if expires_at and expires_at > now:
            active.append(warning)

    if len(active) != len(warnings):

        moderation_records_col.update_one(
            {
                "guild_id": guild_id,
                "user_id": user_id
            },
            {
                "$set": {
                    "warnings": active,
                    "updated_at": now
                }
            }
        )

    return active


# ============================================================
# ======================== 建立案件 ==========================
# ============================================================

def create_case(
    guild_id,
    user_id,
    channel_id,
    message_id,
    content,
    category,
    matched_words
):

    case = {
        "guild_id": guild_id,
        "user_id": user_id,
        "channel_id": channel_id,
        "message_id": message_id,

        "content": content,

        "category": category,
        "matched_words": matched_words,

        "status": "pending_review",

        "action": None,
        "reviewer_id": None,

        "created_at": utc_now(),
        "execute_at": None,

        "cancelled": False,
        "executed": False
    }

    result = moderation_cases_col.insert_one(case)

    return result.inserted_id


# ============================================================
# ======================== 取得處分 Embed ===================
# ============================================================

def build_case_embed(
    case_id,
    message: discord.Message,
    detection
):

    embed = discord.Embed(
        title="🚨 疑似違規訊息",
        description="請管理員人工審核此案件。",
        color=discord.Color.orange()
    )

    embed.add_field(
        name="案件編號",
        value=f"`{case_id}`",
        inline=True
    )

    embed.add_field(
        name="使用者",
        value=f"{message.author.mention}\n`{message.author.id}`",
        inline=True
    )

    embed.add_field(
        name="頻道",
        value=message.channel.mention,
        inline=True
    )

    embed.add_field(
        name="偵測類型",
        value=detection["category"],
        inline=True
    )

    embed.add_field(
        name="觸發詞",
        value=", ".join(detection["matched_words"]),
        inline=True
    )

    content = message.content

    if len(content) > 1000:
        content = content[:1000] + "..."

    embed.add_field(
        name="原始訊息",
        value=f"```{content}```",
        inline=False
    )

    embed.set_footer(
        text="請確認後選擇處分，處分會延遲 60 秒執行。"
    )

    return embed


# ============================================================
# ======================== 四個審核按鈕 ======================
# ============================================================

class ModerationView(discord.ui.View):

    def __init__(self, case_id):
        super().__init__(timeout=None)
        self.case_id = case_id

    async def process_action(
        self,
        interaction: discord.Interaction,
        action: str
    ):

        if not interaction.guild:
            return

        member = interaction.user

        if not isinstance(member, discord.Member):
            return

        if not is_moderator(member):

            await interaction.response.send_message(
                "❌ 你沒有審核權限。",
                ephemeral=True
            )

            return

        case = moderation_cases_col.find_one({
            "_id": self.case_id
        })

        if not case:

            await interaction.response.send_message(
                "❌ 找不到這個案件。",
                ephemeral=True
            )

            return

        if case.get("status") != "pending_review":

            await interaction.response.send_message(
                "❌ 這個案件已經處理過了。",
                ephemeral=True
            )

            return

        execute_at = utc_now() + timedelta(
            seconds=ACTION_DELAY
        )

        moderation_cases_col.update_one(
            {
                "_id": self.case_id
            },
            {
                "$set": {
                    "status": "scheduled",
                    "action": action,
                    "reviewer_id": member.id,
                    "execute_at": execute_at
                }
            }
        )

        await interaction.response.send_message(
            f"✅ 已選擇 **{action}**。\n"
            f"⏳ {ACTION_DELAY} 秒後執行。\n"
            f"案件編號：`{self.case_id}`\n\n"
            f"如需撤回，請在時間內使用：\n"
            f"`/撤回案件 {self.case_id}`",
            ephemeral=True
        )

        try:

            await interaction.message.edit(
                view=None
            )

        except Exception:
            pass

    @discord.ui.button(
        label="警告",
        emoji="⚠️",
        style=discord.ButtonStyle.secondary,
        custom_id="moderation_warning"
    )
    async def warning(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.process_action(
            interaction,
            "警告"
        )

    @discord.ui.button(
        label="小過",
        emoji="🟡",
        style=discord.ButtonStyle.primary,
        custom_id="moderation_minor"
    )
    async def minor(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.process_action(
            interaction,
            "小過"
        )

    @discord.ui.button(
        label="中過",
        emoji="🟠",
        style=discord.ButtonStyle.primary,
        custom_id="moderation_medium"
    )
    async def medium(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.process_action(
            interaction,
            "中過"
        )

    @discord.ui.button(
        label="大過",
        emoji="🔴",
        style=discord.ButtonStyle.danger,
        custom_id="moderation_major"
    )
    async def major(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.process_action(
            interaction,
            "大過"
        )


# ============================================================
# ======================== 套用處分 ==========================
# ============================================================

async def apply_action(case):

    guild = bot.get_guild(case["guild_id"])

    if not guild:
        return

    member = guild.get_member(case["user_id"])

    if not member:

        # 如果使用者已離開伺服器
        # 仍然保留案件紀錄
        return

    action = case["action"]

    guild_id = guild.id
    user_id = member.id

    record = get_user_record(
        guild_id,
        user_id
    )

    # ========================================================
    # 警告
    # ========================================================

    if action == "警告":

        warnings = cleanup_expired_warnings(
            guild_id,
            user_id
        )

        warning_entry = {
            "case_id": str(case["_id"]),
            "created_at": utc_now(),
            "expires_at": utc_now() + timedelta(days=7)
        }

        warnings.append(warning_entry)

        # 第五次警告
        if len(warnings) >= 5:

            warnings = []

            moderation_records_col.update_one(
                {
                    "guild_id": guild_id,
                    "user_id": user_id
                },
                {
                    "$set": {
                        "warnings": warnings,
                        "updated_at": utc_now()
                    },
                    "$inc": {
                        "minor": 1
                    }
                }
            )

            await give_role(
                member,
                MINOR_ROLE_ID
            )

            # 小過第三次
            await check_promotions(
                guild,
                member
            )

        else:

            moderation_records_col.update_one(
                {
                    "guild_id": guild_id,
                    "user_id": user_id
                },
                {
                    "$set": {
                        "warnings": warnings,
                        "updated_at": utc_now()
                    }
                }
            )

            await give_role(
                member,
                WARNING_ROLE_ID
            )

    # ========================================================
    # 小過
    # ========================================================

    elif action == "小過":

        moderation_records_col.update_one(
            {
                "guild_id": guild_id,
                "user_id": user_id
            },
            {
                "$inc": {
                    "minor": 1
                },
                "$set": {
                    "updated_at": utc_now()
                }
            }
        )

        await check_promotions(
            guild,
            member
        )

    # ========================================================
    # 中過
    # ========================================================

    elif action == "中過":

        moderation_records_col.update_one(
            {
                "guild_id": guild_id,
                "user_id": user_id
            },
            {
                "$inc": {
                    "medium": 1
                },
                "$set": {
                    "updated_at": utc_now()
                }
            }
        )

        await check_promotions(
            guild,
            member
        )

    # ========================================================
    # 大過
    # ========================================================

    elif action == "大過":

        moderation_records_col.update_one(
            {
                "guild_id": guild_id,
                "user_id": user_id
            },
            {
                "$inc": {
                    "major": 1
                },
                "$set": {
                    "updated_at": utc_now()
                }
            }
        )

        await check_promotions(
            guild,
            member
        )


# ============================================================
# ======================== 身份組 ===========================
# ============================================================

async def give_role(
    member: discord.Member,
    role_id: int
):

    role = member.guild.get_role(role_id)

    if not role:
        return

    try:
        await member.add_roles(
            role,
            reason="違規處分"
        )

    except discord.Forbidden:
        print(
            f"[ERROR] 無法給予身份組：{role_id}"
        )


# ============================================================
# ======================== 升級判定 ==========================
# ============================================================

async def check_promotions(
    guild: discord.Guild,
    member: discord.Member
):

    record = get_user_record(
        guild.id,
        member.id
    )

    minor = record.get("minor", 0)
    medium = record.get("medium", 0)
    major = record.get("major", 0)

    # --------------------------------------------------------
    # 小過 3 → 中過
    # --------------------------------------------------------

    if minor >= 3:

        promotion_count = minor // 3

        new_minor = minor % 3

        moderation_records_col.update_one(
            {
                "guild_id": guild.id,
                "user_id": member.id
            },
            {
                "$set": {
                    "minor": new_minor
                },
                "$inc": {
                    "medium": promotion_count
                }
            }
        )

        for _ in range(promotion_count):

            await give_role(
                member,
                MEDIUM_ROLE_ID
            )

    # --------------------------------------------------------
    # 中過 3 → 大過
    # --------------------------------------------------------

    record = get_user_record(
        guild.id,
        member.id
    )

    medium = record.get("medium", 0)

    if medium >= 3:

        promotion_count = medium // 3

        new_medium = medium % 3

        moderation_records_col.update_one(
            {
                "guild_id": guild.id,
                "user_id": member.id
            },
            {
                "$set": {
                    "medium": new_medium
                },
                "$inc": {
                    "major": promotion_count
                }
            }
        )

        for _ in range(promotion_count):

            await give_role(
                member,
                MAJOR_ROLE_ID
            )

    # --------------------------------------------------------
    # 大過 3 → BAN
    # --------------------------------------------------------

    record = get_user_record(
        guild.id,
        member.id
    )

    major = record.get("major", 0)

    if major >= 3:

        await give_role(
            member,
            BAN_ROLE_ID
        )


# ============================================================
# ======================== 自動 BAN ==========================
# ============================================================

async def check_ban_role(
    member: discord.Member
):

    role = member.guild.get_role(
        BAN_ROLE_ID
    )

    if not role:
        return

    if role not in member.roles:
        return

    # 管理員保護
    if member.guild_permissions.administrator:
        return

    try:

        await member.guild.ban(
            member,
            reason="取得自動 BAN 身份組"
        )

    except discord.Forbidden:

        print(
            f"[ERROR] 無法 BAN {member}"
        )


# ============================================================
# ======================== 處分執行循環 ======================
# ============================================================

@tasks.loop(seconds=5)
async def process_scheduled_cases():

    now = utc_now()

    cases = moderation_cases_col.find({
        "status": "scheduled",
        "execute_at": {
            "$lte": now
        },
        "cancelled": False,
        "executed": False
    })

    for case in cases:

        try:

            await apply_action(case)

            moderation_cases_col.update_one(
                {
                    "_id": case["_id"]
                },
                {
                    "$set": {
                        "status": "executed",
                        "executed": True,
                        "executed_at": utc_now()
                    }
                }
            )

        except Exception as e:

            print(
                f"[ERROR] 處分執行失敗：{e}"
            )


# ============================================================
# ======================== 自動清理警告 =====================
# ============================================================

@tasks.loop(hours=1)
async def cleanup_warnings():

    now = utc_now()

    records = moderation_records_col.find({
        "warnings": {
            "$exists": True,
            "$ne": []
        }
    })

    for record in records:

        active = []

        for warning in record.get(
            "warnings",
            []
        ):

            expires_at = warning.get(
                "expires_at"
            )

            if expires_at and expires_at > now:

                active.append(warning)

        if len(active) != len(
            record.get("warnings", [])
        ):

            moderation_records_col.update_one(
                {
                    "_id": record["_id"]
                },
                {
                    "$set": {
                        "warnings": active,
                        "updated_at": now
                    }
                }
            )


# ============================================================
# ======================== 訊息監控 ==========================
# ============================================================

@bot.event
async def on_message(message: discord.Message):

    if message.author.bot:
        return

    if not message.guild:
        return

    detection = detect_violation(
        message.content
    )

    if detection:

        case_id = create_case(
            guild_id=message.guild.id,
            user_id=message.author.id,
            channel_id=message.channel.id,
            message_id=message.id,
            content=message.content,
            category=detection["category"],
            matched_words=detection["matched_words"]
        )

        moderation_channel = bot.get_channel(
            MODERATION_CHANNEL_ID
        )

        if moderation_channel:

            embed = build_case_embed(
                case_id,
                message,
                detection
            )

            await moderation_channel.send(
                embed=embed,
                view=ModerationView(case_id)
            )

        if DELETE_VIOLATION_MESSAGE:

            try:
                await message.delete()

            except discord.Forbidden:
                pass

    await bot.process_commands(message)


# ============================================================
# ======================== 撤回案件 ==========================
# ============================================================

@bot.tree.command(
    name="撤回案件",
    description="撤回尚未執行的違規處分"
)
@app_commands.describe(
    case_id="案件編號"
)
async def cancel_case(
    interaction: discord.Interaction,
    case_id: str
):

    if not interaction.guild:

        await interaction.response.send_message(
            "❌ 此指令只能在伺服器使用。",
            ephemeral=True
        )

        return

    member = interaction.user

    if not isinstance(member, discord.Member):

        await interaction.response.send_message(
            "❌ 無法確認你的身份。",
            ephemeral=True
        )

        return

    if not is_moderator(member):

        await interaction.response.send_message(
            "❌ 你沒有審核權限。",
            ephemeral=True
        )

        return

    case = moderation_cases_col.find_one({
        "_id": __import__("bson").ObjectId(case_id)
    })

    if not case:

        await interaction.response.send_message(
            "❌ 找不到案件。",
            ephemeral=True
        )

        return

    if case.get("status") not in (
        "scheduled",
        "executed"
    ):

        await interaction.response.send_message(
            "❌ 這個案件目前不能撤回。",
            ephemeral=True
        )

        return

    # --------------------------------------------------------
    # 尚未執行
    # --------------------------------------------------------

    if case["status"] == "scheduled":

        moderation_cases_col.update_one(
            {
                "_id": case["_id"]
            },
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled": True,
                    "cancelled_by": member.id,
                    "cancelled_at": utc_now()
                }
            }
        )

        await interaction.response.send_message(
            f"↩️ 案件 `{case_id}` 已撤回，處分不會執行。",
            ephemeral=True
        )

        return

    # --------------------------------------------------------
    # 已經執行
    # --------------------------------------------------------

    if case["status"] == "executed":

        guild = interaction.guild

        try:

            banned_user = await bot.fetch_user(
                case["user_id"]
            )

            await guild.unban(
                banned_user,
                reason=f"撤回案件 {case_id}"
            )

            moderation_cases_col.update_one(
                {
                    "_id": case["_id"]
                },
                {
                    "$set": {
                        "status": "revoked_after_execution",
                        "revoked_by": member.id,
                        "revoked_at": utc_now()
                    }
                }
            )

            await interaction.response.send_message(
                f"↩️ 案件 `{case_id}` 已撤回。\n"
                f"🔓 已嘗試解除 BAN。",
                ephemeral=True
            )

        except discord.NotFound:

            await interaction.response.send_message(
                "⚠️ 使用者目前沒有 BAN，或找不到該使用者。",
                ephemeral=True
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ Bot 沒有解除 BAN 的權限。",
                ephemeral=True
            )


# ============================================================
# ======================== 啟動 ===============================
# ============================================================

@bot.event
async def on_ready():

    print(
        f"登入成功：{bot.user}"
    )

    try:

        await bot.tree.sync()

        print("Slash Commands 同步完成")

    except Exception as e:

        print(
            f"Slash Command 同步失敗：{e}"
        )

    if not process_scheduled_cases.is_running():
        process_scheduled_cases.start()

    if not cleanup_warnings.is_running():
        cleanup_warnings.start()


# ============================================================
# ======================== 啟動 Bot ==========================
# ============================================================

bot.run(DISCORD_CODE)
