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

def remove_kb():
    return ReplyKeyboardRemove()
