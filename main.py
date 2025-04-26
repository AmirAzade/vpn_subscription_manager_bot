from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import BOT_TOKEN
from handlers.common import start, handle_buttons
from handlers.admin_handlers import send_database, list_users, extend_subscription, add_config, clear_configs
from handlers.user_handlers import my_info, my_configs, show_invite_code

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("my_info", my_info))
    app.add_handler(CommandHandler("my_configs", my_configs))
    app.add_handler(CommandHandler("invite_code", show_invite_code))
    app.add_handler(CommandHandler("add_config", add_config))
    app.add_handler(CommandHandler("list_users", list_users))
    app.add_handler(CommandHandler("clear_configs", clear_configs))
    app.add_handler(CommandHandler("extend_subscription", extend_subscription))
    app.add_handler(CommandHandler("senddb", send_database))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
