"""
общие хелперы для фоновых задач
"""

from telegram import Bot
from telegram.error import BadRequest
from buttons import get_start_keyboard
from messages import FORBIDDEN_VOICE_MESSAGE


async def safe_edit(bot: Bot, chat_id: int, message_id: int, text: str) -> None:
    """
    безопасно редактирует соо, игнор ошибки 'Message is not modified'
    """

    try:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


async def send_video_note_safe(bot: Bot, chat_id: int, video_file, **kwargs) -> bool:
    """
    чек запрета юзера
    """

    try:
        await bot.send_video_note(chat_id, video_file, **kwargs)
        return True
    except BadRequest as e:
        if "Voice_messages_forbidden" in str(e):
            await bot.send_message(
                chat_id,
                FORBIDDEN_VOICE_MESSAGE,
                reply_markup=get_start_keyboard(),
            )
            return False
        raise
