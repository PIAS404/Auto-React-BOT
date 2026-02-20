import os
import time
import asyncio
import aiohttp
from typing import Dict, Tuple, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ---------- CONFIG ----------
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "@YourUsername")

# Fixed emojis for 14 bots (serial)
EMOJIS = [
    "❤️",  # 1
    "👀",  # 2
    "😱",  # 3
    "🤡",  # 4
    "👻",  # 5
    "💋",  # 6
    "🙈",  # 7
    "💯",  # 8
    "👍",  # 9
    "🥰",  # 10
    "🎉",  # 11
    "⚡",  # 12
    "🔥",  # 13
    "🌚",  # 14
]

RATE_LIMIT = 0.2

# try import ReactionType classes if present
try:
    from telegram import ReactionTypeEmoji  # type: ignore
    HAVE_REACTION_CLASSES = True
except Exception:
    HAVE_REACTION_CLASSES = False


# ----------------- INLINE MENU (UNCHANGED) -----------------
MAIN_MENU = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🚀 Start", callback_data="start"),
        InlineKeyboardButton("📘 Help", callback_data="help"),
    ],
    [
        InlineKeyboardButton("📊 Status", callback_data="status"),
        InlineKeyboardButton("⚠️ Ping", callback_data="ping"),
    ],
    [
        InlineKeyboardButton("🛠 Support", callback_data="support")
    ]
])


# ----------------- SHARED HELPERS (UNCHANGED TEXTS) -----------------
async def send_start_text(target_message, context):
    text = (
        "🤖 Auto Reaction Bot Activated!\n\n"
        "📌 Just add me to any group.\n"
        "📌 No admin permission required.\n"
        "📌 I will automatically react to every new message instantly.\n\n"
        "✨ Enjoy ultra-fast auto reactions!"
    )
    await target_message.reply_text(text, reply_markup=MAIN_MENU)


async def send_help_text(target_message, context):
    text = (
        "❓ Need Help?\n\n"
        "Here’s how to use this bot 👇\n\n"
        "1️⃣ Add the bot to your group\n"
        "2️⃣ No setup needed\n"
        "3️⃣ Every new message gets an instant auto-reaction\n"
        "4️⃣ Works 24/7 and ultra-fast\n\n"
        "⚙️ Commands:\n"
        "/start – Activate the bot\n"
        "/status – Check bot status\n"
        "/ping – Bot response test\n"
        "/support – Contact support\n"
    )
    await target_message.reply_text(text, reply_markup=MAIN_MENU)


async def send_status_text(target_message, context):
    text = (
        "📊 Bot Status\n\n"
        "✅ Auto Reaction: Active\n"
        "⚡ Speed: Ultra-Fast\n"
        "🟢 Server: Online\n"
        "🕒 Uptime: 24/7\n\n"
        "Everything is running perfectly! 🚀"
    )
    await target_message.reply_text(text, reply_markup=MAIN_MENU)


async def send_ping_text(target_message, context):
    t0 = time.time()
    sent = await target_message.reply_text("⚠ Ping!\n\n⏱️ Calculating response time...", reply_markup=MAIN_MENU)
    t1 = time.time()
    latency_ms = int((t1 - t0) * 1000)
    try:
        await sent.edit_text(f"⚠ Ping!\n\n⏱️ Response Time: {latency_ms} ms\n⚡ Status: Smooth & Fast", reply_markup=MAIN_MENU)
    except Exception:
        await target_message.reply_text(f"⚠ Ping!\n\n⏱️ Response Time: {latency_ms} ms\n⚡ Status: Smooth & Fast", reply_markup=MAIN_MENU)


async def send_support_text(target_message, context):
    owner = OWNER_USERNAME
    text = (
        "🛠️ Support Center\n\n"
        "If you need any help, feel free to contact:\n"
        f"👤 Owner: {owner}\n\n"
        "We are here to assist you 24/7 😊"
    )
    await target_message.reply_text(text, reply_markup=MAIN_MENU)


# ----------------- COMMAND HANDLERS (UNCHANGED BEHAVIOR) -----------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await send_start_text(update.message, context)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await send_help_text(update.message, context)

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await send_status_text(update.message, context)

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await send_ping_text(update.message, context)

async def support_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await send_support_text(update.message, context)


# ✅ FIXED CallbackQuery handler (এইটাই আগে ভাঙা ছিল)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()
    msg = query.message  # <-- এখানে reply দিতে হবে

    data = query.data
    if data == "start":
        await send_start_text(msg, context)
    elif data == "help":
        await send_help_text(msg, context)
    elif data == "status":
        await send_status_text(msg, context)
    elif data == "ping":
        await send_ping_text(msg, context)
    elif data == "support":
        await send_support_text(msg, context)
    else:
        await msg.reply_text("Unknown action.")


# ----------------- REACTION CORE (multi-bot safe) -----------------
async def try_set_via_library(bot, chat_id, message_id, payload) -> Tuple[bool, str]:
    try:
        await bot.set_message_reaction(chat_id=chat_id, message_id=message_id, reaction=payload)
        return True, "OK (keyword reaction)"
    except TypeError:
        pass
    except Exception as e:
        return False, f"ERROR (keyword) {type(e).__name__}: {e}"

    try:
        await bot.set_message_reaction(chat_id, message_id, payload)
        return True, "OK (positional)"
    except Exception as e:
        return False, f"ERROR (positional) {type(e).__name__}: {e}"


async def http_set_reaction(bot_token, chat_id, message_id, emoji: str):
    url = f"https://api.telegram.org/bot{bot_token}/setMessageReaction"
    payload = [{"type": "emoji", "emoji": emoji}]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "reaction": payload
            }, timeout=8) as resp:
                txt = await resp.text()
                return (resp.status == 200) and ('"ok":true' in txt.replace(" ", "").lower())
    except Exception:
        return False


async def try_send_reaction(bot, chat_id: int, message_id: int, emoji: str) -> bool:
    if HAVE_REACTION_CLASSES:
        try:
            r = ReactionTypeEmoji(emoji=emoji)  # type: ignore
            ok, _ = await try_set_via_library(bot, chat_id, message_id, [r])
            if ok:
                return True
        except Exception:
            pass

    payload = [{"type": "emoji", "emoji": emoji}]
    ok, _ = await try_set_via_library(bot, chat_id, message_id, payload)
    if ok:
        return True

    return await http_set_reaction(bot.token, chat_id, message_id, emoji)


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or (msg.from_user and msg.from_user.is_bot):
        return

    chat_id = msg.chat_id
    message_id = msg.message_id
    now = time.time()

    # per-bot caches (IMPORTANT: each bot keeps its own state)
    reacted_cache: Dict[int, float] = context.application.bot_data.setdefault("_reacted_cache", {})
    last_react: Dict[int, float] = context.application.bot_data.setdefault("_last_react", {})

    if now - last_react.get(chat_id, 0) < RATE_LIMIT:
        return
    if message_id in reacted_cache:
        return

    fixed_emoji = context.application.bot_data.get("FIXED_EMOJI", "👀")

    ok = await try_send_reaction(context.bot, chat_id, message_id, fixed_emoji)
    if ok:
        reacted_cache[message_id] = now
        last_react[chat_id] = now


def build_app(token: str, fixed_emoji: str):
    app = ApplicationBuilder().token(token).build()

    # store per-bot emoji
    app.bot_data["FIXED_EMOJI"] = fixed_emoji

    # commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("support", support_cmd))

    # inline buttons
    app.add_handler(CallbackQueryHandler(button_handler))

    # auto reaction
    app.add_handler(MessageHandler(filters.ALL & ~filters.StatusUpdate.ALL, on_message))

    return app


async def run_14_bots():
    apps = []
    for i in range(14):
        token = os.getenv(f"BOT_{i+1}_TOKEN")
        if not token or token.strip() == "":
            raise SystemExit(f"❌ ERROR: BOT_{i+1}_TOKEN environment variable not set.")
        apps.append(build_app(token, EMOJIS[i]))

    print(f"✅ Loaded {len(apps)} bots with fixed emojis.")

    # start all bots
    for app in apps:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)

    print("🚀 All 14 bots running... Press Ctrl+C to stop.")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(run_14_bots())