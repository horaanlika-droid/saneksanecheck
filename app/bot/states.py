"""FSM-состояния диалогов бота."""

from aiogram.fsm.state import State, StatesGroup


class ProfileEdit(StatesGroup):
    value = State()  # data: key


class CatAdd(StatesGroup):
    title = State()
    subtitle = State()


class CatEdit(StatesGroup):
    value = State()  # data: id, field


class AlbAdd(StatesGroup):
    category = State()
    title = State()
    description = State()
    location = State()
    year = State()


class AlbEdit(StatesGroup):
    value = State()  # data: id, field


class SvcAdd(StatesGroup):
    title = State()
    description = State()
    price = State()
    price_note = State()
    duration = State()


class SvcEdit(StatesGroup):
    value = State()  # data: id, field


class ExAdd(StatesGroup):
    title = State()
    place = State()
    year = State()
    description = State()


class ExEdit(StatesGroup):
    value = State()  # data: id, field


class Upload(StatesGroup):
    waiting = State()  # data: target, id, count, status_msg_id


class PhotoCaption(StatesGroup):
    value = State()  # data: photo_id, ctx


class AdminAdd(StatesGroup):
    waiting = State()
