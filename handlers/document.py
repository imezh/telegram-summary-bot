from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.document_parser import parse_pdf, parse_docx, parse_txt
from services.deepseek import summarize
from .states import CHOOSING, WAITING_DOCUMENT

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

BACK_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔙 Вернуться в меню", callback_data="menu")],
])

SUPPORTED_MIME = {
    "application/pdf": parse_pdf,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": parse_docx,
    "text/plain": parse_txt,
}


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    doc = update.message.document

    if doc.file_size and doc.file_size > MAX_FILE_SIZE:
        await update.message.reply_text(
            "❌ Файл слишком большой (максимум 20 МБ). Попробуй другой файл.",
            reply_markup=BACK_KEYBOARD,
        )
        return WAITING_DOCUMENT

    mime = doc.mime_type or ""
    parser = SUPPORTED_MIME.get(mime)

    # Try to detect by filename extension if mime not matched
    if parser is None and doc.file_name:
        name = doc.file_name.lower()
        if name.endswith(".pdf"):
            parser = parse_pdf
        elif name.endswith(".docx"):
            parser = parse_docx
        elif name.endswith(".txt"):
            parser = parse_txt

    if parser is None:
        await update.message.reply_text(
            "❌ Неподдерживаемый формат. Отправь PDF, DOCX или TXT файл.",
            reply_markup=BACK_KEYBOARD,
        )
        return WAITING_DOCUMENT

    processing_msg = await update.message.reply_text("⏳ Обрабатываю файл...")

    try:
        file = await doc.get_file()
        data = bytes(await file.download_as_bytearray())
        text = parser(data)

        if not text.strip():
            await processing_msg.edit_text(
                "❌ Не удалось извлечь текст из файла. Возможно, файл пустой или содержит только изображения.",
                reply_markup=BACK_KEYBOARD,
            )
            return WAITING_DOCUMENT

        await processing_msg.edit_text("🤖 Создаю саммари...")
        summary = await summarize(text)

        await processing_msg.delete()
        await update.message.reply_text(
            f"📄 **Саммари документа:**\n\n{summary}",
            parse_mode="Markdown",
            reply_markup=BACK_KEYBOARD,
        )

    except Exception as e:
        await processing_msg.edit_text(
            f"❌ Ошибка при обработке файла: {e}",
            reply_markup=BACK_KEYBOARD,
        )

    return WAITING_DOCUMENT
