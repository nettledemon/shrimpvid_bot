"""
обработка загруженного файла
"""

import os
import asyncio
import tempfile
from telegram import Bot
from utils import convert_to_round_video
from buttons import get_start_keyboard
from messages import (
    PROCESSING_COMPLETE_MESSAGE,
    STEP2,
    STEP3,
    STEP4,
    STEP5,
)
from task_utils import safe_edit, send_video_note_safe


async def process_video_task(
    bot_token: str, chat_id: int, file_id: str, status_message_id: int
):
    """скачивает видео из телеги, конвертирует в кружок и отправляет"""

    try:
        async with Bot(token=bot_token) as bot:
            await safe_edit(bot, chat_id, status_message_id, STEP2)
            await asyncio.sleep(0.7)
            with tempfile.TemporaryDirectory() as tmpdir:
                input_path = os.path.join(tmpdir, "input.mp4")
                output_path = os.path.join(tmpdir, "output.mp4")

                file = await bot.get_file(file_id)
                await file.download_to_drive(input_path)

                await safe_edit(bot, chat_id, status_message_id, STEP3)
                await asyncio.sleep(0.7)
                convert_to_round_video(input_path, output_path)

                await safe_edit(bot, chat_id, status_message_id, STEP4)
                await asyncio.sleep(0.7)

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
                    f"❌ Ошибка обработки видео: {type(e).__name__}: {e}",
                    reply_markup=get_start_keyboard(),
                )
        except Exception:
            pass
