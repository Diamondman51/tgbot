from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def after_start_keyboard():

    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Получить ссылки"), ],
    ], resize_keyboard=True)

    return keyboard


async def ask_notion():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data='yes')],
        [InlineKeyboardButton(text="Нет", callback_data='no')],
    ])
    

    return keyboard


async def ask_notion():
    keyboard = InlineKeyboardBuilder([
        [InlineKeyboardButton(text="Да", callback_data='yes')],
        [InlineKeyboardButton(text="Нет", callback_data='no')],
    ])
    

    return keyboard.adjust(2).as_markup()


async def change_notion():
    keyboard = InlineKeyboardBuilder([
        [InlineKeyboardButton(text="Да", callback_data='yes')],
        [InlineKeyboardButton(text="Нет", callback_data='no')],
    ])
    

    return keyboard.adjust(2).as_markup()
