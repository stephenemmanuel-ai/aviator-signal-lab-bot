import os
import sqlite3
from datetime import datetime, timezone

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip()
}

REFERRAL_LINK = os.getenv("REFERRAL_LINK", "").strip()
PROMO_CODE = os.getenv("PROMO_CODE", "AVIATORLAB").strip()

FREE_CHANNEL_URL = os.getenv("FREE_CHANNEL_URL", "").strip()
DISCUSSION_GROUP_URL = os.getenv("DISCUSSION_GROUP_URL", "").strip()
VIP_GROUP_URL = os.getenv("VIP_GROUP_URL", "").strip()

DB_PATH = os.getenv("DB_PATH", "aviator.db")


# ============================================================
# DATABASE
# ============================================================

def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            first_seen TEXT,
            vip INTEGER DEFAULT 0
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def save_user(user):
    if not user:
        return

    conn = get_db()
    cur = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()

    cur.execute(
        """
        INSERT OR IGNORE INTO users
        (telegram_id, username, first_name, first_seen, vip)
        VALUES (?, ?, ?, ?, 0)
        """,
        (
            user.id,
            user.username,
            user.first_name,
            now,
        ),
    )

    cur.execute(
        """
        UPDATE users
        SET username = ?, first_name = ?
        WHERE telegram_id = ?
        """,
        (
            user.username,
            user.first_name,
            user.id,
        ),
    )

    conn.commit()
    conn.close()


def user_is_vip(telegram_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT vip FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )

    row = cur.fetchone()
    conn.close()

    return bool(row and row[0] == 1)


def set_user_vip(telegram_id, active=True):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR IGNORE INTO users
        (telegram_id, first_seen, vip)
        VALUES (?, ?, 0)
        """,
        (
            telegram_id,
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    cur.execute(
        """
        UPDATE users
        SET vip = ?
        WHERE telegram_id = ?
        """,
        (
            1 if active else 0,
            telegram_id,
        ),
    )

    conn.commit()
    conn.close()


def save_signal(signal_text):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO signals (text, created_at)
        VALUES (?, ?)
        """,
        (
            signal_text,
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    conn.commit()
    conn.close()


def get_latest_signal():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT text, created_at
        FROM signals
        ORDER BY id DESC
        LIMIT 1
        """
    )

    row = cur.fetchone()
    conn.close()

    return row


# ============================================================
# KEYBOARD HELPERS
# ============================================================

def main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎯 Free Signals",
                    callback_data="free",
                ),
                InlineKeyboardButton(
                    "👑 VIP Access",
                    callback_data="vip",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔗 Register",
                    callback_data="register",
                ),
                InlineKeyboardButton(
                    "📊 My Status",
                    callback_data="status",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🚀 Latest Signals",
                    callback_data="signals",
                ),
                InlineKeyboardButton(
                    "📜 Rules",
                    callback_data="rules",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🆘 Help",
                    callback_data="help",
                )
            ],
        ]
    )


def back_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Main Menu",
                    callback_data="menu",
                )
            ]
        ]
    )


# ============================================================
# /START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        save_user(update.effective_user)

    text = (
        "✈️ *WELCOME TO AVIATOR SIGNAL LAB!*\n\n"
        "🎯 Free Aviator analysis\n"
        "👑 VIP community access\n"
        "📊 Session updates & signals\n\n"
        "🔞 18+ only\n"
        "⚠️ Gambling involves risk.\n"
        "❌ No signal is guaranteed.\n\n"
        "Choose an option below:"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=main_keyboard(),
        )
    elif update.message:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=main_keyboard(),
        )


# ============================================================
# REGISTER
# ============================================================

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    buttons = []

    if REFERRAL_LINK:
        buttons.append(
            [
                InlineKeyboardButton(
                    "🔗 REGISTER WITH 1WIN",
                    url=REFERRAL_LINK,
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "⬅️ Main Menu",
                callback_data="menu",
            )
        ]
    )

    text = (
        "🔗 *REGISTRATION*\n\n"
        "Register through the Aviator Signal Lab referral link.\n\n"
        f"🎟 *Promo Code:* `{PROMO_CODE}`\n\n"
        "After registering, complete the applicable VIP "
        "eligibility requirements.\n\n"
        "⚠️ Only gamble with money you can afford to lose."
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ============================================================
# VIP
# ============================================================

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if user_is_vip(query.from_user.id):
        buttons = []

        if VIP_GROUP_URL:
            buttons.append(
                [
                    InlineKeyboardButton(
                        "👑 ENTER VIP GROUP",
                        url=VIP_GROUP_URL,
                    )
                ]
            )

        buttons.append(
            [
                InlineKeyboardButton(
                    "⬅️ Main Menu",
                    callback_data="menu",
                )
            ]
        )

        text = (
            "👑 *VIP ACCESS ACTIVE*\n\n"
            "🟢 Your VIP access is active.\n\n"
            "Use the button below to enter the VIP community."
        )

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    buttons = [
        [
            InlineKeyboardButton(
                "🔗 Register",
                callback_data="register",
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Check Status",
                callback_data="status",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Main Menu",
                callback_data="menu",
            )
        ],
    ]

    text = (
        "👑 *VIP COMMUNITY*\n\n"
        "Current VIP eligibility:\n\n"
        "1️⃣ Register through the Aviator Signal Lab "
        "1win referral link or promo code.\n\n"
        "2️⃣ Make a minimum first deposit of ₹1,500.\n\n"
        "Once the required registration and deposit "
        "are verified, VIP access can be activated.\n\n"
        "⚠️ This is a gambling community. "
        "No signal guarantees a win."
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ============================================================
# STATUS
# ============================================================

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if user_is_vip(query.from_user.id):
        buttons = []

        if VIP_GROUP_URL:
            buttons.append(
                [
                    InlineKeyboardButton(
                        "👑 ENTER VIP GROUP",
                        url=VIP_GROUP_URL,
                    )
                ]
            )

        buttons.append(
            [
                InlineKeyboardButton(
                    "⬅️ Main Menu",
                    callback_data="menu",
                )
            ]
        )

        text = (
            "📊 *VIP STATUS*\n\n"
            "🟢 *VIP ACCESS: ACTIVE*\n\n"
            "Your VIP access has been activated."
        )

    else:
        buttons = [
            [
                InlineKeyboardButton(
                    "🔗 Register",
                    callback_data="register",
                )
            ],
            [
                InlineKeyboardButton(
                    "👑 VIP Requirements",
                    callback_data="vip",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Main Menu",
                    callback_data="menu",
                )
            ],
        ]

        text = (
            "📊 *VIP STATUS*\n\n"
            "⚪ *VIP ACCESS: NOT ACTIVE*\n\n"
            "Your VIP registration/deposit requirements "
            "have not yet been verified."
        )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ============================================================
# FREE SIGNALS
# ============================================================

async def free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    buttons = []

    if FREE_CHANNEL_URL:
        buttons.append(
            [
                InlineKeyboardButton(
                    "🎯 OPEN FREE CHANNEL",
                    url=FREE_CHANNEL_URL,
                )
            ]
        )

    if DISCUSSION_GROUP_URL:
        buttons.append(
            [
                InlineKeyboardButton(
                    "💬 JOIN COMMUNITY",
                    url=DISCUSSION_GROUP_URL,
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "⬅️ Main Menu",
                callback_data="menu",
            )
        ]
    )

    text = (
        "🎯 *FREE AVIATOR SIGNALS*\n\n"
        "Follow the free channel for:\n"
        "• 📊 Session analysis\n"
        "• 🚀 Latest signals\n"
        "• 🕐 Session updates\n"
        "• 💬 Community discussion\n\n"
        "⚠️ Signals are analysis-based and "
        "are not guaranteed outcomes."
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ============================================================
# LATEST SIGNALS
# ============================================================

async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    latest = get_latest_signal()

    if latest:
        signal_text, created_at = latest

        text = (
            "🚀 *LATEST SIGNAL*\n\n"
            f"{signal_text}\n\n"
            "⚠️ No signal is guaranteed."
        )
    else:
        text = (
            "🚀 *LATEST SIGNALS*\n\n"
            "No signal has been posted yet.\n\n"
            "Check the free channel for the latest updates."
        )

    buttons = []

    if FREE_CHANNEL_URL:
        buttons.append(
            [
                InlineKeyboardButton(
                    "🎯 OPEN FREE CHANNEL",
                    url=FREE_CHANNEL_URL,
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "⬅️ Main Menu",
                callback_data="menu",
            )
        ]
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ============================================================
# RULES
# ============================================================

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "📜 *RULES & GUIDELINES*\n\n"
        "🔞 18+ only.\n\n"
        "⚠️ Gambling involves financial risk.\n\n"
        "❌ No signal is guaranteed.\n\n"
        "❌ Never chase losses.\n\n"
        "💰 Only use money you can afford to lose.\n\n"
        "🔐 Never share your password, OTP, UPI PIN, "
        "card PIN or other sensitive financial information.\n\n"
        "🤝 Respect other members and Telegram rules."
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=back_keyboard(),
    )


# ============================================================
# HELP
# ============================================================

async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "🆘 *HELP & SUPPORT*\n\n"
        "/start — ✈️ Main menu\n"
        "/free — 🎯 Free signals\n"
        "/vip — 👑 VIP access\n"
        "/register — 🔗 Registration\n"
        "/status — 📊 VIP status\n"
        "/signals — 🚀 Latest signal\n"
        "/rules — 📜 Rules\n"
        "/help — 🆘 Help\n\n"
        "For account or payment issues, use the "
        "appropriate official support channel."
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=back_keyboard(),
    )


# ============================================================
# CALLBACK MENU
# ============================================================

async def callback_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "✈️ *AVIATOR SIGNAL LAB*\n\n"
        "Choose an option below:"
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )


# ============================================================
# NORMAL COMMANDS
# ============================================================

async def command_free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    buttons = []

    if FREE_CHANNEL_URL:
        buttons.append(
            [
                InlineKeyboardButton(
                    "🎯 OPEN FREE CHANNEL",
                    url=FREE_CHANNEL_URL,
                )
            ]
        )

    if DISCUSSION_GROUP_URL:
        buttons.append(
            [
                InlineKeyboardButton(
                    "💬 JOIN COMMUNITY",
                    url=DISCUSSION_GROUP_URL,
                )
            ]
        )

    await update.message.reply_text(
        "🎯 *FREE AVIATOR SIGNALS*\n\n"
        "Follow the free channel for the latest updates.\n\n"
        "⚠️ Signals are not guaranteed.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def command_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    if user_is_vip(update.effective_user.id):
        buttons = []

        if VIP_GROUP_URL:
            buttons.append(
                [
                    InlineKeyboardButton(
                        "👑 ENTER VIP GROUP",
                        url=VIP_GROUP_URL,
                    )
                ]
            )

        await update.message.reply_text(
            "👑 *VIP ACCESS: ACTIVE*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        await update.message.reply_text(
            "👑 *VIP REQUIREMENTS*\n\n"
            "1️⃣ Register through our 1win referral link "
            "or promo code.\n\n"
            "2️⃣ Minimum first deposit: ₹1,500.\n\n"
            "Once verified, VIP access can be activated.\n\n"
            "Use /register to begin.\n\n"
            "⚠️ Gambling involves risk.",
            parse_mode="Markdown",
        )


async def command_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    buttons = []

    if REFERRAL_LINK:
        buttons.append(
            [
                InlineKeyboardButton(
                    "🔗 REGISTER WITH 1WIN",
                    url=REFERRAL_LINK,
                )
            ]
        )

    await update.message.reply_text(
        f"🔗 *1WIN REGISTRATION*\n\n"
        f"🎟 Promo Code: `{PROMO_CODE}`\n\n"
        "Use the referral link below to register.\n\n"
        "⚠️ Gambling involves risk.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def command_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    if user_is_vip(update.effective_user.id):
        await update.message.reply_text(
            "📊 VIP Status: 🟢 ACTIVE"
        )
    else:
        await update.message.reply_text(
            "📊 VIP Status: ⚪ NOT ACTIVE\n\n"
            "Complete the applicable VIP requirements "
            "and wait for verification."
        )


async def command_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    latest = get_latest_signal()

    if latest:
        await update.message.reply_text(
            "🚀 *LATEST SIGNAL*\n\n"
            f"{latest[0]}\n\n"
            "⚠️ No signal is guaranteed.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "🚀 No signal has been posted yet."
        )


async def command_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    await update.message.reply_text(
        "📜 *RULES*\n\n"
        "🔞 18+ only\n"
        "⚠️ Gambling involves risk\n"
        "❌ No guaranteed signals\n"
        "❌ Never chase losses\n"
        "🔐 Never share passwords, OTPs, UPI PINs "
        "or card details.",
        parse_mode="Markdown",
    )


async def command_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)

    await update.message.reply_text(
        "🆘 Use /start to open the Aviator Signal Lab menu."
    )


# ============================================================
# ADMIN — ACTIVATE VIP
# ============================================================

async def set_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/setvip TELEGRAM_USER_ID"
        )
        return

    try:
        telegram_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid Telegram user ID."
        )
        return

    set_user_vip(telegram_id, True)

    await update.message.reply_text(
        f"👑 VIP activated.\n\n"
        f"User ID: `{telegram_id}`",
        parse_mode="Markdown",
    )


# ============================================================
# ADMIN — REMOVE VIP
# ============================================================

async def remove_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/removevip TELEGRAM_USER_ID"
        )
        return

    try:
        telegram_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid Telegram user ID."
        )
        return

    set_user_vip(telegram_id, False)

    await update.message.reply_text(
        f"VIP removed.\n\n"
        f"User ID: `{telegram_id}`"
    )


# ============================================================
# ADMIN — POST SIGNAL
# ============================================================

async def post_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/postsignal 2.00x\n\n"
            "Example:\n"
            "/postsignal 2.35x"
        )
        return

    signal_text = " ".join(context.args)

    save_signal(signal_text)

    await update.message.reply_text(
        "🚀 Signal saved successfully.\n\n"
        f"🎯 {signal_text}\n\n"
        "⚠️ No signal is guaranteed."
    )


# ============================================================
# ADMIN — BROADCAST
# ============================================================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/broadcast Your message here"
        )
        return

    message = " ".join(context.args)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT telegram_id FROM users")
    users = cur.fetchall()

    conn.close()

    sent = 0

    for row in users:
        try:
            await context.bot.send_message(
                chat_id=row[0],
                text=message,
            )
            sent += 1
        except Exception:
            pass

    await update.message.reply_text(
        f"📢 Broadcast complete.\n\n"
        f"Delivered to: {sent} users."
    )


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("Telegram error:", context.error)


# ============================================================
# MAIN / RENDER WEBHOOK
# ============================================================

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    init_db()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # --------------------------------------------------------
    # COMMANDS
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("free", command_free)
    )

    application.add_handler(
        CommandHandler("vip", command_vip)
    )

    application.add_handler(
        CommandHandler("register", command_register)
    )

    application.add_handler(
        CommandHandler("status", command_status)
    )

    application.add_handler(
        CommandHandler("signals", command_signals)
    )

    application.add_handler(
        CommandHandler("rules", command_rules)
    )

    application.add_handler(
        CommandHandler("help", command_help)
    )

    # --------------------------------------------------------
    # ADMIN COMMANDS
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler("setvip", set_vip)
    )

    application.add_handler(
        CommandHandler("removevip", remove_vip)
    )

    application.add_handler(
        CommandHandler("postsignal", post_signal)
    )

    application.add_handler(
        CommandHandler("broadcast", broadcast)
    )

    # --------------------------------------------------------
    # BUTTON CALLBACKS
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            callback_menu,
            pattern="^menu$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            free,
            pattern="^free$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            vip,
            pattern="^vip$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            register,
            pattern="^register$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            status,
            pattern="^status$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            signals,
            pattern="^signals$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            rules,
            pattern="^rules$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            help_menu,
            pattern="^help$",
        )
    )

    application.add_error_handler(error_handler)

    # --------------------------------------------------------
    # RENDER CONFIGURATION
    # --------------------------------------------------------

    port = int(os.getenv("PORT", "10000"))

    render_url = os.getenv(
        "RENDER_EXTERNAL_URL",
        ""
    ).strip()

    if not render_url:
        raise RuntimeError(
            "RENDER_EXTERNAL_URL environment variable is missing."
        )

    webhook_url = f"{render_url}/telegram"

    print("----------------------------------------")
    print("Aviator Signal Lab bot starting")
    print("----------------------------------------")
    print(f"Webhook URL: {webhook_url}")
    print(f"Port: {port}")
    print("----------------------------------------")

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="telegram",
        webhook_url=webhook_url,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
