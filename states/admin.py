from aiogram.fsm.state import State, StatesGroup

class AddApartmentState(StatesGroup):
    name = State()
    description = State()
    price_hour = State()
    price_day = State()
    photo = State()
