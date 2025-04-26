from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import support_username, keyboard
from database import cur, conn
from utils import generate_invite_code
from .user_handlers import my_info
from datetime import datetime

reply_markup = ReplyKeyboardMarkup(
    keyboard,
    resize_keyboard=True,
    one_time_keyboard=False,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    full_name = update.effective_user.full_name
    cur.execute("SELECT * FROM users WHERE telegram_user_id = ?", (telegram_id,))
    user = cur.fetchone()
    if user:
        await my_info(update, context)
    else:
        invite_code = generate_invite_code()
        cur.execute("INSERT INTO users (telegram_user_id, subscription_end_date, configs, subs, invite_code) VALUES (?, ?, ?, ?, ?)",
                    (telegram_id, datetime.now().isoformat(), "[]", "[]", invite_code))
        conn.commit()
        await update.message.reply_text(f"""
سلام {full_name} عزیز!

به ربات مدیریت اشتراک فیلترشکن خوش آمدید

شما اشتراک فعالی ندارید، لطفا برای خرید اشتراک به پشتیبانی ({support_username}) پیام دهید
        """, reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "👤 وضعیت اشتراک":
        from .user_handlers import my_info
        await my_info(update, context)
    elif text == "📶 کانفیگ های من":
        from .user_handlers import my_configs
        await my_configs(update, context)
    elif text == "🎟️ کد دعوت":
        from .user_handlers import show_invite_code
        await show_invite_code(update, context)
