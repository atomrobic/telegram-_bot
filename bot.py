"""Telegram bot entrypoint for attendance management."""

from __future__ import annotations

import logging

from dotenv import load_dotenv
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from attendance_bot.config import load_settings
from attendance_bot.db import init_db
from attendance_bot.handlers import BotHandlers


def configure_logging() -> None:
    """Set up basic structured logging for local and hosted runs."""
    logging.basicConfig(
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        level=logging.INFO,
    )


def main() -> None:
    """Initialize dependencies and start the bot."""
    configure_logging()
    load_dotenv()
    settings = load_settings()
    init_db(settings.database_path)

    handlers = BotHandlers(settings)
    application = Application.builder().token(settings.bot_token).build()

    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("report", handlers.report))
    application.add_handler(CommandHandler("monthly", handlers.monthly))
    application.add_handler(CommandHandler("employees", handlers.employees))
    application.add_handler(CallbackQueryHandler(handlers.button_handler))

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
