import asyncio
import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from handlers.detect import detect_content
from handlers.actions import handle_action

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]  # read by services/deepseek.py
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
PORT = int(os.environ.get("PORT", 8000))

_WELCOME = (
    "Привет! Просто пришли мне:\n"
    "• YouTube-ссылку\n"
    "• Ссылку на статью\n"
    "• Документ (PDF, DOCX, TXT)\n"
    "• Или любой текст\n\n"
    "Я определю тип контента и предложу варианты обработки."
)


async def start_command(update: Update, _) -> None:
    await update.message.reply_text(_WELCOME)


def build_application() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_action, pattern="^action:"))
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.Document.ALL) & ~filters.COMMAND,
        detect_content,
    ))

    return app


def main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    application = build_application()
    logger.info("Starting webhook on port %d", PORT)
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
        url_path=BOT_TOKEN,
    )


if __name__ == "__main__":
    main()
