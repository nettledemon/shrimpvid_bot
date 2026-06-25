from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# инлайн-кнопки
def get_start_keyboard() -> InlineKeyboardMarkup:
    button_file = InlineKeyboardButton(
        text="🍤 Сделать кружочек", callback_data="start_file"
    )
    button_link = InlineKeyboardButton(
        text="🔮 Прислать ссылку", callback_data="start_link"
    )
    return InlineKeyboardMarkup([[button_file], [button_link]])
