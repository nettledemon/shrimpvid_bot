import sys
from pathlib import Path

# фикс импортов для воркера
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import asyncio
import tempfile
import yt_dlp
from taskiq_redis import RedisStreamBroker, RedisAsyncResultBackend
from telegram import Bot
from utils import convert_to_round_video
from buttons import get_start_keyboard
from messages import (
    PROCESSING_COMPLETE_MESSAGE, TOO_BIG_MESSAGE,
    VIDEO_STEP2, VIDEO_STEP3, VIDEO_STEP4, VIDEO_STEP5,
    LINK_STEP2, LINK_STEP3, LINK_STEP4, LINK_STEP5
)

# конфиг редиса (в докере хостнейм redis)
REDIS_URL = "redis://redis:6379"

result_backend = RedisAsyncResultBackend(redis_url=REDIS_URL)
broker = RedisStreamBroker(url=REDIS_URL).with_result_backend(result_backend)

# задача: обработка загруженного видео
@broker.task(task_name="process_video")
async def process_video(bot_token: str, chat_id: int, file_id: str, status_message_id: int):
    try:
        async with Bot(token=bot_token) as bot:
            # соо о скачивании
            await bot.edit_message_text(chat_id=chat_id, message_id=status_message_id, text=VIDEO_STEP2)
            await asyncio.sleep(0.7)
            with tempfile.TemporaryDirectory() as tmpdir:
                input_path = os.path.join(tmpdir, "input.mp4")
                output_path = os.path.join(tmpdir, "output.mp4")

                file = await bot.get_file(file_id)
                await file.download_to_drive(input_path)

                # соо о конвертации
                await bot.edit_message_text(chat_id=chat_id, message_id=status_message_id, text=VIDEO_STEP3)
                await asyncio.sleep(0.7)
                convert_to_round_video(input_path, output_path)

                # соо об обрезке углов
                await bot.edit_message_text(chat_id=chat_id, message_id=status_message_id, text=VIDEO_STEP4)
                await asyncio.sleep(0.7)

                # соо об отправке
                await bot.edit_message_text(chat_id=chat_id, message_id=status_message_id, text=VIDEO_STEP5)
                await asyncio.sleep(0.7)

                with open(output_path, 'rb') as f:
                    await bot.send_video_note(chat_id, f, read_timeout=120, write_timeout=120)

                # финальное соо с кнопками
                await bot.send_message(
                    chat_id,
                    PROCESSING_COMPLETE_MESSAGE,
                    reply_markup=get_start_keyboard()
                )
    except Exception as e:
        try:
            async with Bot(token=bot_token) as bot:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=status_message_id)
                except:
                    pass
                await bot.send_message(chat_id, f"❌ Ошибка обработки видео: {e}", reply_markup=get_start_keyboard())
        except Exception:
            pass

# задача: обработка видео по ссылке
@broker.task(task_name="process_link_video")
async def process_link_video(bot_token: str, chat_id: int, url: str, status_message_id: int):
    try:
        async with Bot(token=bot_token) as bot:
            # соо о скачивании
            await bot.edit_message_text(chat_id=chat_id, message_id=status_message_id, text=LINK_STEP2)
            await asyncio.sleep(0.7)
            with tempfile.TemporaryDirectory() as tmpdir:
                ydl_opts = {
                    'outtmpl': os.path.join(tmpdir, 'video.mp4'),
                    # ограничение 720p
                    'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]',
                    'merge_output_format': 'mp4',
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url, download=True)
                    filepath = os.path.join(tmpdir, 'video.mp4')

                # соо о конвертации
                await bot.edit_message_text(chat_id=chat_id, message_id=status_message_id, text=LINK_STEP3)
                await asyncio.sleep(0.7)
                output_path = os.path.join(tmpdir, "output.mp4")
                convert_to_round_video(filepath, output_path)

                # соо об обрезке углов
                await bot.edit_message_text(chat_id=chat_id, message_id=status_message_id, text=LINK_STEP4)
                await asyncio.sleep(0.7)

                # проверка размера после обработки
                output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                if output_size_mb > 20:
                    # еще сшакалить
                    convert_to_round_video(filepath, output_path, video_bitrate='256k', audio_bitrate='64k')
                    output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    if output_size_mb > 20:
                        await bot.delete_message(chat_id=chat_id, message_id=status_message_id)
                        await bot.send_message(
                            chat_id,
                            TOO_BIG_MESSAGE,
                            reply_markup=get_start_keyboard()
                        )
                        return

                # соо об отправке
                await bot.edit_message_text(chat_id=chat_id, message_id=status_message_id, text=LINK_STEP5)
                await asyncio.sleep(0.7)

                with open(output_path, 'rb') as f:
                    await bot.send_video_note(chat_id, f, read_timeout=120, write_timeout=120)

                # финальное соо с кнопками
                await bot.send_message(
                    chat_id,
                    PROCESSING_COMPLETE_MESSAGE,
                    reply_markup=get_start_keyboard()
                )
    except Exception as e:
        try:
            async with Bot(token=bot_token) as bot:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=status_message_id)
                except:
                    pass
                await bot.send_message(chat_id, f"❌ Ошибка обработки видео по ссылке: {e}", reply_markup=get_start_keyboard())
        except Exception:
            pass