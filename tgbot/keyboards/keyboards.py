from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


async def after_start_keyboard():

    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="По приоритету"), KeyboardButton(text="По категорию")],
    ], resize_keyboard=True,)

    return keyboard


# async def make_priorities(names: list):
#     keyboard = ReplyKeyboardBuilder()
#     for name in names:
#         keyboard.add(KeyboardButton(text=name))
#     return keyboard.adjust(3).as_markup()


async def make_categories_priorities(names: set):
    keyboard = ReplyKeyboardBuilder()
    for name in names:
        keyboard.add(KeyboardButton(text=name))
    return keyboard.adjust(3).as_markup(resize_keyboard=True)


async def ask_notion():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data='yes')],
        [InlineKeyboardButton(text="Нет", callback_data='no')],
    ])
    
    return keyboard


async def ask_notion_keyboard():
    keyboard = InlineKeyboardBuilder([
        [InlineKeyboardButton(text="Да", callback_data='yes')],
        [InlineKeyboardButton(text="Нет", callback_data='no')],
    ])
    return keyboard.adjust(2).as_markup()


async def change_notion_keyboard():
    keyboard = InlineKeyboardBuilder([
        [InlineKeyboardButton(text="Да, меняем", callback_data='change')],
        [InlineKeyboardButton(text="Нет, оставим", callback_data='save')],
    ])

    return keyboard.adjust(2).as_markup()

