from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy import select
from database import async_session
from models import User
from keyboards.reply import main_menu_kb
from config import ADMIN_IDS

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    tg_id = message.from_user.id
    async with async_session() as session:
        # Проверяем, есть ли пользователь
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        
        if user:
            # Уже зарегистрирован
            is_admin = tg_id in ADMIN_IDS
            await message.answer(
                f"С возвращением, {user.full_name}! 👋\nВыберите действие:",
                reply_markup=main_menu_kb(is_admin)
            )
        else:
            # Начинаем регистрацию – передаём управление в register.py
            await message.answer(
                "Добро пожаловать в систему аренды квартир! 🏡\n"
                "Для начала работы пройдите регистрацию.\n"
                "Введите ваше полное ФИО:"
            )
            # Устанавливаем состояние – но состояние будем устанавливать в register.py
            # Чтобы не плодить импорты, мы вызовем следующий handler через FSM
            # Проще: здесь просто вызовем регистрацию, но лучше передать через state.
            # В register.py обработаем команду /start с состоянием.
            # Можно переделать: в start.py только проверка, а регистрацию запускаем отдельно.
            # Сделаем так: если пользователь не найден, вызываем функцию start_registration
            from handlers.register import start_registration
            await start_registration(message)
