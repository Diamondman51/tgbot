# import datetime
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram import F

from tgbot.handlers.commands import *


def setup() -> Router:
    router = Router()

    router.message.register(start_command_handler, CommandStart())
    router.callback_query.register(get_notion_db, F.data == 'yes')
    router.callback_query.register(no_notion_token, F.data == 'no')
    router.callback_query.register(leave, F.data == 'save')
    router.callback_query.register(get_notion_db, F.data == 'change')
    router.message.register(get_notion_db_token, GetNotionDB.db_token)
    router.message.register(get_notion_db_id, GetNotionDB.db_id)
    router.message.register(get_category, GetCategoryPriority.category)
    router.message.register(get_priority, GetCategoryPriority.priority)
    router.message.register(by_priority, F.text == 'По приоритету')
    router.message.register(by_category, F.text == 'По категорию')
    router.message.register(get_by_priority, GetSetData.priority)
    router.message.register(get_by_category, GetSetData.category)
    router.message.register(get_links, F.text)
    router.message.register(get_links, F)


    return router

    router.message.register(start_command_handler, )
# dt = datetime.datetime.now().astimezone(datetime.timezone.utc).isoformat()
# print("{}".format(dt))