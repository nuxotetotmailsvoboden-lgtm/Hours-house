from aiogram.fsm.state import State, StatesGroup

class RegisterState(StatesGroup):
    choose_name_method = State()      # выбор способа ввода имени
    full_name_manual = State()        # ручной ввод имени
    choose_phone_method = State()     # выбор способа ввода телефона
    waiting_contact = State()         # ожидание контакта от Telegram
    phone_manual = State()            # ручной ввод телефона
    passport = State()                # загрузка паспорта
