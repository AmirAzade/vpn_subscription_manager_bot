import sqlite3
import random
import string
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "7501098148:AAFX1gXLHpNUqjYAqPPbF1LIgC50nl9McxQ"
OWNER_USER_ID = "1279238936"

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
    cur.execute("SELECT * FROM users WHERE telegram_user_id = ?", (telegram_id,))
    user = cur.fetchone()
    if user:
        await update.message.reply_text("You're already registered!")
    else:
        invite_code = generate_invite_code()
        cur.execute("INSERT INTO users (telegram_user_id, subscription_end_date, configs, subs, invite_code) VALUES (?, ?, ?, ?, ?)",
                    (telegram_id, (datetime.now() + timedelta(days=30)).isoformat(), "[]", "[]", invite_code))
        conn.commit()
        await update.message.reply_text(f"Welcome! Your invite code is: {invite_code}")


# ========== ADMIN COMMANDS ==========

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != OWNER_USER_ID:
        return
    cur.execute("SELECT telegram_user_id, subscription_end_date FROM users")
    data = cur.fetchall()
    msg = "\n".join([f"{uid} - {date}" for uid, date in data])
    await update.message.reply_text(f"Users:\n{msg}")


async def extend_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != OWNER_USER_ID:
        return
    try:
        target_id, days = context.args[0], int(context.args[1])
        cur.execute("SELECT subscription_end_date FROM users WHERE telegram_user_id = ?", (target_id,))
        row = cur.fetchone()
        if row:
            new_date = datetime.fromisoformat(row[0]) + timedelta(days=days)
            cur.execute("UPDATE users SET subscription_end_date = ? WHERE telegram_user_id = ?", (new_date.isoformat(), target_id))
            conn.commit()
            await update.message.reply_text(f"Extended {target_id}'s subscription by {days} days.")
        else:
            await update.message.reply_text("User not found.")
    except:
        await update.message.reply_text("Usage: /extend_subscription <telegram_user_id> <days>")


# ========== USER COMMANDS ==========

async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    cur.execute("SELECT subscription_end_date, configs, invite_code FROM users WHERE telegram_user_id = ?", (telegram_id,))
    row = cur.fetchone()
    if row:
        sub_date, configs, invite_code = row
        await update.message.reply_text(f"Subscription ends: {sub_date}\nConfigs: {configs}\nInvite code: {invite_code}")
    else:
        await update.message.reply_text("You are not registered. Use /start.")


async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    config_str = " ".join(context.args)
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


async def my_configs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    cur.execute("SELECT configs FROM users WHERE telegram_user_id = ?", (telegram_id,))
    row = cur.fetchone()
    if row:
        import json
        configs = json.loads(row[0])
        msg = "\n".join(configs) if configs else "No configs."
        await update.message.reply_text(f"Your configs:\n{msg}")
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
    app.add_handler(CommandHandler("extend_subscription", extend_subscription))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()