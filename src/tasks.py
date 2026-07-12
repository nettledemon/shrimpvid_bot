import sys
from pathlib import Path

# фикс импортов для воркера
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
from taskiq_redis import RedisStreamBroker, RedisAsyncResultBackend
from process_video import process_video_task
from process_link_video import process_link_video_task

# конфиг редиса (в докере хостнейм redis)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_URL = f"redis://{REDIS_HOST}:6379?socket_timeout=300&socket_connect_timeout=30&retry_on_timeout=true&health_check_interval=30"

result_backend: RedisAsyncResultBackend = RedisAsyncResultBackend(redis_url=REDIS_URL)
broker = RedisStreamBroker(url=REDIS_URL).with_result_backend(result_backend)


@broker.task(task_name="process_video")
async def process_video(
    bot_token: str, chat_id: int, file_id: str, status_message_id: int
):
    """
    задача: обработка загруженного видео
    """

    await process_video_task(bot_token, chat_id, file_id, status_message_id)


@broker.task(task_name="process_link_video")
async def process_link_video(
    bot_token: str, chat_id: int, url: str, status_message_id: int
):
    """
    задача: обработка видео по ссылке
    """

    await process_link_video_task(bot_token, chat_id, url, status_message_id)
