from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime
from sqlalchemy import select
from database import async_session
from models import Apartment, Booking, User
from states.booking import BookingState
from keyboards.inline import rent_type_kb, confirm_booking_kb, contract_agree_kb
from keyboards.reply import main_menu_kb
from config import ADMIN_IDS
from utils import parse_datetime
import re

router = Router()

async def is_apartment_free(apartment_id: int, start: datetime, end: datetime, session) -> bool:
    bookings = await session.execute(
        select(Booking).where(
            Booking.apartment_id == apartment_id,
            Booking.is_confirmed == True,
            Booking.start_time < end,
            Booking.end_time > start
        )
    )
    return bookings.first() is None

def calculate_price(apartment, start: datetime, end: datetime, rent_type: str) -> float:
    delta = end - start
    if rent_type == 'hourly':
        hours = delta.total_seconds() / 3600
        hours_rounded = int(hours) + (1 if hours % 1 > 0 else 0)
        return apartment.price_per_hour * hours_rounded
    else:
        days = delta.total_seconds() / 86400
        days_rounded = int(days) + (1 if days % 1 > 0 else 0)
        return apartment.price_per_day * days_rounded

@router.callback_query(F.data.startswith("choose_apt_"))
async def choose_apartment(callback: types.CallbackQuery, state: FSMContext):
    apartment_id = int(callback.data.split("_")[2])
    await state.update_data(apartment_id=apartment_id)
    await state.set_state(BookingState.choosing_rent_type)
    await callback.message.delete()
    await callback.message.answer("Выберите тип аренды:", reply_markup=rent_type_kb())
    await callback.answer()

@router.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Бронирование отменено.", reply_markup=main_menu_kb())
    await callback.answer()

@router.callback_query(F.data.in_(["rent_hourly", "rent_daily"]))
async def process_rent_type(callback: types.CallbackQuery, state: FSMContext):
    rent_type = callback.data.split("_")[1]
    await state.update_data(rent_type=rent_type)
    await state.set_state(BookingState.entering_start_datetime)
    await callback.message.delete()
    await callback.message.answer(
        "Введите дату и время **начала** аренды в формате:\n"
        "`ДД.ММ.ГГГГ ЧЧ:ММ`\nНапример: `25.05.2026 15:00`\nВремя по UTC.",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(BookingState.entering_start_datetime)
async def process_start_datetime(message: types.Message, state: FSMContext):
    dt = parse_datetime(message.text)
    if not dt:
        await message.answer("Неверный формат. Введите в формате `ДД.ММ.ГГГГ ЧЧ:ММ`.")
        return
    if dt < datetime.now():
        await message.answer("Дата начала должна быть в будущем.")
        return
    await state.update_data(start_dt=dt)
    await state.set_state(BookingState.entering_end_datetime)
    await message.answer("Теперь введите дату и время **окончания** аренды.")

@router.message(BookingState.entering_end_datetime)
async def process_end_datetime(message: types.Message, state: FSMContext):
    dt_end = parse_datetime(message.text)
    if not dt_end:
        await message.answer("Неверный формат.")
        return
    data = await state.get_data()
    dt_start = data.get('start_dt')
    if not dt_start:
        await message.answer("Ошибка, начните заново.")
        await state.clear()
        return
    if dt_end <= dt_start:
        await message.answer("Окончание должно быть позже начала.")
        return
    if (dt_end - dt_start).days > 30:
        await message.answer("Максимальный срок — 30 суток.")
        return
    await state.update_data(end_dt=dt_end)
    apartment_id = data.get('apartment_id')
    async with async_session() as session:
        apt = await session.get(Apartment, apartment_id)
        if not apt or not apt.is_active:
            await message.answer("Квартира недоступна.")
            await state.clear()
            return
        if not await is_apartment_free(apartment_id, dt_start, dt_end, session):
            await message.answer("Квартира занята на выбранный период.")
            await state.clear()
            return
        rent_type = data.get('rent_type')
        total = calculate_price(apt, dt_start, dt_end, rent_type)
        await state.update_data(total_price=total)
        rent_type_text = "Почасово" if rent_type == 'hourly' else "Посуточно"
        start_str = dt_start.strftime('%d.%m.%Y %H:%M')
        end_str = dt_end.strftime('%d.%m.%Y %H:%M')
        caption = (
            f"🛏 <b>{apt.name}</b>\n"
            f"Тип: {rent_type_text}\n"
            f"Заезд: {start_str}\n"
            f"Выезд: {end_str}\n"
            f"Сумма: <b>{total:.2f} ₽</b>\n\nПроверьте данные и нажмите «Подтвердить»."
        )
        await message.answer(caption, parse_mode="HTML", reply_markup=confirm_booking_kb(apartment_id, start_str, end_str, total))

@router.callback_query(F.data.startswith("confirm_booking_"))
async def confirm_booking(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    apartment_id = data.get('apartment_id')
    start_dt = data.get('start_dt')
    end_dt = data.get('end_dt')
    total = data.get('total_price')
    if not all([apartment_id, start_dt, end_dt, total]):
        await callback.answer("Ошибка, начните заново.")
        await state.clear()
        return
    user = callback.from_user
    async with async_session() as session:
        user_db = await session.execute(select(User).where(User.tg_id == user.id))
        user_db = user_db.scalar_one_or_none()
        if not user_db:
            await callback.answer("Вы не зарегистрированы.")
            return
        apt = await session.get(Apartment, apartment_id)
        if not apt:
            await callback.answer("Квартира не найдена.")
            return
        # Создаём бронь со статусом is_confirmed=False, contract_signed=False
        new_booking = Booking(
            user_id=user_db.id,
            apartment_id=apartment_id,
            start_time=start_dt,
            end_time=end_dt,
            total_price=total,
            is_confirmed=False,
            contract_signed=False
        )
        session.add(new_booking)
        await session.commit()
        await session.refresh(new_booking)
        booking_id = new_booking.id
        
        # Отправляем договор
        contract_text = (
            "📄 **ДОГОВОР АРЕНДЫ**\n\n"
            f"Арендодатель: ООО «РентБот»\n"
            f"Арендатор: {user_db.full_name}\n"
            f"Квартира: {apt.name}\n"
            f"Период: {start_dt.strftime('%d.%m.%Y %H:%M')} – {end_dt.strftime('%d.%m.%Y %H:%M')}\n"
            f"Стоимость: {total:.2f} ₽\n\n"
            "Условия:\n- Оплата на месте.\n- За нарушение правил штраф.\n- При порче имущества – компенсация.\n\n"
            "Пожалуйста, ознакомьтесь с договором. После ознакомления нажмите кнопку ниже."
        )
        await callback.message.delete()
        await callback.message.answer(contract_text, parse_mode="Markdown")
        
        # Отдельное сообщение с двумя кнопками
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        agree_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Договор прочитал, согласен", callback_data=f"agree_{booking_id}")],
            [InlineKeyboardButton(text="❌ Договор прочитал, не согласен", callback_data=f"disagree_{booking_id}")]
        ])
        await callback.message.answer("Вы ознакомились с договором? Примите решение:", reply_markup=agree_kb)
        await state.clear()
        await callback.answer()

@router.callback_query(F.data.startswith("agree_"))
async def agree_contract(callback: types.CallbackQuery, bot):
    booking_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            await callback.answer("Бронь не найдена.")
            return
        if booking.contract_signed:
            await callback.answer("Договор уже подписан.")
            return
        # Подтверждаем
        booking.is_confirmed = True
        booking.contract_signed = True
        await session.commit()
        await callback.message.delete()
        await callback.message.answer(
            "✅ Спасибо! С вами свяжется администратор для оплаты и выдачи ключей.",
            reply_markup=main_menu_kb()
        )
        # Уведомление админам с полными данными для юридической защиты
        user = callback.from_user
        # Получаем данные пользователя из БД (номер телефона)
        user_db = await session.get(User, booking.user_id)
        phone = user_db.phone if user_db else "не указан"
        apt = await session.get(Apartment, booking.apartment_id)
        admin_text = (
            f"🔔 <b>НОВАЯ БРОНЬ (ПОДТВЕРЖДЕНА)</b>\n\n"
            f"<b>Клиент:</b> {user.full_name}\n"
            f"<b>Телефон:</b> {phone}\n"
            f"<b>Telegram ID:</b> {user.id}\n"
            f"<b>Квартира:</b> {apt.name}\n"
            f"<b>Адрес:</b> {apt.description}\n"
            f"<b>Заезд:</b> {booking.start_time.strftime('%d.%m.%Y %H:%M')}\n"
            f"<b>Выезд:</b> {booking.end_time.strftime('%d.%m.%Y %H:%M')}\n"
            f"<b>Сумма:</b> {booking.total_price:.2f} ₽\n"
            f"<b>ID брони:</b> {booking.id}\n\n"
            f"✅ <b>Клиент договором ознакомился, согласен.</b>"
        )
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, admin_text, parse_mode="HTML")
            except Exception as e:
                print(f"Ошибка отправки админу {admin_id}: {e}")
        await callback.answer("Бронирование подтверждено!")

@router.callback_query(F.data.startswith("disagree_"))
async def disagree_contract(callback: types.CallbackQuery, bot):
    booking_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            await callback.answer("Бронь не найдена.")
            return
        # Удаляем бронь
        await session.delete(booking)
        await session.commit()
        await callback.message.delete()
        await callback.message.answer(
            "😔 К сожалению, мы не сможем предоставить вам жильё, так как вы не согласились с условиями договора.\n"
            "Если у вас есть вопросы, свяжитесь с администратором.",
            reply_markup=main_menu_kb()
        )
        # Опциональное уведомление админам
        user = callback.from_user
        admin_text = f"❌ Клиент {user.full_name} отказался от договора (бронь ID {booking_id} отменена)."
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, admin_text)
            except:
                pass
        await callback.answer("Бронирование отменено.")
