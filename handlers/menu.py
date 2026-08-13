from aiogram import Router, types, F
from config import ADMIN_IDS

router = Router()

@router.message(F.text == "🏠 Каталог")
async def catalog_menu(message: types.Message):
    # Обработка передана в catalog.py, но здесь мы ничего не делаем,
    # чтобы избежать конфликтов. В catalog.py есть обработчик с таким же фильтром,
    # поэтому этот обработчик можно удалить или оставить как заглушку.
    # Чтобы не дублировать, убираем обработку каталога из menu.py.
    pass

@router.message(F.text == "📋 Мои брони")
async def my_bookings(message: types.Message):
    await message.answer("📋 Ваши бронирования появятся здесь (функция в разработке).")

@router.message(F.text == "📞 Помощь")
async def help_menu(message: types.Message):
    await message.answer(
        "📞 Если у вас возникли вопросы, свяжитесь с администратором.\n"
        "Или напишите в чат поддержки (ссылка)."
    )

@router.message(F.text == "⚙️ Админ-панель")
async def admin_panel_menu(message: types.Message):
    # Обрабатывается в admin.py, поэтому здесь ничего не делаем
    pass
