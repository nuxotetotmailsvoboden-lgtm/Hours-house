from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from sqlalchemy import select, and_
import re
from database import async_session
from models import Apartment, Booking, User
from states.booking import BookingState
from keyboards.inline import rent_type_kb, confirm_booking_kb, contract_agree_kb
from keyboards.reply import main_menu_kb
from config import ADMIN_IDS, BOT_TOKEN
from aiogram import Bot

router = Router()

# --- Вспомогательные функции ---

async def is_apartment_free(apartment_id: int, start: datetime, end: datetime, session) -> bool:
    """Проверяет, свободна ли квартира на указанный период (нет пересечений с подтверждёнными бронями)."""
    bookings = await session.execute(
        select(Booking).where(
            Booking.apartment_id == apartment_id,
            Booking.is_confirmed == True,
            Booking.start_time < end,
            Booking.end_time > start
        )
    )
    return bookings.first() is None  # если нет ни одной записи — свободна

def parse_datetime(text: str) -> datetime | None:
    """Парсит строку вида '25.05.2026 15:30'"""
    pattern = r'^(\d{2})\.(\d{2})\.(\d{4}) (\d{2}):(\d{2})$'
    match = re.match(pattern, text.strip())
    if not match:
        return None
    day, month, year, hour, minute = map(int, match.groups())
    try:
        dt = datetime(year, month, day, hour, minute)
        return dt
    except ValueError:
        return None

def calculate_price(apartment, start: datetime, end: datetime, rent_type: str) -> float:
    """Расчёт стоимости в зависимости от типа аренды."""
    delta = end - start
    if rent_type == 'hourly':
        hours = delta.total_seconds() / 3600
        # Округляем вверх до целого часа
        hours_rounded = int(hours) + (1 if hours % 1 > 0 else 0)
        return apartment.price_per_hour * hours_rounded
    else:  # daily
        days = delta.total_seconds() / 86400
        days_rounded = int(days) + (1 if days % 1 > 0 else 0)
        return apartment.price_per_day * days_rounded

# --- Обработчики ---

@router.callback_query(F.data.startswith("choose_apt_"))
async def choose_apartment(callback: types.CallbackQuery, state: FSMContext):
    """После выбора квартиры в каталоге — предложить тип аренды."""
    apartment_id = int(callback.data.split("_")[2])
    await state.update_data(apartment_id=apartment_id)
    await state.set_state(BookingState.choosing_rent_type)
    await callback.message.delete()  # убираем сообщение с квартирой
    await callback.message.answer(
        "Выберите тип аренды:",
        reply_markup=rent_type_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: types.CallbackQuery, state: FSMContext):
    """Отмена бронирования."""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Бронирование отменено.", reply_markup=main_menu_kb())
    await callback.answer()

@router.callback_query(F.data.in_(["rent_hourly", "rent_daily"]))
async def process_rent_type(callback: types.CallbackQuery, state: FSMContext):
    """Выбор типа аренды -> запрос даты начала."""
    rent_type = callback.data.split("_")[1]  # hourly или daily
    await state.update_data(rent_type=rent_type)
    await state.set_state(BookingState.entering_start_datetime)
    await callback.message.delete()
    await callback.message.answer(
        "Введите дату и время **начала** аренды в формате:\n"
        "`ДД.ММ.ГГГГ ЧЧ:ММ`\n"
        "Например: `25.05.2026 15:00`\n"
        "Время указывайте по Московскому времени (UTC+3).",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(BookingState.entering_start_datetime)
async def process_start_datetime(message: types.Message, state: FSMContext):
    dt = parse_datetime(message.text)
    if not dt:
        await message.answer("Неверный формат. Введите в формате `ДД.ММ.ГГГГ ЧЧ:ММ`, например `25.05.2026 15:00`.")
        return
    # Проверяем, что дата не в прошлом
    if dt < datetime.now():
        await message.answer("Дата начала должна быть в будущем. Введите корректную дату.")
        return
    await state.update_data(start_dt=dt)
    await state.set_state(BookingState.entering_end_datetime)
    await message.answer("Теперь введите дату и время **окончания** аренды в том же формате.")

@router.message(BookingState.entering_end_datetime)
async def process_end_datetime(message: types.Message, state: FSMContext):
    dt_end = parse_datetime(message.text)
    if not dt_end:
        await message.answer("Неверный формат. Введите в формате `ДД.ММ.ГГГГ ЧЧ:ММ`.")
        return
    data = await state.get_data()
    dt_start = data.get('start_dt')
    if not dt_start:
        await message.answer("Что-то пошло не так, начните заново.")
        await state.clear()
        return
    if dt_end <= dt_start:
        await message.answer("Дата окончания должна быть позже даты начала.")
        return
    # Проверяем, что разница не слишком большая (например, не более 30 суток) — опционально
    if (dt_end - dt_start).days > 30:
        await message.answer("Максимальный срок аренды — 30 суток. Введите меньший период.")
        return
    # Сохраняем end_dt
    await state.update_data(end_dt=dt_end)
    # Получаем квартиру и проверяем доступность
    apartment_id = data.get('apartment_id')
    async with async_session() as session:
        apt = await session.get(Apartment, apartment_id)
        if not apt or not apt.is_active:
            await message.answer("Квартира больше не доступна.")
            await state.clear()
            return
        # Проверка свободности
        if not await is_apartment_free(apartment_id, dt_start, dt_end, session):
            # Ищем ближайшие свободные окна? Пока просто скажем занято.
            await message.answer("Квартира занята на выбранный период. Пожалуйста, выберите другие даты или другую квартиру.")
            # Можно предложить начать заново или вернуться в каталог
            await state.clear()
            return
        # Рассчёт стоимости
        rent_type = data.get('rent_type')
        total = calculate_price(apt, dt_start, dt_end, rent_type)
        await state.update_data(total_price=total)
        # Формируем итоговое сообщение
        rent_type_text = "Почасово" if rent_type == 'hourly' else "Посуточно"
        start_str = dt_start.strftime('%d.%m.%Y %H:%M')
        end_str = dt_end.strftime('%d.%m.%Y %H:%M')
        caption = (
            f"🛏 <b>{apt.name}</b>\n"
            f"Тип аренды: {rent_type_text}\n"
            f"Заезд: {start_str}\n"
            f"Выезд: {end_str}\n"
            f"Сумма: <b>{total:.2f} ₽</b>\n\n"
            "Проверьте данные и нажмите «Подтвердить бронирование»."
        )
        # Сохраняем данные для дальнейшего использования
        await state.update_data(apt_name=apt.name, apt_price_hour=apt.price_per_hour, apt_price_day=apt.price_per_day)
        # Отправляем итоги с кнопкой подтверждения
        await message.answer(caption, parse_mode="HTML", reply_markup=confirm_booking_kb(apartment_id, start_str, end_str, total))

@router.callback_query(F.data.startswith("confirm_booking_"))
async def confirm_booking(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатия «Подтвердить бронирование» — теперь показываем договор."""
    # Из callback можно достать параметры, но лучше взять из состояния
    data = await state.get_data()
    apartment_id = data.get('apartment_id')
    start_dt = data.get('start_dt')
    end_dt = data.get('end_dt')
    total = data.get('total_price')
    rent_type = data.get('rent_type')
    if not all([apartment_id, start_dt, end_dt, total]):
        await callback.answer("Ошибка, начните заново.")
        await state.clear()
        return
    # Генерация договора (шаблон)
    user = callback.from_user
    async with async_session() as session:
        # Получаем данные пользователя
        user_db = await session.execute(select(User).where(User.tg_id == user.id))
        user_db = user_db.scalar_one_or_none()
        if not user_db:
            await callback.answer("Вы не зарегистрированы. Пройдите регистрацию.")
            return
        apt = await session.get(Apartment, apartment_id)
        if not apt:
            await callback.answer("Квартира не найдена.")
            return
        # Создаём запись брони (пока без подтверждения договора, но с is_confirmed=False)
        # Мы сохраним бронь после подписания договора, поэтому пока не создаём.
        # Но можно создать с is_confirmed=False и обновить позже.
        # Поступим так: создаём бронь со статусом is_confirmed=False, contract_signed=False.
        # После согласия с договором обновим на True.
        # Для этого сначала создадим запись, чтобы иметь booking_id для callback.
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
            "Условия:\n"
            "- Оплата производится на месте.\n"
            "- За нарушение правил предусмотрен штраф.\n"
            "- При порче имущества – полная компенсация.\n\n"
            "Нажимая «Прочитал и согласен», вы принимаете условия договора."
        )
        await callback.message.delete()
        await callback.message.answer(contract_text, parse_mode="Markdown", reply_markup=contract_agree_kb(booking_id))
        await state.clear()  # очищаем состояние после создания брони, оставляем только booking_id в callback
        await callback.answer()

@router.callback_query(F.data.startswith("agree_contract_"))
async def agree_contract(callback: types.CallbackQuery, bot: Bot):
    """Подписание договора, подтверждение брони."""
    booking_id = int(callback.data.split("_")[2])
    async with async_session() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            await callback.answer("Бронь не найдена.")
            return
        if booking.contract_signed:
            await callback.answer("Договор уже подписан.")
            return
        # Обновляем статусы
        booking.is_confirmed = True
        booking.contract_signed = True
        await session.commit()
        # Уведомление пользователю
        await callback.message.delete()
        await callback.message.answer(
            "✅ Бронирование подтверждено! Договор подписан.\n"
            "Скоро с вами свяжется администратор для уточнения деталей.",
            reply_markup=main_menu_kb()
        )
        # Уведомление админам
        user = callback.from_user
        apt = await session.get(Apartment, booking.apartment_id)
        admin_text = (
            f"🔔 <b>НОВАЯ БРОНЬ</b>\n"
            f"Пользователь: {user.full_name} (@{user.username or 'без username'})\n"
            f"Квартира: {apt.name}\n"
            f"Заезд: {booking.start_time.strftime('%d.%m.%Y %H:%M')}\n"
            f"Выезд: {booking.end_time.strftime('%d.%m.%Y %H:%M')}\n"
            f"Сумма: {booking.total_price:.2f} ₽\n"
            f"Номер брони: {booking.id}"
        )
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, admin_text, parse_mode="HTML")
            except Exception as e:
                print(f"Не удалось отправить админу {admin_id}: {e}")
        await callback.answer("Бронирование завершено!")
