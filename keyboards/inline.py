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

def rent_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ Почасово", callback_data="rent_hourly")],
        [InlineKeyboardButton(text="📅 Посуточно", callback_data="rent_daily")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")]
    ])

def confirm_booking_kb(apartment_id, start_str, end_str, total_price):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить бронирование", callback_data=f"confirm_booking_{apartment_id}_{start_str}_{end_str}_{total_price}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")]
    ])

def contract_agree_kb(booking_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Прочитал и согласен", callback_data=f"agree_contract_{booking_id}")]
    ])
