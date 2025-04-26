import json
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from database import cur
from config import support_username, keyboard
from telegram import ReplyKeyboardMarkup

reply_markup = ReplyKeyboardMarkup(
    keyboard,
    resize_keyboard=True,
    one_time_keyboard=False,
)

async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    cur.execute("SELECT subscription_end_date, configs, invite_code FROM users WHERE telegram_user_id = ?", (telegram_id,))
    row = cur.fetchone()
    if row:
        sub_date, configs, invite_code = row
        end_date = datetime.fromisoformat(sub_date)
        days_remaining = max((end_date - datetime.now()).days + 1, 0)
        await update.message.reply_text(f"""
وضعیت اشتراک: {" 🟢 فعال" if days_remaining > 0 else " 🔴 غیر فعال"}

زمان باقی مانده از اشتراک: {days_remaining} روز

در صورت تمایل جهت تمدید اشتراک به پشتیبانی ({support_username}) پیام دهید
        """, reply_markup=reply_markup)
    else:
        from .common import start
        await start(update, context)

async def show_invite_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    cur.execute("SELECT invite_code FROM users WHERE telegram_user_id = ?", (telegram_id,))
    row = cur.fetchone()
    if row:
        invite_code = row[0]

        await update.message.reply_text(f"""
کد دعوت شما: `{invite_code}`

در هر دعوت موفق، به ازای هر ماه خرید اشتراک توسط دوستتان 10 روز اشتراک رایگان هدیه میگیرید

از دوست خود بخواهید تا این کد را هنگام خرید به پشتیبانی اعلام کند
        """, reply_markup=reply_markup, parse_mode='MarkdownV2')
    else:
        from .common import start
        await start(update, context)

async def my_configs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    cur.execute("SELECT configs FROM users WHERE telegram_user_id = ?", (telegram_id,))
    row = cur.fetchone()
    if row:
        configs = json.loads(row[0])
        if configs:
            msg = ['📶🚀']
            for i, config in enumerate(configs, 1):
                msg.append(f"کانفیگ {i}:\n```\n{config}\n```")
            msg = "\n".join(msg)
        else:
            msg = "چیزی یافت نشد"
        await update.message.reply_text(msg, parse_mode="MarkdownV2", reply_markup=reply_markup)
    else:
        await update.message.reply_text("You're not registered.")
