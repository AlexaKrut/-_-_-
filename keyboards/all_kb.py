from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

def main_kb():
    kb_list = [
        [KeyboardButton(text="♈️"), KeyboardButton(text="♉️"), KeyboardButton(text="♊️"), KeyboardButton(text="♋️")],
        [KeyboardButton(text="♌️"), KeyboardButton(text="♍️"), KeyboardButton(text="♎️"), KeyboardButton(text="♏️")],
        [KeyboardButton(text="♐️"), KeyboardButton(text="♑️"), KeyboardButton(text="♒️"), KeyboardButton(text="♓️")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)
    return keyboard