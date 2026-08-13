from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def apartment_choose_kb(apartment_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выбрать", callback_data=f"choose_apt_{apartment_id}")]
    ])

def admin_apartment_actions_kb(apartment_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_apt_{apartment_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_apt_{apartment_id}")]
    ])
