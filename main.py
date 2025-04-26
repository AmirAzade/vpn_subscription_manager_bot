import sqlite3
import random
import string
from datetime import datetime, timedelta
from telegram import Update, InputFile, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import json
import os

BOT_TOKEN = "7501098148:AAFX1gXLHpNUqjYAqPPbF1LIgC50nl9McxQ"
OWNER_USER_ID = "1279238936"
support_username = "@AmirrAzade"

keyboard = [
    ["👤 وضعیت اشتراک", "📶 کانفیگ های من"],
    ["🎟️ کد دعوت"],
]
reply_markup = ReplyKeyboardMarkup(
    keyboard,
    resize_keyboard=True,
    one_time_keyboard=False,
)


# Connect to SQLite
conn = sqlite3.connect("users.db", check_same_thread=False)
cur = conn.cursor()

# Create users table

cur.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id TEXT UNIQUE,
    subscription_end_date TEXT,
    configs TEXT,
    subs TEXT,
    invite_code TEXT UNIQUE
)
''')
conn.commit()


def generate_invite_code():
    return ''.join(random.choices(string.ascii_lowercase, k=5))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    

    telegram_id = str(update.effective_user.id)
    full_name = update.effective_user.full_name
    cur.execute("SELECT * FROM users WHERE telegram_user_id = ?", (telegram_id,))
    user = cur.fetchone()
    if user:
        await my_info(update, context)
        # await update.message.reply_text("You're already registered!")
    else:
        invite_code = generate_invite_code()
        cur.execute("INSERT INTO users (telegram_user_id, subscription_end_date, configs, subs, invite_code) VALUES (?, ?, ?, ?, ?)",
                    (telegram_id, (datetime.now()).isoformat(), "[]", "[]", invite_code))
        conn.commit()
        await update.message.reply_text(f"""
سلام {full_name} عزیز!

به ربات مدیریت اشتراک فیلترشکن خوش آمدید

شما اشتراک فعالی ندارید، لطفا برای خرید اشتراک به پشتیبانی ({support_username}) پیام دهید
        """, reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "👤 وضعیت اشتراک":
        await my_info(update, context)
    elif text == "📶 کانفیگ های من":
        await my_configs(update, context)
    elif text == "🎟️ کد دعوت":
        await show_invite_code(update, context)
        
# ========== ADMIN COMMANDS ==========

async def send_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != OWNER_USER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if os.path.exists("users.db"):
        with open("users.db", "rb") as db_file:
            await context.bot.send_document(chat_id=OWNER_USER_ID, document=InputFile(db_file), filename="users.db")
    else:
        await update.message.reply_text("⚠️ users.db file not found.")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != OWNER_USER_ID:
        return
    cur.execute("SELECT telegram_user_id, subscription_end_date FROM users")
    data = cur.fetchall()
    msg = []
    for uid, date in data:
        # Parse the subscription end date and calculate days remaining
        end_date = datetime.fromisoformat(date)
        days_remaining = (end_date - datetime.now()).days
        msg.append(f"{uid} - ({days_remaining+1} days)")
    msg = "\n".join(msg)
    await update.message.reply_text(f"Users:\n{msg}")


async def extend_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != OWNER_USER_ID:
        return
    try:
        target_id, days = context.args[0], int(context.args[1])
        cur.execute("SELECT subscription_end_date, configs, invite_code FROM users WHERE telegram_user_id = ?", (target_id,))
        row = cur.fetchone()
        if row:
            sub_date, configs, invite_code = row
            # Calculate new subscription end date
            new_date = max(datetime.fromisoformat(row[0]), datetime.now()) + timedelta(days=days)
            cur.execute("UPDATE users SET subscription_end_date = ? WHERE telegram_user_id = ?", (new_date.isoformat(), target_id))
            conn.commit()
            
            if(days > 0):
                # Send "you got some sub" message to target_id
                try:
                    await context.bot.send_message(
                        chat_id=target_id,
                        text=f"🎉 تبریک!\n\n{days} روز به اشتراک شما اضافه شد"
                    )
                    
                    # Send subscription status (reusing my_info logic)
                    end_date = datetime.fromisoformat(new_date.isoformat())
                    days_remaining = max((end_date - datetime.now()).days + 1, 0)
                    await context.bot.send_message(
                        chat_id=target_id,
                        text=f"""وضعیت اشتراک: {" 🟢 فعال" if days_remaining > 0 else " 🔴 غیر فعال"}\n\nزمان باقی مانده از اشتراک: {days_remaining} روز\n\nدر صورت تمایل جهت تمدید اشتراک به پشتیبانی ({support_username}) پیام دهید"""
                    )
                except Exception as e:
                    await update.message.reply_text(f"🟢Extended {target_id}'s subscription by {days} days, but 🔴failed to notify user: {str(e)}")
                    return

                await update.message.reply_text(f"🟢Extended {target_id}'s subscription by {days} days and 🟢notified user.")
            else:
                await update.message.reply_text(f"🟢Extended {target_id}'s subscription by {days} days but 🔴failed to notified user because days <= 0.")
        else:
            await update.message.reply_text("🔴User not found.")
    except:
        await update.message.reply_text("🔴🔴 Usage: /extend_subscription <telegram_user_id> <days>")


async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != OWNER_USER_ID:
        return

    try:
        telegram_id, config_str = context.args[0], "".join(context.args[1])
        # telegram_id = str(update.effective_user.id)
        # config_str = " ".join(context.args)
        cur.execute("SELECT configs FROM users WHERE telegram_user_id = ?", (telegram_id,))
        row = cur.fetchone()
        if row:
            import json
            configs = json.loads(row[0])
            configs.append(config_str)
            cur.execute("UPDATE users SET configs = ? WHERE telegram_user_id = ?", (json.dumps(configs), telegram_id))
            conn.commit()
            await update.message.reply_text("Config added.")
        else:
            await update.message.reply_text("You're not registered.")
    except:
        await update.message.reply_text("🔴🔴 Usage: /add_config <telegram_user_id> <config>")

async def clear_configs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != OWNER_USER_ID:
        return

    try:
        telegram_id = context.args[0]
        cur.execute("SELECT configs FROM users WHERE telegram_user_id = ?", (telegram_id,))
        row = cur.fetchone()
        if row:
            import json
            cur.execute("UPDATE users SET configs = ? WHERE telegram_user_id = ?", ("[]", telegram_id))
            conn.commit()
            await update.message.reply_text(f"Configs cleared for user {telegram_id}.")
        else:
            await update.message.reply_text("User not found.")
    except:
        await update.message.reply_text("🔴🔴 Usage: /clear_configs <telegram_user_id>")

# ========== USER COMMANDS ==========

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
        await start(update, context)




async def my_configs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    cur.execute("SELECT configs FROM users WHERE telegram_user_id = ?", (telegram_id,))
    row = cur.fetchone()
    if row:
        configs = json.loads(row[0])
        if configs:
            # Build formatted message with numbered configs
            msg = ['📶🚀']
            for i, config in enumerate(configs, 1):
                msg.append(f"کانفیگ {i}:\n```\n{config}\n```")
            msg = "\n".join(msg)
        else:
            msg = "چیزی یافت نشد"
        await update.message.reply_text(msg, parse_mode="MarkdownV2", reply_markup=reply_markup)
    else:
        await update.message.reply_text("You're not registered.")


# ========== MAIN APP ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()


    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("my_info", my_info))
    app.add_handler(CommandHandler("my_configs", my_configs))
    app.add_handler(CommandHandler("add_config", add_config))
    app.add_handler(CommandHandler("list_users", list_users))
    app.add_handler(CommandHandler("invite_code", show_invite_code))
    app.add_handler(CommandHandler("clear_configs", clear_configs))
    app.add_handler(CommandHandler("extend_subscription", extend_subscription))

    app.add_handler(CommandHandler("senddb", send_database))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()