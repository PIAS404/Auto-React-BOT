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

# =========================
# FIXED 14 EMOJIS ONLY
# =========================
EMOJIS = [
    "❤️",  # BOT 1
    "👀",  # BOT 2
    "😱",  # BOT 3
    "🤡",  # BOT 4
    "👻",  # BOT 5
    "💋",  # BOT 6
    "🙈",  # BOT 7
    "💯",  # BOT 8
    "👍",  # BOT 9
    "🥰",  # BOT 10
    "🎉",  # BOT 11
    "⚡",  # BOT 12
    "🔥",  # BOT 13
    "🌚",  # BOT 14
]

OWNER_USERNAME = os.getenv("OWNER_USERNAME", "@YourUsername")
RATE_LIMIT = 0.2


# =========================
# INLINE MENU
# =========================
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


# =========================
# REACTION HTTP FALLBACK
# =========================
async def http_set_reaction(bot_token: str, chat_id: int, message_id: int, emoji: str):
    url = f"https://api.telegram.org/bot{bot_token}/setMessageReaction"

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reaction": [
            {"type": "emoji", "emoji": emoji}
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            txt = await resp.text()
            return resp.status == 200 and '"ok":true' in txt.lower()


# =========================
# AUTO REACTION HANDLER
# =========================
async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message

    if not msg or (msg.from_user and msg.from_user.is_bot):
        return

    chat_id = msg.chat_id
    message_id = msg.message_id

    reacted_cache = context.application.bot_data.setdefault("cache", {})
    last_react = context.application.bot_data.setdefault("last", {})

    now = time.time()

    if now - last_react.get(chat_id, 0) < RATE_LIMIT:
        return

    if message_id in reacted_cache:
        return

    emoji = context.application.bot_data["emoji"]

    ok = await http_set_reaction(context.bot.token, chat_id, message_id, emoji)

    if ok:
        reacted_cache[message_id] = now
        last_react[chat_id] = now


# =========================
# COMMAND FUNCTIONS
# =========================
async def send_text(target, text):
    await target.reply_text(text, reply_markup=MAIN_MENU)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_text(update.message,
        "🤖 Auto Reaction Bot Activated!\n\n"
        "Add me to group and I react automatically."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_text(update.message,
        "📘 Help:\n"
        "Just add bot to group.\n"
        "It reacts automatically."
    )


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_text(update.message,
        "✅ Bot Status: Online\n⚡ Reaction Active"
    )


async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    t0 = time.time()

    sent = await update.message.reply_text("Pinging...", reply_markup=MAIN_MENU)

    latency = int((time.time() - t0) * 1000)

    await sent.edit_text(f"Pong! {latency} ms", reply_markup=MAIN_MENU)


async def support_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await send_text(update.message,
        f"Contact owner: {OWNER_USERNAME}"
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    msg = query.message

    data = query.data

    if data == "start":
        await start_cmd(update, context)
    elif data == "help":
        await help_cmd(update, context)
    elif data == "status":
        await status_cmd(update, context)
    elif data == "ping":
        await ping_cmd(update, context)
    elif data == "support":
        await support_cmd(update, context)


# =========================
# CREATE BOT APP
# =========================
def create_app(token: str, emoji: str):

    app = ApplicationBuilder().token(token).build()

    app.bot_data["emoji"] = emoji

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("support", support_cmd))

    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(MessageHandler(filters.ALL, on_message))

    return app


# =========================
# RUN 14 BOTS ONLY
# =========================
async def main():

    apps = []

    for i in range(14):

        token = os.getenv(f"BOT_{i+1}_TOKEN")

        if not token:
            raise SystemExit(f"Missing BOT_{i+1}_TOKEN")

        emoji = EMOJIS[i]

        app = create_app(token, emoji)

        apps.append(app)

        print(f"Loaded BOT {i+1} -> {emoji}")

    for app in apps:

        await app.initialize()

        await app.start()

        await app.updater.start_polling()

    print("All 14 bots running")

    await asyncio.Event().wait()


# =========================
# START
# =========================
if __name__ == "__main__":
    asyncio.run(main())
