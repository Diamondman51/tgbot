from aiogram.fsm.state import State, StatesGroup

class GetLink(StatesGroup):
    url = State()
    title = State()
    category = State()
    priority = State()


class GetCategoryPriority(StatesGroup):
    category = State()
    priority = State()


class GetSetData(StatesGroup):
    priority = State()
    category = State()

class GetNotionDB(StatesGroup):
    db_token = State()
    db_id = State()
