#Billy

import os
import logging
import time
import random
import string
import json
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, error
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
import asyncio


# Paths
SEARCH_PATH = "/storage/emulated/0/here/logs"
OUTPUT_PATH = "/storage/emulated/0/here/outputnipogi"


# ==================== BOT CONFIGURATION ====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- PASTE YOUR BOT TOKEN HERE ---
TOKEN = "8421099743:AAGxzSnLjMT_-nKrFs_MNYtSwwtxIBJYPm0"

# --- ADMIN & DATA ---
ADMINS = [8339473478]  # Replace with your admin user ID

ACCOUNTS_FOLDER = "accounts"
USER_DATA_FILE = "𝐁𝐢𝐥𝐥𝐲_user_data.json"
GENERATED_KEYS_FILE = "𝐁𝐢𝐥𝐥𝐲_generated_keys.json"
KEYWORD_USAGE_FILE = "𝐁𝐢𝐥𝐥𝐲_keyword_usage.json"
BANNED_USERS_FILE = "𝐁𝐢𝐥𝐥𝐲_banned_users.json"
WELCOME_VIDEO_PATH = "https://t.me/OriginalAnimePictures/842"

file_locks = {}
# Keywords updated to match V8
CODM_KEYWORDS = [
    "100082", "100055", "100080", "100054", "100072", 
    "gaslite", "authgop", "garena", "sso"
]

# --- Conversation States (from V8) ---
(
    AWAITING_REDEEM_KEY,
    AWAITING_BLOCKLIST_ADD,
    AWAITING_BLOCKLIST_REMOVE,
    AWAITING_BROADCAST_CONTENT,
    AWAITING_MERGE_FILES,
    AWAITING_URL_REMOVER_FILE,
    AWAITING_DUPLICATE_REMOVER_FILE,
) = range(7)


# ==================== MENUS & STYLING ====================
def build_keyboard(menu_items: dict) -> InlineKeyboardMarkup:
    if not menu_items:
        return None
    buttons = [
        InlineKeyboardButton(text, callback_data=data)
        for text, data in menu_items.items()
    ]
    keyboard = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(keyboard)


# Menus updated to use the V8 vending logic (select_lines_ keyword)
MENUS = {
    "main": {
        "🚀 𝐀𝐂𝐂𝐄𝐒𝐒 𝐕𝐀𝐔𝐋𝐓": "menu_search",
        "🛠️ 𝐔𝐓𝐈𝐋𝐈𝐓𝐈𝐄𝐒": "menu_tools",
        "🔑 𝐌𝐘 𝐀𝐂𝐂𝐄𝐒𝐒 𝐏𝐀𝐒𝐒": "my_key",
        "👑 𝐀𝐃𝐌𝐈𝐍 𝐓𝐄𝐑𝐌𝐈𝐍𝐀𝐋": "menu_admin",
        "❌ 𝐂𝐋𝐄𝐀𝐑": "clear_menu",
    },
    "menu_search": {
        "🎮 𝐂𝐚𝐥𝐥 𝐨𝐟 𝐃𝐮𝐭𝐲": "menu_codm",
        "💎 𝐌𝐋𝐁𝐁": "menu_mlbb",
        "🧱 𝐑𝐨𝐛𝐥𝐨𝐱": "menu_roblox",
        "🎬 𝐂𝐢𝐧𝐞𝐦𝐚": "menu_cinema",
        "💳 𝐂𝐨𝐝𝐚𝐒𝐡𝐨𝐩": "menu_codashop",
        "📱 𝐒𝐨𝐜𝐢𝐚𝐥 𝐌𝐞𝐝𝐢𝐚": "menu_social",
        "⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐌𝐀𝐈𝐍": "main",
    },
    "menu_tools": {
        "🔗 𝐔𝐑𝐋 𝐑𝐄𝐌𝐎𝐕𝐄𝐑": "url_remover_start",
        "🗑️ 𝐃𝐔𝐏𝐋𝐈𝐂𝐀𝐓𝐄 𝐑𝐄𝐌𝐎𝐕𝐄𝐑": "duplicate_remover_start",
        "🧾 𝐌𝐄𝐑𝐆𝐄 𝐅𝐈𝐋𝐄𝐒": "merge_start",
        "⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐌𝐀𝐈𝐍": "main",
    },
    "menu_admin": {
        "📊 𝐒𝐓𝐎𝐂𝐊 𝐋𝐄𝐕𝐄𝐋𝐒": "admin_list_stock",
        "👥 𝐔𝐒𝐄𝐑 𝐋𝐈𝐒𝐓": "admin_list_users",
        "📈 𝐔𝐒𝐀𝐆𝐄 𝐒𝐓𝐀𝐓𝐒": "admin_statistics",
        "🚫 𝐁𝐋𝐎𝐂𝐊𝐋𝐈𝐒𝐓": "menu_blocklist",
        "📢 𝐁𝐑𝐎𝐀𝐃𝐂𝐀𝐒𝐓": "broadcast_start",
        "⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐌𝐀𝐈𝐍": "main",
    },
    "menu_codm": {
        "🔑 100082": "select_lines_100082",
        "🔑 100055": "select_lines_100055",
        "🔑 100080": "select_lines_100080",
        "🔑 100054": "select_lines_100054",
        "🔑 100072": "select_lines_100072",
        "🔑 𝐆𝐀𝐒𝐋𝐈𝐓𝐄": "select_lines_gaslite",
        "🔑 𝐀𝐔𝐓𝐇𝐆𝐎𝐏": "select_lines_authgop",
        "🔑 𝐆𝐀𝐑𝐄𝐍𝐀": "select_lines_garena",
        "🔑 𝐒𝐒𝐎": "select_lines_sso",
        "🔀 𝐌𝐢𝐱𝐞𝐝 𝐊𝐞𝐲𝐰𝐨𝐫𝐝𝐬": "select_lines_mixed",
        "⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐒𝐄𝐀𝐑𝐂𝐇": "menu_search",
    },
    "menu_mlbb": {
        "𝐌𝐓𝐀𝐂𝐂": "get_other_mtacc",
        "𝐌𝐀𝐈𝐍 𝐌𝐋": "get_other_mainml",
        "⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐒𝐄𝐀𝐑𝐂𝐇": "menu_search",
    },
    "menu_roblox": {
        "𝐑𝐁𝐋𝐗": "get_other_rblx",
        "⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐒𝐄𝐀𝐑𝐂𝐇": "menu_search",
    },
    "menu_cinema": {
        "𝐍𝐄𝐓𝐅𝐋𝐈𝐗": "get_other_netflix",
        "𝐁𝐈𝐋𝐈 𝐁𝐈𝐋𝐈": "get_other_bilibili",
        "𝐘𝐎𝐔𝐓𝐔𝐁𝐄": "get_other_youtube",
        "⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐒𝐄𝐀𝐑𝐂𝐇": "menu_search",
    },
    "menu_codashop": {
        "𝐂𝐎𝐃𝐀": "get_other_coda", 
        "⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐒𝐄𝐀𝐑𝐂𝐇": "menu_search"
    },
    "menu_social": {
        "𝐅𝐀𝐂𝐄𝐁𝐎𝐎𝐊": "get_other_facebook",
        "𝐈𝐍𝐒𝐓𝐀𝐆𝐑𝐀𝐌": "get_other_instagram",
        "𝐓𝐈𝐊𝐓𝐎𝐊": "get_other_tiktok",
        "𝐓𝐖𝐈𝐓𝐓𝐄𝐑": "get_other_twitter",
        "𝐓𝐄𝐋𝐄𝐆𝐑𝐀𝐌": "get_other_telegram",
        "𝐃𝐈𝐒𝐂𝐎𝐑𝐃": "get_other_discord",
        "⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐒𝐄𝐀𝐑𝐂𝐇": "menu_search",
    },
    "menu_blocklist": {
        "➕ 𝐀𝐃𝐃 𝐓𝐎 𝐁𝐋𝐎𝐂𝐊𝐋𝐈𝐒𝐓": "blocklist_add_start",
        "➖ 𝐑𝐄𝐌𝐎𝐕𝐄 𝐅𝐑𝐎𝐌 𝐁𝐋𝐎𝐂𝐊𝐋𝐈𝐒𝐓": "blocklist_remove_start",
        "⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐀𝐃𝐌𝐈𝐍": "menu_admin",
    },
}


# ==================== UTILITY & DATA FUNCTIONS (from V8) ====================
def load_data(file_path, default_value):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading {file_path}: {e}")
    return default_value

SEARCH_PATH = "/storage/emulated/0/here/logs"
OUTPUT_PATH = "/storage/emulated/0/here/outputnipogi"

def save_data(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
    except IOError as e:
        logger.error(f"Error saving {file_path}: {e}")


user_data = load_data(USER_DATA_FILE, {})
generated_keys = load_data(GENERATED_KEYS_FILE, {})
keyword_usage = load_data(KEYWORD_USAGE_FILE, {})
banned_users = load_data(BANNED_USERS_FILE, {})


def get_total_stock():
    total_lines = 0
    if not os.path.exists(ACCOUNTS_FOLDER):
        return 0
    for filename in os.listdir(ACCOUNTS_FOLDER):
        if filename.endswith(".txt"):
            try:
                with open(
                    os.path.join(ACCOUNTS_FOLDER, filename),
                    "r",
                    encoding="utf-8",
                    errors="ignore",
                ) as f:
                    lines = sum(1 for line in f if line.strip())
                    total_lines += lines
            except Exception:
                continue
    return total_lines


def get_key_remaining_time(user_info: dict) -> str:
    if not user_info:
        return "N/A"
    if user_info.get("duration") == float("inf"):
        return "Lifetime Access"
    redeemed_at = user_info.get("redeemed_at", 0)
    duration = user_info.get("duration", 0)
    if not redeemed_at or not duration:
        return "N/A"
    remaining_seconds = (redeemed_at + duration) - time.time()
    if remaining_seconds <= 0:
        return "Expired"
    days, rem = divmod(remaining_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    return f"{int(days)}d {int(hours)}h {int(minutes)}m"


def get_user_id_from_username(username_to_find: str) -> str | None:
    username_to_find = username_to_find.lstrip("@").lower()
    for user_id, data in user_data.items():
        if data.get("username", "").lower() == username_to_find:
            return user_id
    return None


def is_user_active(user_id):
    info = user_data.get(str(user_id))
    if not info:
        return False
    if info.get("duration") == float("inf"):
        return True
    return time.time() < (info.get("redeemed_at", 0) + info.get("duration", 0))


async def notify_admins(message: str, context: ContextTypes.DEFAULT_TYPE):
    for admin_id in ADMINS:
        try:
            await context.bot.send_message(
                chat_id=admin_id, text=message, parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send notification to admin {admin_id}: {e}")


async def delete_message_after_delay(message: Update.message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except error.BadRequest as e:
        logger.info(f"Could not delete message after delay: {e}")


# ==================== BAN & USAGE LIMIT SYSTEM (from V8) ====================
async def show_cooldown(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    cooldown_duration = 240  # 4 minutes
    try:
        msg = await context.bot.send_message(
            chat_id=chat_id, text=f"⏳ System Cooldown: {cooldown_duration} seconds"
        )
        for i in range(cooldown_duration - 5, -1, -5):
            await asyncio.sleep(5)
            try:
                await msg.edit_text(f"⏳ System Cooldown: {i} seconds remaining...")
            except error.BadRequest:
                break
        await msg.edit_text("✅ Cooldown finished. You can now generate again.")
        asyncio.create_task(delete_message_after_delay(msg, 10))
    except Exception as e:
        logger.error(f"An error occurred in show_cooldown: {e}")


def is_user_banned(user_id):
    user_id_str = str(user_id)
    if user_id_str in banned_users:
        ban_info = banned_users[user_id_str]
        lift_time = ban_info.get("lift_time")
        if lift_time and time.time() < lift_time:
            return True
        elif lift_time and time.time() >= lift_time:
            del banned_users[user_id_str]
            save_data(BANNED_USERS_FILE, banned_users)
            return False
    return False


def get_ban_message(user_id):
    user_id_str = str(user_id)
    if user_id_str in banned_users:
        ban_info = banned_users[user_id_str]
        reason = ban_info.get("reason", "System resource abuse.")
        return (
            f"🚨 **ACCESS DENIED** 🚨\n\n"
            f"**Reason:** {reason}\n"
            f"Your access has been temporarily suspended.\n\n"
            f"Please contact an administrator if you believe this is a mistake."
        )
    return "You are banned."


async def check_generation_gap(
    user_id: int, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    if user_id in ADMINS:
        return False
    user_info = user_data.get(str(user_id), {})
    last_gen_time = user_info.get("last_gen_time", 0)
    if last_gen_time > 0 and (time.time() - last_gen_time) < 240:  # 4 minutes
        ban_time = time.time()
        banned_users[str(user_id)] = {
            "ban_time": ban_time,
            "lift_time": ban_time + 3600,  # 1 hour ban for spamming
            "reason": "Cooldown violation (spamming).",
        }
        save_data(BANNED_USERS_FILE, banned_users)
        await context.bot.send_message(user_id, get_ban_message(user_id))
        await notify_admins(
            f"User @{user_info.get('username', user_id)} has been auto-banned for violating the generation cooldown.",
            context,
        )
        return True
    return False


# ==================== CORE GENERATION LOGIC (from V8) ====================
async def vend_accounts(
    user_id, keyword, line_count, context: ContextTypes.DEFAULT_TYPE
):
    start_time = time.time()
    if await check_generation_gap(user_id, context):
        return

    is_cod_keyword = line_count is not None
    if not is_cod_keyword:
        is_lifetime = user_data.get(str(user_id), {}).get("duration") == float("inf")
        line_count = 150 if is_lifetime else 100

    msg = await context.bot.send_message(
        chat_id=user_id, text="🛰️ Accessing data vault... Please wait."
    )
    await asyncio.sleep(2)
    try:
        await msg.edit_text("✅ Connection established. Preparing your data package...")
    except error.BadRequest:
        pass
    await asyncio.sleep(1)

    file_path = os.path.join(ACCOUNTS_FOLDER, f"{keyword}.txt")
    if not os.path.exists(file_path):
        await msg.edit_text(
            f"❌ **Error:** Data stream for '`{keyword.upper()}`' not found."
        )
        return

    lock = file_locks.setdefault(file_path, asyncio.Lock())
    accounts_to_send = []

    async with lock:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.strip() for line in f if line.strip()]
            if not lines:
                await msg.edit_text(
                    f"⚠️ **Out of Stock** ⚠️\n\nThe data stream for `{keyword.upper()}` is currently empty. Please try another keyword or check back later.",
                    parse_mode="Markdown"
                )
                return

            actual_line_count = min(line_count, len(lines))
            accounts_to_send = random.sample(lines, actual_line_count)
            remaining_accounts = [line for line in lines if line not in accounts_to_send]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(remaining_accounts))
        except Exception as e:
            logger.error(f"Error vending accounts: {e}")
            await msg.edit_text("An internal server error occurred. Please try again later.")
            return
        finally:
            if accounts_to_send:
                 await msg.delete()

    output_filename = f"𝒆𝒄𝒍𝒊𝒑𝒔𝒆{keyword.upper()}.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(accounts_to_send))

    try:
        user_info = user_data.get(str(user_id), {})
        process_time = time.time() - start_time
        new_caption = (
            f"📦 𝐋𝐈𝐍𝐄𝐒 𝐆𝐄𝐍𝐄𝐑𝐀𝐓𝐄𝐃 𝐒𝐔𝐂𝐂𝐄𝐒𝐒𝐅𝐔𝐋𝐋𝐘 📦\n\n"
            f"🔹 𝐃𝐎𝐌𝐀𝐈𝐍: `{keyword.upper()}`\n"
            f"🔹 𝐔𝐍𝐈𝐓𝐒: `{len(accounts_to_send)}`\n"
            f"🔹 𝐓𝐑𝐀𝐍𝐒𝐌𝐈𝐒𝐒𝐈𝐎𝐍 𝐓𝐈𝐌𝐄: `{process_time:.2f} seconds`\n"
            f"🔹 𝐆𝐄𝐍𝐄𝐑𝐀𝐓𝐄𝐃 𝐎𝐍: `{datetime.now().strftime('%Y-%m-%d')}`\n\n"
            f"*This file is protected and will be deleted after 5 minutes.*\n\n"
            f"__Bot by @billyxjeff__"
        )
        with open(output_filename, "rb") as f:
            sent_message = await context.bot.send_document(
                chat_id=user_id,
                document=f,
                caption=new_caption,
                parse_mode="Markdown",
                protect_content=True,
                filename=output_filename,
            )
            asyncio.create_task(delete_message_after_delay(sent_message, 300))

        if user_id not in ADMINS:
            asyncio.create_task(show_cooldown(user_id, context))

        user_info["last_gen_time"] = time.time()
        user_info["generation_count"] = user_info.get("generation_count", 0) + 1
        user_data[str(user_id)] = user_info
        save_data(USER_DATA_FILE, user_data)
        keyword_usage[keyword] = keyword_usage.get(keyword, 0) + 1
        save_data(KEYWORD_USAGE_FILE, keyword_usage)

        if user_id not in ADMINS:
            admin_notif = (
                f"**📈 Activity Log**\n"
                f"**User:** `@{user_info.get('username', 'N/A')}`\n"
                f"**Stream:** `{keyword.upper()}`\n"
                f"**Units:** `{len(accounts_to_send)}`\n"
                f"**Key Status:** `{get_key_remaining_time(user_info)}`"
            )
            await notify_admins(admin_notif, context)
    except Exception as e:
        logger.error(f"Failed to send document: {e}")
        async with lock:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write("\n".join(accounts_to_send))
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Transmission failed. The data has been rolled back. Please try again.",
        )
    finally:
        if os.path.exists(output_filename):
            os.remove(output_filename)


# ==================== MAIN MENU & COMMANDS (from V8) ====================
async def get_main_menu_components(user_id: int) -> tuple[str, InlineKeyboardMarkup]:
    user_info = user_data.get(str(user_id), {})
    user_name = user_info.get("username", "N/A")
    total_gens = user_info.get("generation_count", 0)

    caption = (
        f"**Welcome to the Digital Vault, {user_name}!**\n\n"
        f"Here you can access various data streams and utilities. Please select an option from the menu below.\n\n"
        f"🔑 **Access Status:** `{get_key_remaining_time(user_info)}`\n"
        f"📈 **Total Generations:** `{total_gens}`\n"
        f"🗂️ **Total Stock:** `{get_total_stock():,}` lines"
    )

    menu_items = MENUS["main"].copy()
    if user_id not in ADMINS:
        menu_items.pop("👑 𝐀𝐃𝐌𝐈𝐍 𝐓𝐄𝐑𝐌𝐈𝐍𝐀𝐋", None)
    return caption, build_keyboard(menu_items)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_user_banned(user_id):
        await update.message.reply_text(get_ban_message(user_id), parse_mode="Markdown")
        return

    caption = """
♨️ 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙏𝙊 𝙀𝘾𝙇𝙄𝙋𝙎𝙀 𝙎𝙀𝘼𝙍𝘾𝙃𝙀𝙍 ♨️
🚀 𝒀𝑶𝑼𝑹 𝑼𝑳𝑻𝑰𝑴𝑨𝑻𝑬 𝑨𝑳𝑳-𝑰𝑵-𝑶𝑵𝑬 𝑷𝑨𝑳𝑫𝑶 𝑮𝑬𝑵𝑬𝑹𝑨𝑻𝑶𝑹 𝑯𝑼𝑩

💠 𝑾𝑯𝑨𝑻 𝑴𝑨𝑲𝑬𝑺 𝙀𝘾𝙇𝙋𝙄𝙎𝙀 𝑫𝑰𝑭𝑭𝑬𝑹𝑬𝑵𝑻?
🔹 𝑼𝑳𝑻𝑹𝑨-𝑭𝑨𝑺𝑻 𝑻𝑿𝑻 𝑮𝑬𝑵𝑬𝑹𝑨𝑻𝑰𝑶𝑵 – 𝑰𝑵𝑺𝑻𝑨𝑵𝑻. 𝑺𝑯𝑨𝑹𝑷. 𝑹𝑬𝑳𝑰𝑨𝑩𝑳𝑬.
🔹 𝑬𝑿𝑷𝑨𝑵𝑫𝑬𝑫 𝑲𝑬𝒀𝑾𝑶𝑹𝑫 𝑪𝑶𝑽𝑬𝑹𝑨𝑮𝑬 – 𝑾𝑶𝑹𝑲𝑺 𝑾𝑰𝑻𝑯 𝑪𝑶𝑫𝑴, 𝑴𝑳𝑩𝑩, 𝑹𝑶𝑩𝑳𝑶𝑿, 𝑪𝑰𝑵𝑬𝑴𝑨, 𝑵𝑬𝑻𝑭𝑳𝑰𝑿, 𝑨𝑵𝑫 𝑴𝑶𝑹𝑬!
🔹 𝑩𝑼𝑰𝑳𝑻-𝑰𝑵 𝑻𝑶𝑶𝑳𝑺 –
 • 𝑻𝑿𝑻 𝑴𝑬𝑹𝑮𝑬𝑹
 • 𝑫𝑼𝑷𝑳𝑰𝑪𝑨𝑻𝑬 𝑭𝑰𝑳𝑻𝑬𝑹
 • 𝑨𝑼𝑻𝑶 𝑭𝑶𝑹𝑴𝑨𝑻𝑻𝑬𝑹
🔹 𝑺𝑳𝑬𝑬𝑲 𝑼𝑰 – 𝑩𝑼𝑰𝑳𝑻 𝑭𝑶𝑹 𝑺𝑷𝑬𝑬𝑫 𝑨𝑵𝑫 𝑪𝑳𝑨𝑹𝑰𝑻𝒀

🧠 𝐔𝐒𝐄𝐑 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒
/start – 𝑰𝑵𝑰𝑻𝑰𝑨𝑳𝑰𝒁𝑬 𝑻𝑯𝑬 𝑩𝑶𝑻 𝑺𝒀𝑺𝑻𝑬𝑴
/menu – 𝑨𝑪𝑪𝑬𝑺𝑺 𝑭𝑼𝑳𝑳 𝑶𝑷𝑻𝑰𝑶𝑵𝑺 & 𝑻𝑶𝑶𝑳𝑺
/redeem `key` – 𝑹𝑬𝑫𝑬𝑬𝑴 𝒀𝑶𝑼𝑹 𝑲𝑬𝒀

🛡️ 𝐀𝐃𝐌𝐈𝐍 𝐂𝐎𝐍𝐓𝐑𝐎𝐋𝐒
/generatekey – 𝑰𝑵𝑺𝑻𝑨𝑵𝑻𝑳𝒀 𝑰𝑺𝑺𝑼𝑬 𝑨 𝑵𝑬𝑾 𝑽𝑨𝑳𝑰𝑫 𝑲𝑬𝒀
/deleteuser – 𝑹𝑬𝑴𝑶𝑽𝑬 𝑨 𝑺𝑷𝑬𝑪𝑰𝑭𝑰𝑪 𝑼𝑺𝑬𝑹
/revokeall – 𝑬𝑿𝑷𝑰𝑹𝑬 𝑨𝑳𝑳 𝑨𝑪𝑻𝑰𝑽𝑬 𝑲𝑬𝒀𝑺
/broadcast – 𝑺𝑬𝑵𝑫 𝑮𝑳𝑶𝑩𝑨𝑳 𝑨𝑵𝑵𝑶𝑼𝑵𝑪𝑬𝑴𝑬𝑵𝑻

⚠️ 𝑵𝑶𝑻𝑰𝑪𝑬 𝑻𝑶 𝑨𝑳𝑳 𝑼𝑺𝑬𝑹𝑺
𝙀𝘾𝙇𝙋𝙄𝙎𝙀 𝙎𝙀𝘼𝙍𝘾𝙃𝙀𝙍 𝑼𝑺𝑬𝑺 𝑨 𝑺𝑴𝑨𝑹𝑻 𝑪𝑶𝑶𝑳𝑫𝑶𝑾𝑵.
❗ 𝑮𝑬𝑵𝑬𝑹𝑨𝑻𝑰𝑵𝑮 𝑻𝑶𝑶 𝑸𝑼𝑰𝑪𝑲𝑳𝒀 𝑴𝑨𝒀 𝑹𝑬𝑺𝑼𝑳𝑻 𝑰𝑵 𝑨 𝑻𝑬𝑴𝑷𝑶𝑹𝑨𝑹𝒀 𝑳𝑶𝑪𝑲.
⏳ 𝑾𝑨𝑰𝑻 𝟒 𝑴𝑰𝑵𝑼𝑻𝑬𝑺 𝑩𝑬𝑻𝑾𝑬𝑬𝑵 𝑭𝑰𝑳𝑬 𝑮𝑬𝑵𝑬𝑹𝑨𝑻𝑰𝑶𝑵𝑺.
🎫  𝐍𝐄𝐄𝐃 𝐀 𝐕𝐀𝐋𝐈𝐃 𝐊𝐄𝐘? 𝐌𝐄𝐒𝐒𝐀𝐆𝐄 𝐌𝐄 @billyxjeff
    """

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔑 𝐑𝐄𝐃𝐄𝐄𝐌 𝐀𝐂𝐂𝐄𝐒𝐒 𝐊𝐄𝐘", callback_data="redeem_start")]]
    )
    if os.path.exists(WELCOME_VIDEO_PATH):
        try:
            with open(WELCOME_VIDEO_PATH, "rb") as video_file:
                await context.bot.send_video(
                    chat_id=user_id,
                    video=video_file,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
        except Exception:
            await update.message.reply_text(
                caption, parse_mode="HTML", reply_markup=keyboard
            )
    else:
        await update.message.reply_text(
            caption, parse_mode="HTML", reply_markup=keyboard
        )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.effective_message
    if is_user_banned(user_id):
        await message.reply_text(get_ban_message(user_id), parse_mode="Markdown")
        return
    if user_id not in ADMINS and not is_user_active(user_id):
        await message.reply_text(
            "❌ **Access Denied.** Please use the `/redeem <key>` command to authenticate.",
            parse_mode="Markdown",
        )
        return

    caption, reply_markup = await get_main_menu_components(user_id)
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                caption, reply_markup=reply_markup, parse_mode="Markdown"
            )
        except error.BadRequest:
            await message.reply_text(
                caption, reply_markup=reply_markup, parse_mode="Markdown"
            )
    else:
        await message.reply_text(
            caption, reply_markup=reply_markup, parse_mode="Markdown"
        )


async def mykey_logic(user_id, message, is_callback=False):
    user_info = user_data.get(str(user_id))
    if user_info and is_user_active(user_id):
        text = (
            f"**👤 Access Pass Details**\n\n"
            f"**Status:** `ACTIVE` ✅\n"
            f"**Access Level:** `{get_key_remaining_time(user_info)}`\n"
            f"**Key ID:** `{user_info['key']}`\n\n"
            f"__Bot by @billyxjeff__"
        )
    else:
        text = (
            f"**👤 Access Pass Details**\n\n"
            f"**Status:** `INACTIVE` ❌\n"
            f"Use `/redeem <key>` to activate your access.\n\n"
            f"__Bot by @billyxjeff__"
        )

    reply_markup = build_keyboard({"⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐌𝐀𝐈𝐍": "main"})

    if is_callback:
        await message.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)


async def mykey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await mykey_logic(update.effective_user.id, update.message)


async def mykey_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await mykey_logic(query.from_user.id, query.message, is_callback=True)


# ==================== BUTTON HANDLER (from V8) ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    callback_data = query.data

    if is_user_banned(user_id):
        await query.answer(get_ban_message(user_id), show_alert=True)
        return

    if callback_data == "clear_menu":
        try:
            await query.message.delete()
        except error.BadRequest:
            pass
        return
        
    if callback_data == "main":
        caption, reply_markup = await get_main_menu_components(user_id)
        await query.edit_message_text(caption, reply_markup=reply_markup, parse_mode="Markdown")
        return

    if callback_data == "my_key":
        await mykey_callback(update, context)
        return

    if callback_data.startswith("select_lines_"):
        keyword = callback_data.split("select_lines_")[1]
        lines_menu = {
            "50 𝐋𝐈𝐍𝐄𝐒": f"generate_{keyword}_50",
            "100 𝐋𝐈𝐍𝐄𝐒": f"generate_{keyword}_100",
            "150 𝐋𝐈𝐍𝐄𝐒": f"generate_{keyword}_150",
        }
        back_menu = "menu_codm" if keyword in CODM_KEYWORDS or keyword == "mixed" else "menu_search"
        lines_menu["⬅️ 𝐁𝐀𝐂𝐊"] = back_menu

        await query.edit_message_text(
            text=f"Please select the number of lines for **{keyword.upper()}**:",
            reply_markup=build_keyboard(lines_menu),
            parse_mode="Markdown",
        )
        return

    if callback_data.startswith("generate_"):
        parts = callback_data.split("_")
        keyword, line_count = parts[1], int(parts[2])
        await query.message.delete()
        await vend_accounts(user_id, keyword, line_count, context)
        return

    if callback_data.startswith("get_other_"):
        keyword = callback_data.split("get_other_")[1]
        await query.message.delete()
        await vend_accounts(user_id, keyword, None, context)
        return

    if callback_data in MENUS:
        caption = f"**{callback_data.replace('menu_', '').replace('_', ' ').title()} Menu**\n\n𝐏𝐥𝐞𝐚𝐬𝐞 𝐜𝐡𝐨𝐨𝐬𝐞 𝐚𝐧 𝐨𝐩𝐭𝐢𝐨𝐧:"
        menu_items = MENUS[callback_data].copy()
        await query.edit_message_text(
            text=caption, reply_markup=build_keyboard(menu_items), parse_mode="Markdown"
        )
        return

    # Admin button handlers
    if callback_data == "admin_list_stock":
        await admin_list_stock(update, context)
    elif callback_data == "admin_list_users":
        await admin_list_users(update, context)
    elif callback_data == "admin_statistics":
        await admin_statistics(update, context)


# ==================== CONVERSATION & ADMIN HANDLERS (from V8) ====================
async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


async def menu_in_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await menu(update, context)
    return ConversationHandler.END


# --- REDEEM KEY ---
async def redeemkey_start_cmd(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not context.args:
        await update.message.reply_text(
            "Please provide a key. Usage: `/redeem <key>`", parse_mode="Markdown"
        )
        return ConversationHandler.END

    key_to_redeem = context.args[0].strip()
    await process_key_logic(update, context, key_to_redeem)
    return ConversationHandler.END


async def redeemkey_start_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    try:
        await query.edit_message_caption(
            caption="🔑 **Please send your access key in the chat.**",
            reply_markup=None,
            parse_mode="Markdown",
        )
    except error.BadRequest:
        await query.edit_message_text(
            text="🔑 **Please send your access key in the chat.**",
            reply_markup=None,
            parse_mode="Markdown",
        )
    return AWAITING_REDEEM_KEY


async def process_key_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    key_to_redeem = update.message.text.strip()
    await process_key_logic(update, context, key_to_redeem)
    await menu(update, context)
    return ConversationHandler.END


async def process_key_logic(update, context, key_to_redeem):
    user_info_obj = update.effective_user
    user_id = str(user_info_obj.id)

    if is_user_banned(user_id):
        await update.effective_message.reply_text(
            get_ban_message(user_id), parse_mode="Markdown"
        )
        return
    if is_user_active(user_id):
        await update.effective_message.reply_text(
            "✅ You already have an active key."
        )
        return

    key_data = generated_keys.get(key_to_redeem)
    if key_data and time.time() - key_data.get("created_at", 0) <= 86400:
        user_data[user_id] = {
            "key": key_to_redeem,
            "redeemed_at": time.time(),
            "duration": key_data.get("duration"),
            "username": user_info_obj.username or user_info_obj.first_name,
            "last_gen_time": 0,
            "generation_count": 0,
        }
        del generated_keys[key_to_redeem]
        save_data(USER_DATA_FILE, user_data)
        save_data(GENERATED_KEYS_FILE, generated_keys)
        validity = get_key_remaining_time(user_data[user_id])
        await update.effective_message.reply_text(
            f"🎉 **Key Redeemed Successfully!** 🎉\n\nYour access is now active.\n**Validity:** `{validity}`",
            parse_mode="Markdown",
        )
        admin_message = (
            f"**➕ New User Authenticated**\n\n"
            f"**User:** `@{user_info_obj.username or user_info_obj.first_name}`\n"
            f"**Access:** `{validity}`\n"
            f"**Key Used:** `{key_to_redeem}`"
        )
        await notify_admins(admin_message, context)
    else:
        if key_data:
            del generated_keys[key_to_redeem]
            save_data(GENERATED_KEYS_FILE, generated_keys)
            await update.effective_message.reply_text("❌ This key has expired.")
        else:
            await update.effective_message.reply_text(
                "❌ **Invalid Key**\nThe key you entered is invalid or has already been used."
            )


# --- ADMIN INFO COMMANDS ---
async def admin_list_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    stock_message = "📊 **Vault Stock Levels** 📊\n\n"
    all_keywords = sorted(
        [f.replace(".txt", "") for f in os.listdir(ACCOUNTS_FOLDER) if f.endswith(".txt")]
    )

    for keyword in all_keywords:
        file_path = os.path.join(ACCOUNTS_FOLDER, f"{keyword}.txt")
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = sum(1 for line in f if line.strip())
            stock_message += f"• **{keyword.upper()}**: `{lines:,}` units\n"
        except Exception:
            stock_message += f"• **{keyword.upper()}**: `Error reading file`\n"

    await query.edit_message_text(
        stock_message,
        parse_mode="Markdown",
        reply_markup=build_keyboard({"⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐀𝐃𝐌𝐈𝐍": "menu_admin"}),
    )


async def admin_list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    active_users = {
        uid: data for uid, data in user_data.items() if is_user_active(uid)
    }
    if not active_users:
        await query.edit_message_text(
            "👥 **Active User Roster** 👥\n\nNo active users found.",
            reply_markup=build_keyboard({"⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐀𝐃𝐌𝐈𝐍": "menu_admin"}),
        )
        return

    user_list_str = "👥 **Active User Roster** 👥\n\n"
    for uid, info in active_users.items():
        user_list_str += f"• `@{info.get('username', uid)}` - {get_key_remaining_time(info)}\n"
    await query.edit_message_text(
        user_list_str,
        parse_mode="Markdown",
        reply_markup=build_keyboard({"⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐀𝐃𝐌𝐈𝐍": "menu_admin"}),
    )


async def admin_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not keyword_usage:
        await query.edit_message_text(
            "📈 **Usage Statistics** 📈\n\nNo usage data recorded yet.",
            reply_markup=build_keyboard({"⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐀𝐃𝐌𝐈𝐍": "menu_admin"}),
        )
        return

    stats_msg = "📈 **Usage Statistics** 📈\n\n"
    sorted_keywords = sorted(
        keyword_usage.items(), key=lambda item: item[1], reverse=True
    )
    for keyword, count in sorted_keywords:
        stats_msg += f"• **{keyword.upper()}**: `{count}` generations\n"
    await query.edit_message_text(
        stats_msg,
        parse_mode="Markdown",
        reply_markup=build_keyboard({"⬅️ 𝐁𝐀𝐂𝐊 𝐓𝐎 𝐀𝐃𝐌𝐈𝐍": "menu_admin"}),
    )


# --- BROADCAST ---
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.edit_message_text("Please send the message you want to broadcast (text or photo).")
    return AWAITING_BROADCAST_CONTENT
async def process_broadcast_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    admin_user = update.message.from_user
    active_user_ids = {uid for uid in user_data if is_user_active(uid) and not is_user_banned(uid)} | {str(admin) for admin in ADMINS}
    sent_count = 0
    message_base = f"<b>ADMIN ANNOUNCEMENT!!</b>\n────────────────────\n{{content}}\n────────────────────\n<b>Messenger:</b> @{admin_user.username}"
    if update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
        for user_id in active_user_ids:
            try:
                await context.bot.send_photo(chat_id=user_id, photo=photo_file_id, caption=message_base.format(content=update.message.caption or ''), parse_mode="HTML")
                sent_count += 1; await asyncio.sleep(0.05)
            except Exception as e: logger.error(f"Broadcast photo failed for {user_id}: {e}")
    elif update.message.text:
        for user_id in active_user_ids:
            try:
                await context.bot.send_message(chat_id=user_id, text=message_base.format(content=update.message.text), parse_mode="HTML")
                sent_count += 1; await asyncio.sleep(0.05)
            except Exception as e: logger.error(f"Broadcast text failed for {user_id}: {e}")
    await update.message.reply_text(f"✅ Broadcast sent to {sent_count}/{len(active_user_ids)} users.")
    return ConversationHandler.END


# --- BLOCKLIST ---
async def blocklist_add_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.callback_query.edit_message_text(
        "**Add to Blocklist**\n\nPlease reply with the user to block using the format:\n`@username [duration] [unit] [reason...]`\n\n**Example:** `@someuser 7 days Spamming`"
    )
    return AWAITING_BLOCKLIST_ADD


async def process_blocklist_add(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    try:
        parts = update.message.text.split(maxsplit=3)
        if len(parts) < 3:
            raise ValueError("Invalid format")
        username, duration_val_str, unit = parts[0], parts[1], parts[2]
        reason = parts[3] if len(parts) > 3 else "Manual ban by admin."

        if not username.startswith("@"):
            raise ValueError("Username must start with @")
        user_id_to_ban = get_user_id_from_username(username)
        if not user_id_to_ban:
            await update.message.reply_text(
                f"❌ User '`{username}`' not found.", parse_mode="Markdown"
            )
            return ConversationHandler.END

        duration_val = int(duration_val_str)
        unit = unit.lower().rstrip("s")
        duration_map = {"minute": 60, "day": 86400, "year": 31536000}
        if unit not in duration_map:
            await update.message.reply_text(
                "❌ Invalid unit. Use: `minutes`, `days`, or `years`.",
                parse_mode="Markdown",
            )
            return AWAITING_BLOCKLIST_ADD

        ban_duration_seconds = duration_val * duration_map[unit]
        ban_time = time.time()
        banned_users[user_id_to_ban] = {
            "ban_time": ban_time,
            "lift_time": ban_time + ban_duration_seconds,
            "reason": reason,
        }
        save_data(BANNED_USERS_FILE, banned_users)
        await update.message.reply_text(
            f"✅ User `{username}` has been added to the blocklist for {duration_val} {unit}(s).",
            parse_mode="Markdown",
        )
    except (IndexError, ValueError) as e:
        logger.error(f"Error processing blocklist add: {e}")
        await update.message.reply_text(
            "Invalid format. Please use `@username [duration] [unit] [reason...]`.",
            parse_mode="Markdown",
        )
        return AWAITING_BLOCKLIST_ADD
    return ConversationHandler.END


async def blocklist_remove_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.callback_query.edit_message_text(
        "**Remove from Blocklist**\n\nPlease reply with the username to remove (e.g., `@username`)."
    )
    return AWAITING_BLOCKLIST_REMOVE


async def process_blocklist_remove(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    username_to_unban = update.message.text
    if not username_to_unban.startswith("@"):
        await update.message.reply_text(
            "Invalid format. Please provide a valid username starting with `@`."
        )
        return AWAITING_BLOCKLIST_REMOVE
    user_id_to_unban = get_user_id_from_username(username_to_unban)
    if not user_id_to_unban:
        await update.message.reply_text(
            f"❌ User '`{username_to_unban}`' not found.", parse_mode="Markdown"
        )
        return ConversationHandler.END
    if str(user_id_to_unban) in banned_users:
        del banned_users[str(user_id_to_unban)]
        save_data(BANNED_USERS_FILE, banned_users)
        await update.message.reply_text(
            f"✅ User `{username_to_unban}` removed from blocklist.",
            parse_mode="Markdown",
        )
        try:
            await context.bot.send_message(
                chat_id=int(user_id_to_unban), text="Your ban has been lifted by an admin."
            )
        except Exception as e:
            logger.error(f"Could not notify user {user_id_to_unban} about unban: {e}")
    else:
        await update.message.reply_text("❌ User is not on the blocklist.")
    return ConversationHandler.END


# --- TOOLS ---
async def merge_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["merged_content"] = []
    await update.callback_query.edit_message_text(
        "**Merge Tool**\n\nSend `.txt` files to combine them into one. Use `/save <filename.txt>` when you're finished.",
        parse_mode="Markdown",
    )
    return AWAITING_MERGE_FILES


async def receive_merge_files(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not (update.message.document and update.message.document.file_name.endswith(".txt")):
        await update.message.reply_text("⚠️ Please send only `.txt` files.")
        return AWAITING_MERGE_FILES
    try:
        file = await update.message.document.get_file()
        accounts = (await file.download_as_bytearray()).decode("utf-8").strip().splitlines()
        context.user_data.get("merged_content", []).extend(accounts)
        await update.message.reply_text(
            f"✅ Added **{len(accounts)}** lines.\nTotal lines: **{len(context.user_data['merged_content'])}**.",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    return AWAITING_MERGE_FILES


async def save_merged_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if len(context.args) < 1:
        await update.message.reply_text(
            "Usage: `/save <new_filename.txt>`", parse_mode="Markdown"
        )
        return AWAITING_MERGE_FILES
    filename = context.args[0]
    if not filename.endswith(".txt"):
        filename += ".txt"
    merged_content = context.user_data.get("merged_content", [])
    if not merged_content:
        await update.message.reply_text("No content to save.")
        return AWAITING_MERGE_FILES
    with open(filename, "w", encoding="utf-8") as f:
        for line in merged_content:
            f.write(line.strip() + "\n")
    try:
        with open(filename, "rb") as f:
            await context.bot.send_document(
                chat_id=update.message.chat_id,
                document=f,
                caption=(
                    f"🎉 **Merge Complete!**\n`{len(merged_content)}` total lines."
                ),
                parse_mode="Markdown",
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send file: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)
    context.user_data.pop("merged_content", None)
    return ConversationHandler.END


async def duplicate_remover_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.callback_query.edit_message_text(
        "**Duplicate Remover**\n\nPlease send the `.txt` file you wish to clean.",
        parse_mode="Markdown",
    )
    return AWAITING_DUPLICATE_REMOVER_FILE


async def process_duplicate_remover_file(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not (update.message.document and update.message.document.file_name.endswith(".txt")):
        await update.message.reply_text("⚠️ Please send a `.txt` file.")
        return AWAITING_DUPLICATE_REMOVER_FILE
    output_filename = ""
    try:
        document = update.message.document
        file = await document.get_file()
        lines = (await file.download_as_bytearray()).decode("utf-8", "ignore").strip().splitlines()
        original_count = len(lines)
        unique_lines = list(dict.fromkeys(lines))
        cleaned_count = len(unique_lines)
        removed_count = original_count - cleaned_count
        output_filename = f"cleaned_{document.file_name}"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(unique_lines))
        with open(output_filename, "rb") as f:
            await context.bot.send_document(
                chat_id=update.message.chat_id,
                document=f,
                caption=f"✅ **Cleaning Complete!**\n\n**Original:** `{original_count}`\n**Removed:** `{removed_count}`\n**Final:** `{cleaned_count}`",
                parse_mode="Markdown",
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        if output_filename and os.path.exists(output_filename):
            os.remove(output_filename)
    return ConversationHandler.END


async def url_remover_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.callback_query.edit_message_text(
        "**URL & Credential Extractor**\n\nPlease send the `.txt` file to process.",
        parse_mode="Markdown",
    )
    return AWAITING_URL_REMOVER_FILE


async def process_url_remover_file(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not (update.message.document and update.message.document.file_name.endswith(".txt")):
        await update.message.reply_text("⚠️ Please send a `.txt` file.")
        return AWAITING_URL_REMOVER_FILE

    output_filename = ""
    try:
        document = update.message.document
        file = await document.get_file()
        lines = (await file.download_as_bytearray()).decode("utf-8", "ignore").splitlines()
        original_count = len(lines)
        extracted_creds = []
        cred_pattern = re.compile(r"([^:]+:[^:]+)$")
        for line in lines:
            match = cred_pattern.search(line.strip())
            if match:
                extracted_creds.append(match.group(1))
        final_count = len(extracted_creds)
        output_filename = f"extracted_{document.file_name}"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(extracted_creds))
        with open(output_filename, "rb") as f:
            await context.bot.send_document(
                chat_id=update.message.chat_id,
                document=f,
                caption=(
                    f"✅ **Extraction Complete!**\n\n"
                    f"**Lines Processed:** `{original_count}`\n"
                    f"**Credentials Extracted:** `{final_count}`"
                ),
                parse_mode="Markdown",
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error processing file: {e}")
    finally:
        if output_filename and os.path.exists(output_filename):
            os.remove(output_filename)
    return ConversationHandler.END


# --- ADMIN COMMANDS ---
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMINS:
        return
    if not (
        update.message.reply_to_message
        and update.message.reply_to_message.document
        and update.message.reply_to_message.document.file_name.endswith(".txt")
    ):
        await update.message.reply_text(
            "Usage: Reply to a `.txt` file with `/add <keyword>`.",
            parse_mode="Markdown",
        )
        return
    if not context.args:
        await update.message.reply_text("Please specify a keyword.")
        return
    keyword = context.args[0].lower()
    file_path = os.path.join(ACCOUNTS_FOLDER, f"{keyword}.txt")

    try:
        file = await update.message.reply_to_message.document.get_file()
        content = (await file.download_as_bytearray()).decode("utf-8", "ignore")
        cleaned_lines_from_upload = {
            line.strip() for line in content.strip().splitlines() if line.strip()
        }

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                existing_lines = {line.strip() for line in f if line.strip()}
        else:
            existing_lines = set()

        combined_lines = sorted(list(existing_lines | cleaned_lines_from_upload))

        with open(file_path, "w", encoding="utf-8") as f:
            for line in combined_lines:
                f.write(line + "\n")

        await update.message.reply_text(
            f"✅ **Stock Updated**\n- **Keyword:** `{keyword.upper()}`\n- **Total Lines:** `{len(combined_lines):,}`",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Error in /add command: {e}")
        await update.message.reply_text(f"An error occurred: {e}")


async def generatekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMINS:
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "**Usage:** `/generatekey [count] [duration] [unit]`\n"
            "**Example:** `/generatekey 5 7 days` or `/generatekey 1 lifetime`",
            parse_mode="Markdown",
        )
        return
    try:
        count = int(context.args[0])
        if context.args[1].lower() == "lifetime":
            duration_seconds, validity_str = float("inf"), "LIFETIME"
        else:
            duration_val = int(context.args[1])
            unit = context.args[2].lower().rstrip("s")
            duration_map = {"day": 86400, "hour": 3600, "minute": 60}
            duration_seconds = duration_val * duration_map[unit]
            validity_str = f"{duration_val} {unit.upper()}(S)"

        keys_generated = []
        for _ in range(count):
            chars = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )
            key = f"𝙆𝘼𝙄-{chars[0:4]}-{chars[4:7]}-{chars[7:10]}"
            keys_generated.append(key)
            generated_keys[key] = {
                "duration": duration_seconds,
                "created_at": time.time(),
            }

        save_data(GENERATED_KEYS_FILE, generated_keys)
        keys_list_str = "\n".join([f"`{key}`" for key in keys_generated])
        await update.message.reply_text(
            f"🔑 **Access Keys Generated** 🔑\n\n{keys_list_str}\n\n**Validity:** `{validity_str}`",
            parse_mode="Markdown",
        )
    except (ValueError, IndexError):
        await update.message.reply_text("Invalid command format.")


async def deleteuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMINS:
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: /deleteuser <@username or user_id>"
        )
        return
    identifier = context.args[0]
    user_id = (
        get_user_id_from_username(identifier) if identifier.startswith("@") else identifier
    )
    if user_id and str(user_id) in user_data:
        del user_data[str(user_id)]
        save_data(USER_DATA_FILE, user_data)
        await update.message.reply_text(f"🗑️ User {identifier} has been deleted.")
    else:
        await update.message.reply_text("❌ User not found.")


async def revokeall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMINS:
        return
    generated_keys.clear()
    user_data.clear()
    save_data(GENERATED_KEYS_FILE, {})
    save_data(USER_DATA_FILE, {})
    await update.message.reply_text("🔥 All keys and user data have been purged.")


# ==================== MAIN SETUP ====================
def main():
    application = Application.builder().token(TOKEN).build()

    fallbacks = [
        CommandHandler("cancel", cancel_conversation),
        CommandHandler("menu", menu_in_conversation),
    ]

    redeem_conv = ConversationHandler(
        entry_points=[
            CommandHandler("redeem", redeemkey_start_cmd),
            CallbackQueryHandler(redeemkey_start_callback, pattern="^redeem_start$")
        ],
        states={
            AWAITING_REDEEM_KEY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_key_input)
            ]
        },
        fallbacks=fallbacks,
        per_message=False,
    )
    broadcast_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(broadcast_start, pattern='^broadcast_start$'),
    ],
    states={
        AWAITING_BROADCAST_CONTENT: [
            MessageHandler(
                filters.TEXT | filters.PHOTO,
                process_broadcast_content
            )
        ]
    },
        fallbacks=fallbacks,
        per_message=False,
    )
    blocklist_add_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(blocklist_add_start, pattern="^blocklist_add_start$")
        ],
        states={
            AWAITING_BLOCKLIST_ADD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_blocklist_add)
            ]
        },
        fallbacks=fallbacks,
        per_message=False,
    )
    blocklist_remove_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                blocklist_remove_start, pattern="^blocklist_remove_start$"
            )
        ],
        states={
            AWAITING_BLOCKLIST_REMOVE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, process_blocklist_remove
                )
            ]
        },
        fallbacks=fallbacks,
        per_message=False,
    )
    merge_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(merge_start, pattern="^merge_start$")],
        states={
            AWAITING_MERGE_FILES: [
                MessageHandler(filters.Document.TXT, receive_merge_files),
                CommandHandler("save", save_merged_file),
            ]
        },
        fallbacks=fallbacks,
        per_message=False,
    )
    duplicate_remover_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                duplicate_remover_start, pattern="^duplicate_remover_start$"
            )
        ],
        states={
            AWAITING_DUPLICATE_REMOVER_FILE: [
                MessageHandler(
                    filters.Document.TXT, process_duplicate_remover_file
                )
            ]
        },
        fallbacks=fallbacks,
        per_message=False,
    )
    url_remover_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(url_remover_start, pattern="^url_remover_start$")
        ],
        states={
            AWAITING_URL_REMOVER_FILE: [
                MessageHandler(filters.Document.TXT, process_url_remover_file)
            ]
        },
        fallbacks=fallbacks,
        per_message=False,
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("mykey", mykey_command))
    application.add_handler(CommandHandler("generatekey", generatekey))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("revokeall", revokeall))
    application.add_handler(CommandHandler("deleteuser", deleteuser))

    application.add_handler(redeem_conv)
    application.add_handler(broadcast_conv)
    application.add_handler(blocklist_add_conv)
    application.add_handler(blocklist_remove_conv)
    application.add_handler(merge_conv)
    application.add_handler(duplicate_remover_conv)
    application.add_handler(url_remover_conv)

    application.add_handler(CallbackQueryHandler(button_handler))

    os.makedirs("assets", exist_ok=True)
    os.makedirs(ACCOUNTS_FOLDER, exist_ok=True)

    logger.info("Digital Vault Bot is starting...")
    application.run_polling()


if __name__ == "__main__":
    main()
