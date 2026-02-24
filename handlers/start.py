from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .states import CHOOSING, WAITING_DOCUMENT, WAITING_YOUTUBE

MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📄 Саммари документа", callback_data="doc")],
    [InlineKeyboardButton("🎥 Саммари YouTube", callback_data="yt")],
])

WELCOME_TEXT = (
    "👋 Привет! Я бот для создания саммари.\n\n"
    "Выбери, что хочешь сделать:"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(WELCOME_TEXT, reply_markup=MENU_KEYBOARD)
    return CHOOSING


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "doc":
        await query.edit_message_text(
            "📄 Отправь мне файл (PDF, DOCX или TXT) — я сделаю саммари.",
        )
        return WAITING_DOCUMENT

    if query.data == "yt":
        await query.edit_message_text(
            "🎥 Отправь ссылку на YouTube-видео — я сделаю саммари субтитров.",
        )
        return WAITING_YOUTUBE

    # "menu" callback — back to main menu
    await query.edit_message_text(WELCOME_TEXT, reply_markup=MENU_KEYBOARD)
    return CHOOSING


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(WELCOME_TEXT, reply_markup=MENU_KEYBOARD)
    return CHOOSING
