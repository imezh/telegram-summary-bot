import asyncio
import os
import logging

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from handlers.states import CHOOSING, WAITING_DOCUMENT, WAITING_YOUTUBE
from handlers.start import start, menu_callback, back_to_menu
from handlers.document import handle_document
from handlers.youtube import handle_youtube

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]  # read by services/deepseek.py
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
PORT = int(os.environ.get("PORT", 8000))


def build_application() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                CallbackQueryHandler(menu_callback, pattern="^(doc|yt|menu)$"),
            ],
            WAITING_DOCUMENT: [
                MessageHandler(filters.Document.ALL, handle_document),
                CallbackQueryHandler(menu_callback, pattern="^menu$"),
            ],
            WAITING_YOUTUBE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube),
                CallbackQueryHandler(menu_callback, pattern="^menu$"),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
        ],
    )

    app.add_handler(conv_handler)
    return app


def main() -> None:
    # Python 3.10+ no longer auto-creates an event loop; set one explicitly
    # so that PTB's run_webhook (which calls asyncio.get_event_loop()) works.
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
