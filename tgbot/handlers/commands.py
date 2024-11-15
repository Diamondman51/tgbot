from pprint import pprint
import re
from aiogram import types
from aiogram.fsm.context import FSMContext
import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy import exists, select
from tgbot.database.database import Links, User, session
from tgbot.keyboards.keyboards import *
from tgbot.notion.notion import create_page, create_page_data, get_page
from tgbot.states.states import GetLink, GetCategoryPriority, GetNotionDB, GetSetData
from asgiref.sync import async_to_sync

session = session

async def start_command_handler(message: types.Message, state: FSMContext):
    from_user = message.from_user
    async with session() as conn:    
        user  = select(exists().where(User.tg_user_id == from_user.id))
        user = await conn.execute(user)
        user = user.scalar()
        print(user)
        if not user:
            greeting_text = f"Здравствуйте, {from_user.full_name}! У вас есть Notion Database?"
            user = User(tg_user_id=from_user.id)
            session().add(user)
            await conn.commit()
            keyboard = await ask_notion_keyboard()
            await message.answer(greeting_text, reply_markup=keyboard)
        elif user:
            user = select(User).where(User.tg_user_id == from_user.id)
            res = await conn.execute(user)
            user = res.scalar()
            db_token = user.notion_db_token
            db_id = user.notion_db_id
            if db_token and db_id:
                greeting_text = f"С возвращением {from_user.full_name}, меняем Notion базу?"
                await message.answer(greeting_text, reply_markup= await change_notion_keyboard())
            else:
                greeting_text = f"С возвращением {from_user.full_name}, добавим Notion базу?"
                await message.answer(greeting_text, reply_markup= await ask_notion())


async def leave(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.answer("Отлично, можете продолжать", reply_markup=await after_start_keyboard())
    # await callback.message.answer("",)
    # callback.message.answer("Все готово, можете продолжать")


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
    await message.answer('Спасибо, все готово', reply_markup= await after_start_keyboard())
    db = await state.get_data()
    async with session() as conn:
        user_id = message.from_user.id
        user = select(exists().where(User.tg_user_id == user_id))
        user = await conn.execute(user)
        user = user.scalar()
        db_token = db.get('db_token')
        db_id = db.get("db_id")
        if not user:
            new_user = User(tg_user_id=message.from_user.id, notion_db_token=db_token, notion_db_id=db_id)
            conn.add(new_user)
            await conn.commit()
        elif user:
            user = select(User).where(User.tg_user_id == message.from_user.id)
            res = await conn.execute(user)
            user = res.scalar()
            user.notion_db_token = db_token
            user.notion_db_id = db_id
            await conn.commit()

    await state.clear()
    # pprint(db)


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
    await callback.message.answer('Хорошо, регистрацию можете пройти тут https://www.notion.so/, после перезапустите бот и выберите "Да" чтобы подключить Notion', reply_markup= await after_start_keyboard())


async def get_links(message: types.Message, state: FSMContext):
    
    # url_pattern = r'(https?://[^\s]+)'
    url_pattern = r'https?://[^\s\)\]]+'
    # Extract all links from the message text
    
    print(message.text)

    # Check if the message was forwarded from a user
    if message.forward_from:
        user = message.forward_from
        response = f"Сообщение было переслано от пользователя: {user.full_name}, Type: {user} (@{user.username if user.username else 'Нет username'})."
        print(response)

        message_text = message.text if message.text else message.caption
        
        links: str = re.findall(url_pattern, message_text)
        
        await category(message, state, links)

    # Check if the message was forwarded from a channel or group
    elif message.forward_from_chat:
        chat = message.forward_from_chat
        chat_type = "канала" if chat.type == "channel" else "группы"
        response = f"Сообщение было переслано из {chat_type}: {chat.title} (@{chat.username if chat.username else 'Нет username'})"
        print(response)
        message_text = message.text if message.text else message.caption
        links: str = re.findall(url_pattern, message_text)
        await category(message, state, links)
    
    # If the message was forwarded but the original sender is hidden
    elif message.forward_sender_name:
        response = f"Сообщение было переслано от: {message.forward_sender_name}."
        print(response)
        message_text = message.text if message.text else message.caption
        links: str = re.findall(url_pattern, message_text)
        await category(message, state, links)


    # elif message.forward_origin:
    #     print(f"message origin")
        
    # elif message.forward_from_message_id:
    #     print(f"message id")


    else:
        message_text = message.text if message.text else message.caption
        links: str = re.findall(url_pattern, message_text)
        print('Get links links', links, '\n')
        await category(message, state, links)
    print(message.text)
    
    # print('url', message.link_preview_options.url)
    # print('prefer_small_media', message.link_preview_options.prefer_small_media)
    # print('prefer_large_media', message.link_preview_options.prefer_large_media)
    # print('show_above_text', message.link_preview_options.show_above_text)
    # await message.reply(response)


async def category(message: types.Message, state: FSMContext, links: list):
    if links:
        user = select(User).filter(User.tg_user_id == message.from_user.id)
        async with session() as conn:
            user = await conn.execute(user)
            user = user.scalar()
            db_token = user.notion_db_token
            db_id = user.notion_db_id

            if db_token and db_id:
                data = await get_page(db_id, db_token)
                set_data = {field['properties']["Category"]['rich_text'][0]['plain_text'] for field in data}
                keyboard = await make_categories_priorities(set_data)

            else:
                links = select(Links).filter(Links.user_id == message.from_user.id)
                links = await conn.execute(links)
                links = links.scalars().all()
                set_data = {link.category for link in links}
                if set_data:
                    keyboard = await make_categories_priorities(set_data)
   
        await message.answer('Выберите или введите категорию: ', reply_markup= keyboard)
        await state.update_data(links=links)
        await state.set_state(GetCategoryPriority.category)
    else:
        print('else statement')
        await message.reply("Мы не нашли ссылок в вашем сообщении")



async def get_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(GetCategoryPriority.priority)
    user = select(User).filter(User.tg_user_id == message.from_user.id)
    async with session() as conn:
        user = await conn.execute(user)
        user = user.scalar()
        db_token = user.notion_db_token
        db_id = user.notion_db_id

        if db_token and db_id:
            data = await get_page(db_id, db_token)
            set_data = {field['properties']["Priority"]["select"]["name"] for field in data}
            pprint(data)
            if set_data:
                keyboard = await make_categories_priorities(set_data)
        else:
            links = select(Links).filter(Links.user_id == message.from_user.id)
            links = await conn.execute(links)
            links = links.scalars().all()
            set_data = {link.priority for link in links}
            if set_data:    
                keyboard = await make_categories_priorities(set_data)

    await message.answer('Выберите или введите приоритет: ', reply_markup=keyboard)


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
        await message.answer('Ваши ссылки успешно сохранены в базу', reply_markup=await after_start_keyboard())
    except Exception as e:
        await message.answer("Произошла ошибка, повторите попытку", reply_markup= await after_start_keyboard())
        print("Error", e)

    async with session() as conn:

        user = select(User).filter(User.tg_user_id == user_id)
        user = await conn.execute(user)
        user = user.scalar()
        print("User         ", user)
        db_token = user.notion_db_token
        db_id = user.notion_db_id

        if db_token and db_id:
            co = 1
            ls = []
            for url in links:
                try:
                    data = await create_page_data(url, title, category, priority)
                    page, response = await create_page(data, db_id, db_token)
                    ls.append(response.status == 200)
                    print('Page', page)
                    print(co, 'сохранен')
                    co += 1
                except Exception as e:
                    await message.answer("Произошла ошибка во время сохранения ссылок в Notion, повторите попытку", reply_markup= await after_start_keyboard())
                    print("Error", e)
            if all(ls):
                await message.answer("Ваши ссылки успешно сохранены в Notion Database", reply_markup= await after_start_keyboard())


async def by_priority(message: types.Message, state: FSMContext):
    user = select(User).filter(User.tg_user_id == message.from_user.id)
    async with session() as conn:
        user = await conn.execute(user)
        user = user.scalar()
        db_token = user.notion_db_token
        db_id = user.notion_db_id

        if db_token and db_id:
            data = await get_page(db_id, db_token)
            set_data = {field['properties']["Priority"]["select"]["name"] for field in data}
            pprint(data)
            if set_data:
                keyboard = await make_categories_priorities(set_data)
                page = [[field['properties']["URL"]["title"][0]["text"]["content"], field['properties']["Title"]["rich_text"][0]["text"]["content"], field['properties']["Priority"]["select"]["name"], field['properties']["Category"]['rich_text'][0]['plain_text']] for field in data]
                await state.update_data(set_data=set_data)
                await state.set_state(GetSetData.priority)
                await state.update_data(page=page)
                await message.answer("Выберите приоритет: ", reply_markup=keyboard)
                # pprint(data)
            else:
                await message.answer('Извините, у вас пока нет приоритетов(', reply_markup= await after_start_keyboard())


        else:
            links = select(Links).filter(Links.user_id == message.from_user.id)
            links = await conn.execute(links)
            links = links.scalars().all()
            set_data = {link.priority for link in links}
            if set_data:    
                keyboard = await make_categories_priorities(set_data)
                await message.answer("Выберите приоритет: ", reply_markup=keyboard)
                print('By priority links: \t', *{link.priority for link in links})
            else:
                await message.answer('Извините, у вас пока нет приоритетов(', reply_markup= await after_start_keyboard())


async def get_by_priority(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pages = data.get("page")
    pages = filter(lambda page: page[2] == message.text, pages)
    print(pages)
    async with session() as conn:
        if pages:
            for page in pages:
                await message.answer(f"URL: {page[0]}\nTitle: {page[1]}\nPriority: {page[2]}\nCategory: {page[3]}", reply_markup= await after_start_keyboard())
        elif not pages:    
            links = select(Links).filter(Links.priority == message.text)
            links = await conn.execute(links)
            links = links.scalars().all()
            if links:
                for link in links:
                    await message.answer(f"URL: {link.url}\nTitle: {link.title}\nCategory: {link.category}\nPriority: {link.priority}", reply_markup= await after_start_keyboard())
            else:
                await message.answer('Извините, у вас нет ссылок по этому приоритету')
    await message.answer('Success', reply_markup= await after_start_keyboard())

    await state.clear()


async def by_category(message: types.Message, state: FSMContext):
    user = select(User).filter(User.tg_user_id == message.from_user.id)
    async with session() as conn:
        user = await conn.execute(user)
        user = user.scalar()
        db_token = user.notion_db_token
        db_id = user.notion_db_id

        if db_token and db_id:
            data = await get_page(db_id, db_token)
            set_data = {field['properties']["Category"]['rich_text'][0]['plain_text'] for field in data}
            if set_data:
                keyboard = await make_categories_priorities(set_data)
                page = [[field['properties']["URL"]["title"][0]["text"]["content"], field['properties']["Title"]["rich_text"][0]["text"]["content"], field['properties']["Priority"]["select"]["name"], field['properties']["Category"]['rich_text'][0]['plain_text']] for field in data]
                await state.update_data(set_data=set_data)
                await state.update_data(page=page)
                await state.set_state(GetSetData.category)
                await message.answer("Выберите категорию: ", reply_markup=keyboard)
                # pprint(data)
            else:
                await message.answer('Извините, у вас пока нет категорий(', reply_markup= await after_start_keyboard())

        else:
            links = select(Links).filter(Links.user_id == message.from_user.id)
            links = await conn.execute(links)
            links = links.scalars().all()
            set_data = {link.category for link in links}
            if set_data:
                keyboard = await make_categories_priorities(set_data)
                await message.answer("Выберите категорию: ", reply_markup=keyboard)
                print('By priority links: \t', *{link.priority for link in links})
            else:
                await message.answer('Извините, у вас пока нет категорий(', reply_markup= await after_start_keyboard())


async def get_by_category(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pages = data.get("page")
    # async with session() as conn:
    #     links = await conn.execute(links)
    #     links = links.scalars().all()
    #     for link in links:
    #         await message.answer(f"URL: {link.url}\nTitle: {link.title}\nCategory: {link.category}\nPriority: {link.priority}",)
    # await message.answer('Success', reply_markup= await after_start_keyboard())

    # await state.clear()
    pages = filter(lambda page: page[3] == message.text, pages)

    async with session() as conn:
        if pages:
            for page in pages:
                await message.answer(f"URL: {page[0]}\nTitle: {page[1]}\nPriority: {page[2]}\nCategory: {page[3]}", reply_markup= await after_start_keyboard())
        elif not pages:    
            links = select(Links).filter(Links.category == message.text)
            links = await conn.execute(links)
            links = links.scalars().all()
            if links:
                for link in links:
                    await message.answer(f"URL: {link.url}\nTitle: {link.title}\nCategory: {link.category}\nPriority: {link.priority}", reply_markup= await after_start_keyboard())
            else:
                await message.answer('Извините, у вас нет ссылок по этому приоритету')
    await message.answer('Success', reply_markup= await after_start_keyboard())

    await state.clear()
