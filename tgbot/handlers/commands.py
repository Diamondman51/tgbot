from pprint import pprint
import re
from aiogram import types
from aiogram.fsm.context import FSMContext
import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy import exists, select
from tgbot.database.database import Links, User, session
from tgbot.keyboards.keyboards import *
from tgbot.notion.notion import create_page, create_page_data
from tgbot.states.states import GetLink, GetCategoryPriority, GetNotionDB

session = session

async def start_command_handler(message: types.Message, state: FSMContext):
    from_user = message.from_user

    # TODO need to make notion db changable
    # user = select(exists().where(User.tg_user_id == from_user.id))
    # user = await session().execute(user)
    # user = user.scalar()
    # if not user:
    greeting_text = f"Здравствуйте, {from_user.full_name}! У вас есть Notion?"
    keyboard = await ask_notion()
    await message.answer(greeting_text, reply_markup=keyboard)
    
    # else:
        

async def get_notion_db(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Отправьте Notion token", )
    await state.set_state(GetNotionDB.db_token)


async def get_notion_db_token(message: types.Message, state: FSMContext):
    await state.update_data(db_token=message.text)
    await message.answer("Отправьте Notion Database ID")
    await state.set_state(GetNotionDB.db_id)


async def get_notion_db_id(message: types.Message, state: FSMContext):
    await state.update_data(db_id=message.text)
    await message.answer('Спасибо, все готово')
    db = await state.get_data()
    async with session() as conn:
        user_id = message.from_user.id
        user = select(exists().where(User.tg_user_id == user_id))
        user = await conn.execute(user)
        user = user.scalar()
        if not user:
            db_token = db.get('db_token')
            db_id = db.get("db_id")
            new_user = User(tg_user_id=message.from_user.id, notion_db_token=db_token, notion_db_id=db_id)
            conn.add(new_user)
            await conn.commit()


    await state.clear()
    pprint(db)


async def no_notion_token(callback: types.CallbackQuery):
    async with session() as conn:
        user_id = callback.from_user.id
        user = select(exists().where(User.tg_user_id == user_id))
        user = await conn.execute(user)
        user = user.scalar()
        if not user:
            new_user = User(tg_user_id=callback.from_user.id)
            conn.add(new_user)
            await conn.commit()
    await callback.answer()
    await callback.message.answer('Хорошо, регистрацию можете пройти тут https://www.notion.so/, после перезапустите бот и выберите "Да" чтобы подключить Notion')


async def get_links(message: types.Message, state: FSMContext):
    
    url_pattern = r'(https?://[^\s]+)'
    url_pattern = r'https?://[^\s\)\]]+'
    # Extract all links from the message text
    

    # Check if the message was forwarded from a user
    if message.forward_from:
        user = message.forward_from
        response = f"Сообщение было переслано от пользователя: {user.full_name}, Type: {user} (@{user.username if user.username else 'Нет username'})."
        links: str = re.findall(url_pattern, message.text)
        await category(message, state, links)

    # Check if the message was forwarded from a channel or group
    elif message.forward_from_chat:
        chat = message.forward_from_chat
        chat_type = "канала" if chat.type == "channel" else "группы"
        response = f"Сообщение было переслано из {chat_type}: {chat.title} (@{chat.username if chat.username else 'Нет username'})"
        links: str = re.findall(url_pattern, message.text)
        await category(message, state, links)
    
    # If the message was forwarded but the original sender is hidden
    elif message.forward_sender_name:
        response = f"Сообщение было переслано от: {message.forward_sender_name}."
        links: str = re.findall(url_pattern, message.text)
        await category(message, state, links)

    else:
        links: str = re.findall(url_pattern, message.text)
        print(links, '\n')
        await category(message, state, links)
    
    # print('url', message.link_preview_options.url)
    # print('prefer_small_media', message.link_preview_options.prefer_small_media)
    # print('prefer_large_media', message.link_preview_options.prefer_large_media)
    # print('show_above_text', message.link_preview_options.show_above_text)
    # await message.reply(response)


async def category(message: types.Message, state: FSMContext, links: list):
    if links:
        await message.answer('Введите категорию: ')
        await state.update_data(links=links)
        await state.set_state(GetCategoryPriority.category)
    else:
        print('else statement')
        await message.reply("Мы не нашли ссылок в вашем сообщении")



async def get_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(GetCategoryPriority.priority)
    await message.answer('Введите приоритет: ')


async def get_priority(message: types.Message, state: FSMContext):
    await state.update_data(priority=message.text)
    
    category_priority = await state.get_data()
    category = category_priority.get('category')
    priority = category_priority.get("priority")
    links = category_priority.get('links')
    user_id = message.from_user.id
    await save_links(message, links, user_id, category, priority)
    await state.clear()

async def save_links(message: types.Message, links: list, user_id, category: str, priority: str):
    try:
        async with session() as conn:
            for link in links:
                print('Link--------------\n', link)
                async with aiohttp.ClientSession() as request:
                    async with request.get(link) as res:
                        html_text = await res.text()
                        bs = BeautifulSoup(html_text, "html.parser")
                        title = bs.find("title").get_text()
                new_link = Links(user_id=user_id, url=link, title=title, category=category, priority=priority)
                conn.add(new_link)
            await conn.commit()
        print('\n--------------------Links--------------------\n', links, '\n')
        await message.answer('Ваши ссылки успешно сохранены')
    except Exception as e:
        await message.answer("Произошла ошибка")
        print("Error", e)

    async with session() as conn:

        user = select(User).filter(User.tg_user_id == user_id)
        user = await conn.execute(user)
        user = user.scalar()
        print("User         ", user)
        db_token = user.notion_db_token
        db_id = user.notion_db_id

        if db_token and db_id:
            for url in links:
                try:
                    data = await create_page_data(url, title, category, priority)
                    page = await create_page(data, db_id, db_token)
                except Exception as e:
                    await message.answer("Произошла ошибка во время сохранения ссылок в Notion")
                    print("Error", e)