from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from utils import handle_video_message, handle_link_message
from buttons import get_start_keyboard
from messages import START_MESSAGE, START_BUTTON_MESSAGE, WAITING_FOR_BUTTON_MESSAGE
from tasks import process_video, process_link_video

# обработка кнопок под сообщениями
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "start_file":
        context.user_data['state'] = 'awaiting_video'
        # клавиатуры нет без reply_markup
        await query.edit_message_text(text=START_BUTTON_MESSAGE)
    elif data == "start_link":
        context.user_data['state'] = 'awaiting_link'
        await query.edit_message_text(text="🔮 Отправь мне ссылку на видео, и я сделаю кружочек!\nПоддерживаются YouTube, TikTok и многие другие.")

# команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = None
    await update.message.reply_text(START_MESSAGE, reply_markup=get_start_keyboard())

# любое соо от юзера
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    if state == 'awaiting_video':
        await handle_video_message(update, context, process_video.kiq)
    elif state == 'awaiting_link':
        await handle_link_message(update, context, process_link_video.kiq)
    else:
        # если соо не по делу
        await update.message.reply_text(WAITING_FOR_BUTTON_MESSAGE, reply_markup=get_start_keyboard())

# сборка приложения
def get_application(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    return app