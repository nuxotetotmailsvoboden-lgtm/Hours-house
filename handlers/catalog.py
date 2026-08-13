from aiogram import Router, types, F
from sqlalchemy import select
from datetime import datetime
from database import async_session
from models import Apartment, Booking
from keyboards.inline import apartment_choose_kb

router = Router()

@router.message(F.text == "🏠 Каталог")
async def show_catalog(message: types.Message):
    async with async_session() as session:
        apartments = await session.execute(select(Apartment).where(Apartment.is_active == True))
        apartments = apartments.scalars().all()
        if not apartments:
            await message.answer("🏚 На данный момент активных квартир нет.")
            return
        for apt in apartments:
            # Проверяем занятость
            now = datetime.utcnow()
            # Находим брони, которые пересекаются с текущим временем
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
            caption = (
                f"🏠 <b>{apt.name}</b>\n"
                f"{apt.description}\n"
                f"💰 {apt.price_per_hour} ₽/час | {apt.price_per_day} ₽/сутки\n"
                f"Статус: {status}"
            )
            await message.answer_photo(
                apt.photo_file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=apartment_choose_kb(apt.id)
            )
