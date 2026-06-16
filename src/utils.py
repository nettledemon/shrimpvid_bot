import ffmpeg
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from buttons import get_start_keyboard
from messages import (
    NOT_VIDEO_MESSAGE, NOT_LINK_MESSAGE,
    WAITING_FOR_BUTTON_MESSAGE,
    TOO_BIG_MESSAGE, VIDEO_STEP1, LINK_STEP1
)
from config import get_bot_token

# основная функция конвертации видео в кружочек
def convert_to_round_video(input_path: str, output_path: str = None, max_duration: int = 59,
                           video_bitrate: str = '512k', audio_bitrate: str = '128k') -> str:
    if output_path is None:
        output_path = Path(input_path).stem + "_circle.mp4"

    # длительность: первые max_duration секунд
    probe = ffmpeg.probe(input_path)
    duration = float(probe['format']['duration'])
    duration_param = min(duration, max_duration)

    # видео: скейл до 512, потом кроп центра
    video = ffmpeg.input(input_path, ss=0, t=duration_param).video
    video = ffmpeg.filter(video, 'scale', 512, 512, force_original_aspect_ratio='increase')
    video = ffmpeg.filter(video, 'crop', 512, 512)

    # аудио: кроп синх видео, формат телеграм
    audio = ffmpeg.input(input_path, ss=0, t=duration_param).audio
    audio = ffmpeg.filter(audio, 'aformat', sample_fmts='fltp', sample_rates='48000', channel_layouts='stereo')

    # сборка и кодирование
    stream = ffmpeg.output(
        video, audio, output_path,
        vcodec='libx264',
        video_bitrate=video_bitrate,
        acodec='aac',
        audio_bitrate=audio_bitrate,
        ar=48000,
        ac=2,
        preset='fast',
        **{'movflags': '+faststart'}
    )

    ffmpeg.run(stream, overwrite_output=True)
    return output_path

# обработка видео
async def handle_video_message(update: Update, context: ContextTypes.DEFAULT_TYPE, process_video_func):
    if context.user_data.get('state') != 'awaiting_video':
        await update.message.reply_text(WAITING_FOR_BUTTON_MESSAGE, reply_markup=get_start_keyboard())
        return

    # проверка, что вообще видео
    if not update.message.video:
        await update.message.reply_text(NOT_VIDEO_MESSAGE, reply_markup=get_start_keyboard())
        context.user_data['state'] = None
        return

    video = update.message.video

    # проверка размера
    max_size_mb = 20
    file_size_mb = video.file_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        await update.message.reply_text(TOO_BIG_MESSAGE.format(size=file_size_mb, max_size=max_size_mb),
                                        reply_markup=get_start_keyboard())
        context.user_data['state'] = None
        return

    # соо статуса
    status_msg = await update.message.reply_text(VIDEO_STEP1)
    context.user_data['state'] = None

    await process_video_func(
        bot_token=get_bot_token(),
        chat_id=update.effective_chat.id,
        file_id=video.file_id,
        status_message_id=status_msg.message_id
    )

# обработка присланной ссылки
async def handle_link_message(update: Update, context: ContextTypes.DEFAULT_TYPE, process_link_func):
    if context.user_data.get('state') != 'awaiting_link':
        await update.message.reply_text(WAITING_FOR_BUTTON_MESSAGE, reply_markup=get_start_keyboard())
        return

    url = update.message.text.strip()
    # проверка, что это ссылка
    if not (url.startswith('http://') or url.startswith('https://')):
        await update.message.reply_text(NOT_LINK_MESSAGE, reply_markup=get_start_keyboard())
        context.user_data['state'] = None
        return

    # соо статуса
    status_msg = await update.message.reply_text(LINK_STEP1)
    context.user_data['state'] = None

    await process_link_func(
        bot_token=get_bot_token(),
        chat_id=update.effective_chat.id,
        url=url,
        status_message_id=status_msg.message_id
    )