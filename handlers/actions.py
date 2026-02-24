from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from services.deepseek import summarize, key_ideas
from services.document_parser import parse_pdf, parse_docx, parse_txt
from services.youtube_parser import get_transcript
from services.article_parser import fetch_article

_RETRY_KEYBOARD = InlineKeyboardMarkup([[
    InlineKeyboardButton("📝 Саммари", callback_data="action:summarize"),
    InlineKeyboardButton("💡 Ключевые идеи", callback_data="action:key_ideas"),
]])


async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    action = query.data.split(":")[1]  # summarize / key_ideas / cancel

    if action == "cancel":
        await query.edit_message_text("Отменено.")
        context.user_data.clear()
        return

    content_type = context.user_data.get("content_type")
    if not content_type:
        await query.edit_message_text("Сначала отправьте документ, ссылку или текст.")
        return

    await query.edit_message_text("⏳ Обрабатываю…")

    try:
        text = await _extract_text(content_type, context)
    except Exception as exc:
        await query.edit_message_text(f"❌ Ошибка при извлечении текста: {exc}")
        return

    try:
        if action == "summarize":
            result = await summarize(text)
        else:
            result = await key_ideas(text)
    except Exception as exc:
        await query.edit_message_text(f"❌ Ошибка при обработке: {exc}")
        return

    await query.edit_message_text("✅ Готово")

    chunks = [result[i:i + 4096] for i in range(0, len(result), 4096)]
    for idx, chunk in enumerate(chunks):
        is_last = idx == len(chunks) - 1
        kwargs = {"reply_markup": _RETRY_KEYBOARD if is_last else None}
        try:
            await query.message.reply_text(chunk, parse_mode="Markdown", **kwargs)
        except BadRequest:
            await query.message.reply_text(chunk, **kwargs)


async def _extract_text(content_type: str, context: ContextTypes.DEFAULT_TYPE) -> str:
    if content_type == "youtube":
        url = context.user_data["content_url"]
        return await _run_sync(get_transcript, url)

    if content_type == "article":
        url = context.user_data["content_url"]
        return await _run_sync(fetch_article, url)

    if content_type == "document":
        data: bytes = context.user_data["content_data"]
        mime: str = context.user_data.get("content_mime", "")
        filename: str = context.user_data.get("content_filename", "")
        return _parse_document(data, mime, filename)

    if content_type == "text":
        return context.user_data["content_text"]

    raise ValueError(f"Неизвестный тип контента: {content_type}")


def _parse_document(data: bytes, mime: str, filename: str) -> str:
    mime_map = {
        "application/pdf": parse_pdf,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": parse_docx,
        "text/plain": parse_txt,
    }
    if mime in mime_map:
        return mime_map[mime](data)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    ext_map = {"pdf": parse_pdf, "docx": parse_docx, "txt": parse_txt}
    if ext in ext_map:
        return ext_map[ext](data)
    raise ValueError(f"Неподдерживаемый формат файла: {filename or mime}")


async def _run_sync(func, *args):
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)
