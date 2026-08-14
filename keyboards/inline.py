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


def edit_apartment_menu_kb(apartment_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏷️ Название", callback_data=f"edit_field_{apartment_id}_name")],
        [InlineKeyboardButton(text="📝 Описание", callback_data=f"edit_field_{apartment_id}_description")],
        [InlineKeyboardButton(text="💰 Цена за час", callback_data=f"edit_field_{apartment_id}_price_hour")],
        [InlineKeyboardButton(text="💰 Цена за сутки", callback_data=f"edit_field_{apartment_id}_price_day")],
        [InlineKeyboardButton(text="🖼️ Фото", callback_data=f"edit_field_{apartment_id}_photo")],
        [InlineKeyboardButton(text="🔄 Активность", callback_data=f"edit_field_{apartment_id}_active")],
        [InlineKeyboardButton(text="✅ Готово", callback_data=f"edit_done_{apartment_id}")]
    ])

def confirm_delete_kb(apartment_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{apartment_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_delete_{apartment_id}")]
    ])

def contract_agree_kb(booking_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Прочитал и согласен", callback_data=f"agree_contract_{booking_id}")]
    ])
