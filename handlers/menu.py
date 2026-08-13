from aiogram import Router, types, F
from config import ADMIN_IDS

router = Router()

@router.message(F.text == "📋 Мои брони")
async def my_bookings(message: types.Message):
    await message.answer("📋 Ваши бронирования появятся здесь (функция в разработке).")

@router.message(F.text == "📞 Помощь")
async def help_menu(message: types.Message):
    await message.answer(
        "📞 Если у вас возникли вопросы, свяжитесь с администратором.\n"
        "Или напишите в чат поддержки (ссылка)."
    )
