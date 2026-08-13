from aiogram import Router, types, F
from config import ADMIN_IDS

router = Router()

@router.message(F.text == "🏠 Каталог")
async def catalog_menu(message: types.Message):
    await message.answer("📦 Каталог квартир скоро будет доступен.")

@router.message(F.text == "📋 Мои брони")
async def my_bookings(message: types.Message):
    await message.answer("📋 Ваши бронирования появятся здесь.")

@router.message(F.text == "📞 Помощь")
async def help_menu(message: types.Message):
    await message.answer(
        "📞 Если у вас возникли вопросы, свяжитесь с администратором.\n"
        "Или напишите в чат поддержки (ссылка)."
    )

@router.message(F.text == "⚙️ Админ-панель")
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет прав администратора.")
        return
    await message.answer("⚙️ Админ-панель:\n- Добавить квартиру\n- Управление бронями\n(функционал в разработке)")
