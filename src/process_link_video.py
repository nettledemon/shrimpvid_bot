"""
обработка видео по ссылке
"""

import os
import asyncio
import tempfile
import yt_dlp
from telegram import Bot
from utils import convert_to_round_video
from buttons import get_start_keyboard
from messages import (
    PROCESSING_COMPLETE_MESSAGE,
    TOO_BIG_MESSAGE,
    STEP2,
    STEP3,
    STEP4,
    STEP5,
)
from task_utils import safe_edit, send_video_note_safe


async def process_link_video_task(
    bot_token: str, chat_id: int, url: str, status_message_id: int
):
    """
    скачивает видео по ссылке, конвертирует в кружок и отправляет
    """

    try:
        async with Bot(token=bot_token) as bot:
            await safe_edit(bot, chat_id, status_message_id, STEP2)
            await asyncio.sleep(0.7)
            with tempfile.TemporaryDirectory() as tmpdir:
                ydl_opts = {
                    "cookiefile": os.getenv("COOKIES_FILE"),
                    "outtmpl": os.path.join(tmpdir, "video.mp4"),
                    "format": "bestvideo+bestaudio/best",
                    "merge_output_format": "mp4",
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url, download=True)
                    filepath = os.path.join(tmpdir, "video.mp4")

                await safe_edit(bot, chat_id, status_message_id, STEP3)
                await asyncio.sleep(0.7)
                output_path = os.path.join(tmpdir, "output.mp4")
                convert_to_round_video(filepath, output_path)

                await safe_edit(bot, chat_id, status_message_id, STEP4)
                await asyncio.sleep(0.7)

                output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                if output_size_mb > 20:
                    convert_to_round_video(
                        filepath, output_path, video_bitrate="256k", audio_bitrate="64k"
                    )
                    output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    if output_size_mb > 20:
                        await bot.delete_message(
                            chat_id=chat_id, message_id=status_message_id
                        )
                        await bot.send_message(
                            chat_id, TOO_BIG_MESSAGE, reply_markup=get_start_keyboard()
                        )
                        return

                await safe_edit(bot, chat_id, status_message_id, STEP5)
                await asyncio.sleep(0.7)

                with open(output_path, "rb") as f:
                    success = await send_video_note_safe(
                        bot, chat_id, f, read_timeout=120, write_timeout=120
                    )
                if not success:
                    await bot.delete_message(
                        chat_id=chat_id, message_id=status_message_id
                    )
                    return

                await bot.send_message(
                    chat_id,
                    PROCESSING_COMPLETE_MESSAGE,
                    reply_markup=get_start_keyboard(),
                )
    except Exception as e:
        try:
            async with Bot(token=bot_token) as bot:
                try:
                    await bot.delete_message(
                        chat_id=chat_id, message_id=status_message_id
                    )
                except Exception:
                    pass
                await bot.send_message(
                    chat_id,
                    f"❌ Ошибка обработки видео по ссылке: {type(e).__name__}: {e}",
                    reply_markup=get_start_keyboard(),
                )
        except Exception:
            pass
