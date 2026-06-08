"""Telegram bot entrypoint for attendance management."""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

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


class DummyHandler(BaseHTTPRequestHandler):
    """Dummy web server to keep Render Web Service alive."""
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")


def run_dummy_server() -> None:
    """Start the dummy web server on the port provided by Render."""
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()


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

    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    # Start the dummy web server in a background thread
    threading.Thread(target=run_dummy_server, daemon=True).start()

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
