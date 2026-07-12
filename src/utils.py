"""
обработчики
"""

import ffmpeg
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from buttons import get_start_keyboard
from messages import (
    NOT_VIDEO_MESSAGE,
    NOT_LINK_MESSAGE,
    WAITING_FOR_BUTTON_MESSAGE,
    TOO_BIG_MESSAGE,
    STEP1,
)
from config import get_bot_token


def convert_to_round_video(
    input_path: str,
    output_path: str | None = None,
    max_duration: int = 59,
    video_bitrate: str = "512k",
    audio_bitrate: str = "128k",
) -> str:
    """
    основная функция конвертации видео в кружочек
    """

    if output_path is None:
        output_path = Path(input_path).stem + "_circle.mp4"

    # проверяем длительность и наличие аудио
    try:
        probe = ffmpeg.probe(input_path)
    except ffmpeg.Error as e:
        raise RuntimeError(
            f"ffmpeg не может прочитать файл: {e.stderr.decode()}"
        ) from e

    duration = float(probe["format"]["duration"])
    duration_param = min(duration, max_duration)

    # проверяем, есть ли аудиопоток
    has_audio = any(
        stream.get("codec_type") == "audio" for stream in probe.get("streams", [])
    )

    # видео: скейл до 512, потом кроп центра
    video = ffmpeg.input(input_path, ss=0, t=duration_param).video
    video = ffmpeg.filter(
        video, "scale", 512, 512, force_original_aspect_ratio="increase"
    )
    video = ffmpeg.filter(video, "crop", 512, 512)

    if has_audio:
        # аудио: обрезаем синхронно с видео, формат телеграм
        audio = ffmpeg.input(input_path, ss=0, t=duration_param).audio
        audio = ffmpeg.filter(
            audio,
            "aformat",
            sample_fmts="fltp",
            sample_rates="48000",
            channel_layouts="stereo",
        )
        stream = ffmpeg.output(
            video,
            audio,
            output_path,
            vcodec="libx264",
            video_bitrate=video_bitrate,
            acodec="aac",
            audio_bitrate=audio_bitrate,
            ar=48000,
            ac=2,
            preset="fast",
            **{"movflags": "+faststart"},
        )
    else:
        stream = ffmpeg.output(
            video,
            output_path,
            vcodec="libx264",
            video_bitrate=video_bitrate,
            preset="fast",
            **{"movflags": "+faststart"},
        )

    try:
        ffmpeg.run(stream, overwrite_output=True)
    except ffmpeg.Error as e:
        raise RuntimeError(f"Ошибка конвертации видео: {e.stderr.decode()}") from e

    return output_path


async def handle_video_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    process_video_func,
):
    """
    обработка видео
    """

    assert update.message is not None
    assert update.effective_chat is not None
    assert context.user_data is not None

    if context.user_data.get("state") != "awaiting_video":
        await update.message.reply_text(
            WAITING_FOR_BUTTON_MESSAGE, reply_markup=get_start_keyboard()
        )
        return

    # проверка, что вообще видео
    if not update.message.video:
        await update.message.reply_text(
            NOT_VIDEO_MESSAGE, reply_markup=get_start_keyboard()
        )
        context.user_data["state"] = None
        return

    video = update.message.video

    # проверка размера
    max_size_mb = 20
    video = update.message.video
    assert video.file_size is not None
    file_size_mb = video.file_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        await update.message.reply_text(
            TOO_BIG_MESSAGE.format(size=file_size_mb, max_size=max_size_mb),
            reply_markup=get_start_keyboard(),
        )
        context.user_data["state"] = None
        return

    # соо статуса
    status_msg = await update.message.reply_text(STEP1)
    context.user_data["state"] = None

    await process_video_func(
        bot_token=get_bot_token(),
        chat_id=update.effective_chat.id,
        file_id=video.file_id,
        status_message_id=status_msg.message_id,
    )


async def handle_link_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, process_link_func
):
    """
    обработка присланной ссылки
    """

    assert update.message is not None
    assert update.effective_chat is not None
    assert context.user_data is not None

    if context.user_data.get("state") != "awaiting_link":
        await update.message.reply_text(
            WAITING_FOR_BUTTON_MESSAGE, reply_markup=get_start_keyboard()
        )
        return

    assert update.message.text is not None

    url = update.message.text.strip()
    # проверка, что это ссылка
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text(
            NOT_LINK_MESSAGE, reply_markup=get_start_keyboard()
        )
        context.user_data["state"] = None
        return

    # соо статуса
    status_msg = await update.message.reply_text(STEP1)
    context.user_data["state"] = None

    await process_link_func(
        bot_token=get_bot_token(),
        chat_id=update.effective_chat.id,
        url=url,
        status_message_id=status_msg.message_id,
    )
