import sys
from pathlib import Path

# корень проекта в путь поиска модулей
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import tempfile
from taskiq_redis import RedisStreamBroker, RedisAsyncResultBackend
from telegram import Bot
from utils import convert_to_round_video, get_again_keyboard
from messages import PROCESSING_COMPLETE_MESSAGE

REDIS_URL = "redis://redis:6379"  # для Docker, для локальной отладки замени на localhost

result_backend = RedisAsyncResultBackend(redis_url=REDIS_URL)
broker = RedisStreamBroker(url=REDIS_URL).with_result_backend(result_backend)


# выполняется воркером в фоне
@broker.task(task_name="process_video")
async def process_video(bot_token: str, chat_id: int, file_id: str):
    try:
        async with Bot(token=bot_token) as bot:
            with tempfile.TemporaryDirectory() as tmpdir:
                input_path = os.path.join(tmpdir, "input.mp4")
                output_path = os.path.join(tmpdir, "output.mp4")

                # скачать
                file = await bot.get_file(file_id)
                await file.download_to_drive(input_path)

                # конвертировать
                convert_to_round_video(input_path, output_path)

                # отправить
                with open(output_path, 'rb') as f:
                    await bot.send_video_note(chat_id, f, read_timeout=120, write_timeout=120)

                # кнопка "Сделать ещё"
                await bot.send_message(
                    chat_id,
                    PROCESSING_COMPLETE_MESSAGE,
                    reply_markup=get_again_keyboard()
                )

    except Exception as e:
        try:
            async with Bot(token=bot_token) as bot:
                await bot.send_message(chat_id, f"❌ Ошибка обработки видео: {e}")
        except Exception:
            pass