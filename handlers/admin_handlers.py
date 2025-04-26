import os
import json
from datetime import datetime, timedelta
from telegram import Update, InputFile
from telegram.ext import ContextTypes
from database import cur, conn
from config import OWNER_USER_ID, support_username

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
            new_date = max(datetime.fromisoformat(row[0]), datetime.now()) + timedelta(days=days)
            cur.execute("UPDATE users SET subscription_end_date = ? WHERE telegram_user_id = ?", (new_date.isoformat(), target_id))
            conn.commit()
            
            if(days > 0):
                try:
                    await context.bot.send_message(
                        chat_id=target_id,
                        text=f"🎉 تبریک!\n\n{days} روز به اشتراک شما اضافه شد"
                    )
                    
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