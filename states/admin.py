from aiogram.fsm.state import State, StatesGroup

class AddApartmentState(StatesGroup):
    name = State()
    description = State()
    price_hour = State()
    price_day = State()
    photo = State()

class EditApartmentState(StatesGroup):
    choosing_field = State()          # выбор поля для редактирования
    editing_name = State()
    editing_description = State()
    editing_price_hour = State()
    editing_price_day = State()
    editing_photo = State()
    confirming_delete = State()       # подтверждение удаления
