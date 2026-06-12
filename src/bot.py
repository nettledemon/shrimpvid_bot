from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍤 Отправь мне видео, и я сделаю из него кружочек!\n"
        "Требования: квадратное, не длиннее 59 секунд."
    )

def get_application(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    return app