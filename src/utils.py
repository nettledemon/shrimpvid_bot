import ffmpeg
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from messages import NOT_VIDEO_MESSAGE, VIDEO_ACCEPTED_MESSAGE
from config import get_bot_token


# кнопка "Сделать ещё"
def get_again_keyboard() -> InlineKeyboardMarkup:
    button = InlineKeyboardButton(text="🍤 Сделать ещё", callback_data="again")
    return InlineKeyboardMarkup([[button]])


# проверка, подходит ли видео под требования телеграма
def is_valid_video(video) -> bool:
    if video.duration > 59:
        return False
    if video.width != video.height:
        return False
    return True


# понятное сообщение об ошибке
def get_validation_error_message(video) -> str | None:
    if video.duration > 59:
        return f"❌ Видео слишком длинное: {video.duration} секунд.\nМаксимум — 59 секунд."
    if video.width != video.height:
        return f"❌ Видео должно быть квадратным.\nТвоё видео имеет размеры {video.width}x{video.height}."
    return None


# конвертация обычного видео в телеграм-кружочек (квадрат 512, h264, aac)
def convert_to_round_video(input_path: str, output_path: str = None, max_duration: int = 59) -> str:
    if output_path is None:
        output_path = Path(input_path).stem + "_circle.mp4"

    probe = ffmpeg.probe(input_path)
    duration = float(probe['format']['duration'])
    duration_param = min(duration, max_duration)

    # обрезка и масштаб видео
    video = ffmpeg.input(input_path, ss=0, t=duration_param).video
    video = ffmpeg.filter(video, 'crop', 'min(iw,ih)', 'min(iw,ih)')
    video = ffmpeg.filter(video, 'scale', 512, 512)

    # обрезка аудио и перевод в формат, понятный телеграму
    audio = ffmpeg.input(input_path, ss=0, t=duration_param).audio
    audio = ffmpeg.filter(audio, 'aformat', sample_fmts='fltp', sample_rates='48000', channel_layouts='stereo')

    # склейка и кодировка
    stream = ffmpeg.output(
        video, audio, output_path,
        vcodec='libx264',
        video_bitrate='512k',
        acodec='aac',
        audio_bitrate='128k',
        ar=48000,
        ac=2,
        preset='fast',
        **{'movflags': '+faststart'}
    )

    ffmpeg.run(stream, overwrite_output=True)
    return output_path


# полная обработка (проверки + запуск)
async def handle_video_message(update: Update, context, process_video_func):
    if not update.message.video:
        await update.message.reply_text(NOT_VIDEO_MESSAGE)
        return

    video = update.message.video

    if not is_valid_video(video):
        error_msg = get_validation_error_message(video)
        await update.message.reply_text(error_msg)
        return

    await update.message.reply_text(VIDEO_ACCEPTED_MESSAGE)

    await process_video_func(
        bot_token=get_bot_token(),
        chat_id=update.effective_chat.id,
        file_id=video.file_id
    )