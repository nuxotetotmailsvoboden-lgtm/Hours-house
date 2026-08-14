from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from database import async_session
from models import Apartment, User, Booking
from states.admin import AddApartmentState
from keyboards.reply import main_menu_kb, cancel_kb, admin_panel_kb
from keyboards.inline import admin_apartment_actions_kb
from config import ADMIN_IDS
import re

router = Router()

async def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(F.text == "⚙️ Админ-панель")
async def admin_panel(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора.")
        return
    await message.answer("⚙️ Админ-панель\nВыберите действие:", reply_markup=admin_panel_kb())

@router.message(F.text == "➕ Добавить квартиру")
async def add_apartment_start(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.set_state(AddApartmentState.name)
    await message.answer("Введите название квартиры:", reply_markup=cancel_kb())

@router.message(AddApartmentState.name, F.text)
async def add_apt_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await cancel_action(message, state)
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AddApartmentState.description)
    await message.answer("Введите описание квартиры:")

@router.message(AddApartmentState.description, F.text)
async def add_apt_description(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await cancel_action(message, state)
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(AddApartmentState.price_hour)
    await message.answer("Введите цену за час (в рублях, например, 500):")

@router.message(AddApartmentState.price_hour, F.text)
async def add_apt_price_hour(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await cancel_action(message, state)
        return
    text = message.text.strip().replace(',', '.')
    if not re.match(r'^\d+(\.\d+)?$', text):
        await message.answer("Введите число (например, 500 или 500.50)")
        return
    await state.update_data(price_hour=float(text))
    await state.set_state(AddApartmentState.price_day)
    await message.answer("Введите цену за сутки (в рублях):")

@router.message(AddApartmentState.price_day, F.text)
async def add_apt_price_day(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await cancel_action(message, state)
        return
    text = message.text.strip().replace(',', '.')
    if not re.match(r'^\d+(\.\d+)?$', text):
        await message.answer("Введите число.")
        return
    await state.update_data(price_day=float(text))
    await state.set_state(AddApartmentState.photo)
    await message.answer("Загрузите фото квартиры (изображение):")

@router.message(AddApartmentState.photo, F.photo)
async def add_apt_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id
    data = await state.get_data()
    async with async_session() as session:
        new_apt = Apartment(
            name=data['name'],
            description=data['description'],
            price_per_hour=data['price_hour'],
            price_per_day=data['price_day'],
            photo_file_id=file_id,
            is_active=True
        )
        session.add(new_apt)
        await session.commit()
    await state.clear()
    await message.answer("✅ Квартира успешно добавлена!", reply_markup=main_menu_kb(is_admin=True))

@router.message(AddApartmentState.photo)
async def add_apt_photo_incorrect(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await cancel_action(message, state)
        return
    await message.answer("Пожалуйста, загрузите фото (изображение).")

@router.message(F.text == "❌ Отмена")
async def cancel_action(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_menu_kb(is_admin=await is_admin(message.from_user.id)))

@router.message(F.text == "📋 Список квартир")
async def list_apartments_admin(message: types.Message):
    if not await is_admin(message.from_user.id):
        return
    async with async_session() as session:
        result = await session.execute(select(Apartment))
        apartments = result.scalars().all()
        if not apartments:
            await message.answer("Квартир пока нет.")
            return
        for apt in apartments:
            text = f"🏠 {apt.name}\n{apt.description}\n💰 {apt.price_per_hour} ₽/час, {apt.price_per_day} ₽/сутки\n{'✅ Активна' if apt.is_active else '❌ Неактивна'}"
            await message.answer_photo(apt.photo_file_id, caption=text, reply_markup=admin_apartment_actions_kb(apt.id))

@router.message(F.text == "📋 Список клиентов")
async def list_clients(message: types.Message):
    if not await is_admin(message.from_user.id):
        return
    async with async_session() as session:
        users = await session.execute(select(User))
        users = users.scalars().all()
        if not users:
            await message.answer("Нет зарегистрированных клиентов.")
            return
        text = "📋 **Список клиентов:**\n\n"
        for u in users:
            bookings = await session.execute(
                select(Booking).where(Booking.user_id == u.id, Booking.is_confirmed == True)
            )
            bookings = bookings.scalars().all()
            status = "🔴 Есть бронь" if bookings else "🟢 Нет броней"
            text += (
                f"ID: {u.id}\n"
                f"👤 {u.full_name}\n"
                f"📱 {u.phone}\n"
                f"📄 [Скачать паспорт]({u.passport_file})\n"
                f"Статус: {status}\n\n"
            )
        await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "🔙 Назад")
async def back_to_menu(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu_kb(is_admin=await is_admin(message.from_user.id)))
