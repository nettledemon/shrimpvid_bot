from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import get_bot_token
from utils import get_again_keyboard, get_start_keyboard, handle_video_message
from messages import START_MESSAGE, START_BUTTON_MESSAGE
from tasks import process_video


# нажатие на инлайн-кнопку "Сделать ещё"
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "again":
        await query.message.reply_text(START_BUTTON_MESSAGE, reply_markup=None)
        context.user_data['waiting_for_video'] = True

    elif query.data == "start_processing":
        await query.message.reply_text(START_BUTTON_MESSAGE, reply_markup=None)
        context.user_data['waiting_for_video'] = True


# команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_MESSAGE, reply_markup=get_start_keyboard())
    # сброс флага, чтобы без кнопки ничего не работало
    context.user_data['waiting_for_video'] = False


# любое сообщение от юзера
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_video_message(update, context, process_video.kiq)


# сборка приложения
def get_application(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    return app