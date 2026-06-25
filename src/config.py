import os
from dotenv import load_dotenv
from pathlib import Path

# корень проекта
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# токен бота из .env
def get_bot_token() -> str:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN not found in .env")
    return token
