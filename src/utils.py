import ffmpeg
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from messages import (
    NOT_VIDEO_MESSAGE,
    VIDEO_ACCEPTED_MESSAGE,
    WAITING_FOR_BUTTON_MESSAGE,
    TOO_LONG_MESSAGE,
    TOO_BIG_MESSAGE
)
from config import get_bot_token


# кнопка "Сделать ещё"
def get_again_keyboard() -> InlineKeyboardMarkup:
    button = InlineKeyboardButton(text="🍤 Сделать ещё", callback_data="again")
    return InlineKeyboardMarkup([[button]])


# кнопка "Сделать кружочек" (в ответ на /start)
def get_start_keyboard() -> InlineKeyboardMarkup:
    button = InlineKeyboardButton(text="🍤 Сделать кружочек", callback_data="start_processing")
    return InlineKeyboardMarkup([[button]])


# конвертация видео в кружочек
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
    # если бот не ждет - жать кнопку
    if not context.user_data.get('waiting_for_video'):
        await update.message.reply_text(WAITING_FOR_BUTTON_MESSAGE, reply_markup=get_start_keyboard())
        return

    if not update.message.video:
        await update.message.reply_text(NOT_VIDEO_MESSAGE)
        return

    video = update.message.video

    # проверка длительности
    if video.duration > 59:
        await update.message.reply_text(TOO_LONG_MESSAGE.format(duration=video.duration))
        return

    # проверка размера
    max_size_mb = 20
    file_size_mb = video.file_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        await update.message.reply_text(TOO_BIG_MESSAGE.format(size=file_size_mb, max_size=max_size_mb))
        return

    await update.message.reply_text(VIDEO_ACCEPTED_MESSAGE)

    await process_video_func(
        bot_token=get_bot_token(),
        chat_id=update.effective_chat.id,
        file_id=video.file_id
    )

    # сброс флага
    context.user_data['waiting_for_video'] = False