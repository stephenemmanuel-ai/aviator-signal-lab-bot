import os
import sqlite3
from datetime import datetime

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip()
}

REFERRAL_LINK = os.getenv("REFERRAL_LINK", "")
PROMO_CODE = os.getenv("PROMO_CODE", "AVIATORLAB")
FREE_CHANNEL_URL = os.getenv("FREE_CHANNEL_URL", "")
DISCUSSION_GROUP_URL = os.getenv("DISCUSSION_GROUP_URL", "")
VIP_GROUP_URL = os.getenv("VIP_GROUP_URL", "")
DB_PATH = os.getenv("DB_PATH", "aviator.db")


def db():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            first_seen TEXT,
            vip INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def save_user(user):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO users
        (telegram_id, username, first_seen, vip)
        VALUES (?, ?, ?, ?)
    """, (
        user.id,
        user.username,
        datetime.utcnow().isoformat(),
        0
    ))

    cur.execute("""
        UPDATE users
        SET username = ?
        WHERE telegram_id = ?
    """, (user.username, user.id))

    conn.commit()
    conn.close()


def is_vip(telegram_id):
    conn = db()
    cur = conn.cursor()

    cur.execute(
        "SELECT vip FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )

    row = cur.fetchone()
    conn.close()

    return bool(row and row[0] == 1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    keyboard = [
        [
            InlineKeyboardButton(
                "🎯 Free Signals",
                callback_data="free"
            ),
            InlineKeyboardButton(
                "👑 VIP Access",
                callback_data="vip"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔗 Register",
                callback_data="register"
            ),
            InlineKeyboardButton(
                "📊 My Status",
                callback_data="status"
            ),
        ],
        [
            InlineKeyboardButton(
                "🚀 Latest Signals",
                callback_data="signals"
            ),
            InlineKeyboardButton(
                "📜 Rules",
                callback_data="rules"
            ),
        ],
        [
            InlineKeyboardButton(
                "🆘 Help",
                callback_data="help"
            )
        ],
    ]

    text = (
        "✈️ *Welcome to Aviator Signal Lab!*\n\n"
        "Get access to our free Aviator analysis "
        "and VIP community.\n\n"
        "🔞 18+ only\n"
        "⚠️ Gambling involves risk. No signal is guaranteed.\n\n"
        "Choose an option below:"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = []

    if REFERRAL_LINK:
        keyboard.append([
            InlineKeyboardButton(
                "🔗 Register with 1win",
                url=REFERRAL_LINK
            )
        ])

    text = (
        "🔗 *1win Registration*\n\n"
        "To register through Aviator Signal Lab:\n\n"
        f"🎟 Promo Code: `{PROMO_CODE}`\n\n"
        "Use the registration link below and enter "
        "the promo code during registration if requested.\n\n"
        "⚠️ Only use funds you can afford to lose. "
        "Gambling outcomes are uncertain."
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if is_vip(query.from_user.id):
        keyboard = []

        if VIP_GROUP_URL:
            keyboard.append([
                InlineKeyboardButton(
                    "👑 Enter VIP Group",
                    url=VIP_GROUP_URL
                )
            ])

        text = (
            "👑 *VIP ACCESS ACTIVE*\n\n"
            "Your VIP access is currently active."
        )

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    text = (
        "👑 *VIP Community*\n\n"
        "Current VIP eligibility:\n\n"
        "1️⃣ Register through our 1win referral link "
        "or promo code.\n"
        "2️⃣ Make a minimum first deposit of ₹1,500.\n\n"
        "After the required registration and deposit "
        "are verified, VIP access can be activated.\n\n"
        "⚠️ This is a gambling community. No signal "
        "guarantees a win."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🔗 Register",
                callback_data="register"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Check Status",
                callback_data="status"
            )
        ],
    ]

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if is_vip(query.from_user.id):
        text = (
            "📊 *VIP Status*\n\n"
            "🟢 VIP ACCESS: ACTIVE\n\n"
            "You can enter the VIP community below."
        )

        keyboard = []

        if VIP_GROUP_URL:
            keyboard.append([
                InlineKeyboardButton(
                    "👑 Enter VIP Group",
                    url=VIP_GROUP_URL
                )
            ])

    else:
        text = (
            "📊 *VIP Status*\n\n"
            "⚪ VIP ACCESS: NOT ACTIVE\n\n"
            "Complete the registration and VIP "
            "eligibility requirements, then your "
            "status can be verified."
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔗 Register",
                    callback_data="register"
                )
            ],
            [
                InlineKeyboardButton(
                    "👑 VIP Requirements",
                    callback_data="vip"
                )
            ],
        ]

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = []

    if FREE_CHANNEL_URL:
        keyboard.append([
            InlineKeyboardButton(
                "🎯 Open Free Channel",
                url=FREE_CHANNEL_URL
            )
        ])

    if DISCUSSION_GROUP_URL:
        keyboard.append([
            InlineKeyboardButton(
                "💬 Join Community",
                url=DISCUSSION_GROUP_URL
            )
        ])

    text = (
        "🎯 *Free Aviator Signals*\n\n"
        "Follow the free channel for analysis, "
        "session updates and signals.\n\n"
        "⚠️ Signals are analysis-based and are not "
        "guaranteed outcomes."
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "🚀 *Latest Signals*\n\n"
        "No signal has been posted by the admin yet.\n\n"
        "Check the free channel for the latest updates."
    )

    keyboard = []

    if FREE_CHANNEL_URL:
        keyboard.append([
            InlineKeyboardButton(
                "🎯 Open Free Channel",
                url=FREE_CHANNEL_URL
            )
        ])

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "📜 *Rules & Guidelines*\n\n"
        "• 🔞 18+ only\n"
        "• Never gamble money you cannot afford to lose.\n"
        "• Signals are not guaranteed.\n"
        "• Never chase losses.\n"
        "• Do not share your account password, OTP, "
        "UPI PIN or card details with anyone.\n"
        "• VIP access is subject to verification.\n"
        "• Follow Telegram group rules."
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "🆘 *Help & Support*\n\n"
        "/start — Main menu\n"
        "/free — Free signals\n"
        "/vip — VIP access\n"
        "/register — Registration\n"
        "/status — VIP status\n"
        "/signals — Latest signals\n"
        "/rules — Rules\n"
        "/help — Help\n\n"
        "For account/payment issues, contact the "
        "appropriate official support channel."
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown"
    )


async def command_free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    keyboard = []

    if FREE_CHANNEL_URL:
        keyboard.append([
            InlineKeyboardButton(
                "🎯 Open Free Channel",
                url=FREE_CHANNEL_URL
            )
        ])

    await update.message.reply_text(
        "🎯 *Free Aviator Signals*\n\n"
        "Open the channel below for the latest updates.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def command_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    if is_vip(update.effective_user.id):
        keyboard = []

        if VIP_GROUP_URL:
            keyboard.append([
                InlineKeyboardButton(
                    "👑 Enter VIP Group",
                    url=VIP_GROUP_URL
                )
            ])

        await update.message.reply_text(
            "👑 *VIP ACCESS ACTIVE*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            "👑 VIP eligibility:\n\n"
            "1️⃣ Register through our 1win referral link "
            "or promo code.\n"
            "2️⃣ Minimum first deposit: ₹1,500.\n\n"
            "Use /register to begin.\n\n"
            "⚠️ Gambling involves risk. No signal is guaranteed."
        )


async def command_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    keyboard = []

    if REFERRAL_LINK:
        keyboard.append([
            InlineKeyboardButton(
                "🔗 Register with 1win",
                url=REFERRAL_LINK
            )
        ])

    await update.message.reply_text(
        f"🔗 *1win Registration*\n\n"
        f"🎟 Promo Code: `{PROMO_CODE}`\n\n"
        "Use the referral link below to register.\n\n"
        "⚠️ Gambling involves risk.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def command_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    if is_vip(update.effective_user.id):
        await update.message.reply_text(
            "📊 VIP Status: 🟢 ACTIVE"
        )
    else:
        await update.message.reply_text(
            "📊 VIP Status: ⚪ NOT ACTIVE\n\n"
            "Complete the VIP requirements and wait "
            "for verification."
        )


async def command_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    await update.message.reply_text(
        "🚀 Latest Signals\n\n"
        "No signal has been posted by the admin yet."
    )


async def command_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    await update.message.reply_text(
        "📜 Rules\n\n"
        "🔞 18+ only\n"
        "⚠️ Gambling involves risk.\n"
        "❌ No signal is guaranteed.\n"
        "❌ Never chase losses.\n"
        "🔐 Never share passwords, OTPs, UPI PINs "
        "or card details."
    )


async def command_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    await update.message.reply_text(
        "🆘 Help\n\n"
        "Use /start to open the main menu."
    )


async def set_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /setvip TELEGRAM_USER_ID"
        )
        return

    try:
        telegram_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "Invalid Telegram user ID."
        )
        return

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO users
        (telegram_id, first_seen, vip)
        VALUES (?, ?, 0)
    """, (
        telegram_id,
        datetime.utcnow().isoformat()
    ))

    cur.execute("""
        UPDATE users
        SET vip = 1
        WHERE telegram_id = ?
    """, (telegram_id,))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"👑 VIP activated for `{telegram_id}`",
        parse_mode="Markdown"
    )


async def remove_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /removevip TELEGRAM_USER_ID"
        )
        return

    try:
        telegram_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "Invalid Telegram user ID."
        )
        return

    conn = db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET vip = 0 WHERE telegram_id = ?",
        (telegram_id,)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"Removed VIP access for `{telegram_id}`",
        parse_mode="Markdown"
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured.")

    init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("free", command_free))
    application.add_handler(CommandHandler("vip", command_vip))
    application.add_handler(CommandHandler("register", command_register))
    application.add_handler(CommandHandler("status", command_status))
    application.add_handler(CommandHandler("signals", command_signals))
    application.add_handler(CommandHandler("rules", command_rules))
    application.add_handler(CommandHandler("help", command_help))

    application.add_handler(CommandHandler("setvip", set_vip))
    application.add_handler(CommandHandler("removevip", remove_vip))

    application.add_handler(CallbackQueryHandler(start, pattern="^start$"))
    application.add_handler(CallbackQueryHandler(free, pattern="^free$"))
    application.add_handler(CallbackQueryHandler(vip, pattern="^vip$"))
    application.add_handler(CallbackQueryHandler(register, pattern="^register$"))
    application.add_handler(CallbackQueryHandler(status, pattern="^status$"))
    application.add_handler(CallbackQueryHandler(signals, pattern="^signals$"))
    application.add_handler(CallbackQueryHandler(rules, pattern="^rules$"))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))

    print("Aviator Signal Lab bot started.")

    application.run_polling()


if __name__ == "__main__":
    main()
