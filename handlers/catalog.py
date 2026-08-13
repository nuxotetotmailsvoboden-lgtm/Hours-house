from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from datetime import datetime
from database import async_session
from models import Apartment, Booking, User
from keyboards.inline import apartment_choose_kb
from handlers.register import start_registration

router = Router()

@router.message(F.text == "🏠 Каталог")
async def show_catalog(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    async with async_session() as session:
        # 1. Проверяем, зарегистрирован ли пользователь
        user = await session.execute(select(User).where(User.tg_id == tg_id))
        user = user.scalar_one_or_none()
        if not user:
            await message.answer("Для просмотра каталога необходимо зарегистрироваться.")
            await start_registration(message, state)
            return

        # 2. Получаем все активные квартиры
        apartments = await session.execute(
            select(Apartment).where(Apartment.is_active == True)
        )
        apartments = apartments.scalars().all()
        if not apartments:
            await message.answer("🏚 На данный момент активных квартир нет.")
            return

        now = datetime.utcnow()
        for apt in apartments:
            # 3. Проверяем, занята ли квартира сейчас
            active_booking = await session.execute(
                select(Booking).where(
                    Booking.apartment_id == apt.id,
                    Booking.is_confirmed == True,
                    Booking.start_time <= now,
                    Booking.end_time >= now
                )
            )
            active_booking = active_booking.scalar_one_or_none()
            if active_booking:
                status = f"🔴 Занята до {active_booking.end_time.strftime('%d.%m.%Y %H:%M')}"
            else:
                status = "🟢 Свободна"

            # 4. Формируем описание
            caption = (
                f"🏠 <b>{apt.name}</b>\n"
                f"{apt.description}\n"
                f"💰 {apt.price_per_hour} ₽/час | {apt.price_per_day} ₽/сутки\n"
                f"Статус: {status}"
            )

            # 5. Отправляем фото с кнопкой «Выбрать»
            await message.answer_photo(
                apt.photo_file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=apartment_choose_kb(apt.id)
            )
