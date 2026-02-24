import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

YOUTUBE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/\S+"
)


def _action_keyboard(cancel: bool = False) -> InlineKeyboardMarkup:
    row = [
        InlineKeyboardButton("📝 Саммари", callback_data="action:summarize"),
        InlineKeyboardButton("💡 Ключевые идеи", callback_data="action:key_ideas"),
    ]
    buttons = [row]
    if cancel:
        buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="action:cancel")])
    return InlineKeyboardMarkup(buttons)


async def detect_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message

    # Document upload
    if message.document:
        doc = message.document
        data = (await (await context.bot.get_file(doc.file_id)).download_as_bytearray())
        context.user_data["content_type"] = "document"
        context.user_data["content_data"] = bytes(data)
        context.user_data["content_filename"] = doc.file_name or ""
        context.user_data["content_mime"] = doc.mime_type or ""
        await message.reply_text(
            "📄 Документ получен. Что сделать?",
            reply_markup=_action_keyboard(),
        )
        return

    text = (message.text or "").strip()
    if not text:
        return

    # YouTube URL
    if YOUTUBE_RE.match(text):
        context.user_data["content_type"] = "youtube"
        context.user_data["content_url"] = text
        await message.reply_text(
            "🎥 YouTube-видео. Что сделать?",
            reply_markup=_action_keyboard(),
        )
        return

    # Any other URL
    if text.startswith("http://") or text.startswith("https://"):
        context.user_data["content_type"] = "article"
        context.user_data["content_url"] = text
        await message.reply_text(
            "📰 Статья из интернета. Что сделать?",
            reply_markup=_action_keyboard(),
        )
        return

    # Plain text
    context.user_data["content_type"] = "text"
    context.user_data["content_text"] = text
    await message.reply_text(
        "✏️ Текст получен. Обработать?",
        reply_markup=_action_keyboard(cancel=True),
    )
