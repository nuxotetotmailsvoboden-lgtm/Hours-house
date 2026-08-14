from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def main_menu_kb(is_admin: bool = False):
    buttons = [
        [KeyboardButton(text="🏠 Каталог")],
        [KeyboardButton(text="📋 Мои брони")],
        [KeyboardButton(text="📞 Помощь")]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="⚙️ Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def admin_panel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить квартиру")],
            [KeyboardButton(text="📋 Список квартир")],
            [KeyboardButton(text="📋 Список клиентов")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def remove_kb():
    return ReplyKeyboardRemove()

def choose_name_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Использовать имя из Telegram")],
            [KeyboardButton(text="✏️ Ввести вручную")]
        ],
        resize_keyboard=True
    )

def choose_phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер", request_contact=True)],
            [KeyboardButton(text="✏️ Ввести вручную")]
        ],
        resize_keyboard=True
    )

def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )
