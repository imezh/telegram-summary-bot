import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled

from services.youtube_parser import get_transcript
from services.deepseek import summarize
from .states import WAITING_YOUTUBE

BACK_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔙 Вернуться в меню", callback_data="menu")],
])

YOUTUBE_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/\S+"
)


def _is_youtube_url(text: str) -> bool:
    return bool(YOUTUBE_PATTERN.search(text))


async def handle_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text or ""

    if not _is_youtube_url(text):
        await update.message.reply_text(
            "❌ Это не похоже на YouTube-ссылку. Отправь корректный URL.",
            reply_markup=BACK_KEYBOARD,
        )
        return WAITING_YOUTUBE

    processing_msg = await update.message.reply_text("⏳ Получаю субтитры...")

    try:
        transcript = get_transcript(text)
    except TranscriptsDisabled:
        await processing_msg.edit_text(
            "❌ Субтитры отключены для этого видео.",
            reply_markup=BACK_KEYBOARD,
        )
        return WAITING_YOUTUBE
    except NoTranscriptFound:
        await processing_msg.edit_text(
            "❌ Субтитры не найдены для этого видео (нет ни русских, ни английских).",
            reply_markup=BACK_KEYBOARD,
        )
        return WAITING_YOUTUBE
    except ValueError as e:
        await processing_msg.edit_text(
            f"❌ {e}",
            reply_markup=BACK_KEYBOARD,
        )
        return WAITING_YOUTUBE
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ Не удалось получить субтитры: {e}",
            reply_markup=BACK_KEYBOARD,
        )
        return WAITING_YOUTUBE

    try:
        await processing_msg.edit_text("🤖 Создаю саммари...")
        summary = await summarize(transcript)

        await processing_msg.delete()
        await update.message.reply_text(
            f"🎥 **Саммари видео:**\n\n{summary}",
            parse_mode="Markdown",
            reply_markup=BACK_KEYBOARD,
        )
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ Ошибка при создании саммари: {e}",
            reply_markup=BACK_KEYBOARD,
        )

    return WAITING_YOUTUBE
