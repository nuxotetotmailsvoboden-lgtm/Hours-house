from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from database import async_session
from models import Apartment
from states.admin import EditApartmentState
from keyboards.inline import edit_apartment_menu_kb, confirm_delete_kb, admin_apartment_actions_kb
from config import ADMIN_IDS
import re

router = Router()

async def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ------------------- РЕДАКТИРОВАНИЕ -------------------

@router.callback_query(F.data.startswith("edit_apt_"))
async def edit_apartment(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.")
        return
    apartment_id = int(callback.data.split("_")[2])
    await state.update_data(apartment_id=apartment_id)
    await state.set_state(EditApartmentState.choosing_field)
    await callback.message.delete()
    await callback.message.answer("Что хотите изменить?", reply_markup=edit_apartment_menu_kb(apartment_id))
    await callback.answer()

@router.callback_query(F.data.startswith("edit_field_"))
async def edit_field(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.")
        return
    _, _, apartment_id, field = callback.data.split("_")
    apartment_id = int(apartment_id)
    await state.update_data(apartment_id=apartment_id, field=field)
    field_names = {
        "name": "новое название",
        "description": "новое описание",
        "price_hour": "новую цену за час (число)",
        "price_day": "новую цену за сутки (число)",
        "photo": "новое фото (изображение)",
        "active": "активность (введите 'да' или 'нет')"
    }
    if field == "photo":
        await state.set_state(EditApartmentState.editing_photo)
        await callback.message.answer("Загрузите новое фото для квартиры.")
    elif field == "active":
        await state.set_state(EditApartmentState.choosing_field)  # чтобы не запрашивать текст
        # Меняем активность сразу
        async with async_session() as session:
            apt = await session.get(Apartment, apartment_id)
            if apt:
                apt.is_active = not apt.is_active
                await session.commit()
                status = "активна" if apt.is_active else "неактивна"
                await callback.message.answer(f"✅ Статус изменён: квартира теперь {status}")
        await callback.message.answer("Что ещё хотите изменить?", reply_markup=edit_apartment_menu_kb(apartment_id))
        await callback.answer()
    else:
        await state.set_state(getattr(EditApartmentState, f"editing_{field}"))
        await callback.message.answer(f"Введите {field_names.get(field, 'новое значение')}:")
    await callback.answer()

@router.message(EditApartmentState.editing_name, F.text)
async def edit_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    apt_id = data.get('apartment_id')
    async with async_session() as session:
        apt = await session.get(Apartment, apt_id)
        if apt:
            apt.name = message.text.strip()
            await session.commit()
            await message.answer("✅ Название обновлено.")
    await state.set_state(EditApartmentState.choosing_field)
    await message.answer("Что ещё хотите изменить?", reply_markup=edit_apartment_menu_kb(apt_id))

@router.message(EditApartmentState.editing_description, F.text)
async def edit_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    apt_id = data.get('apartment_id')
    async with async_session() as session:
        apt = await session.get(Apartment, apt_id)
        if apt:
            apt.description = message.text.strip()
            await session.commit()
            await message.answer("✅ Описание обновлено.")
    await state.set_state(EditApartmentState.choosing_field)
    await message.answer("Что ещё хотите изменить?", reply_markup=edit_apartment_menu_kb(apt_id))

@router.message(EditApartmentState.editing_price_hour, F.text)
async def edit_price_hour(message: types.Message, state: FSMContext):
    text = message.text.strip().replace(',', '.')
    if not re.match(r'^\d+(\.\d+)?$', text):
        await message.answer("Введите число (например, 500 или 500.50).")
        return
    data = await state.get_data()
    apt_id = data.get('apartment_id')
    async with async_session() as session:
        apt = await session.get(Apartment, apt_id)
        if apt:
            apt.price_per_hour = float(text)
            await session.commit()
            await message.answer("✅ Цена за час обновлена.")
    await state.set_state(EditApartmentState.choosing_field)
    await message.answer("Что ещё хотите изменить?", reply_markup=edit_apartment_menu_kb(apt_id))

@router.message(EditApartmentState.editing_price_day, F.text)
async def edit_price_day(message: types.Message, state: FSMContext):
    text = message.text.strip().replace(',', '.')
    if not re.match(r'^\d+(\.\d+)?$', text):
        await message.answer("Введите число (например, 5000).")
        return
    data = await state.get_data()
    apt_id = data.get('apartment_id')
    async with async_session() as session:
        apt = await session.get(Apartment, apt_id)
        if apt:
            apt.price_per_day = float(text)
            await session.commit()
            await message.answer("✅ Цена за сутки обновлена.")
    await state.set_state(EditApartmentState.choosing_field)
    await message.answer("Что ещё хотите изменить?", reply_markup=edit_apartment_menu_kb(apt_id))

@router.message(EditApartmentState.editing_photo, F.photo)
async def edit_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    apt_id = data.get('apartment_id')
    photo = message.photo[-1]
    file_id = photo.file_id
    async with async_session() as session:
        apt = await session.get(Apartment, apt_id)
        if apt:
            apt.photo_file_id = file_id
            await session.commit()
            await message.answer("✅ Фото обновлено.")
    await state.set_state(EditApartmentState.choosing_field)
    await message.answer("Что ещё хотите изменить?", reply_markup=edit_apartment_menu_kb(apt_id))

@router.message(EditApartmentState.editing_photo)
async def edit_photo_incorrect(message: types.Message):
    await message.answer("Пожалуйста, загрузите изображение.")

@router.callback_query(F.data.startswith("edit_done_"))
async def edit_done(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.")
        return
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("✅ Редактирование завершено.")
    await callback.answer()

# ------------------- УДАЛЕНИЕ -------------------

@router.callback_query(F.data.startswith("delete_apt_"))
async def delete_apartment(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.")
        return
    apartment_id = int(callback.data.split("_")[2])
    await state.update_data(apartment_id=apartment_id)
    await state.set_state(EditApartmentState.confirming_delete)
    # Проверяем, есть ли брони
    async with async_session() as session:
        apt = await session.get(Apartment, apartment_id)
        if not apt:
            await callback.answer("Квартира не найдена.")
            return
        # Проверим, есть ли активные брони
        bookings = await session.execute(
            select(Booking).where(Booking.apartment_id == apartment_id, Booking.is_confirmed == True)
        )
        bookings = bookings.scalars().all()
        if bookings:
            await callback.message.answer(
                f"⚠️ На квартиру «{apt.name}» есть активные брони. Удалить невозможно, сначала отмените брони."
            )
            await state.clear()
            await callback.answer()
            return
    await callback.message.delete()
    await callback.message.answer(
        f"⚠️ Вы уверены, что хотите удалить квартиру «{apt.name}»? Это действие необратимо.",
        reply_markup=confirm_delete_kb(apartment_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.")
        return
    apartment_id = int(callback.data.split("_")[2])
    async with async_session() as session:
        apt = await session.get(Apartment, apartment_id)
        if apt:
            await session.delete(apt)
            await session.commit()
            await callback.message.delete()
            await callback.message.answer(f"✅ Квартира «{apt.name}» удалена.")
        else:
            await callback.message.answer("❌ Квартира не найдена.")
    await state.clear()
    await callback.answer()

@router.callback_query(F.data.startswith("cancel_delete_"))
async def cancel_delete(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.")
        return
    await callback.message.delete()
    await callback.message.answer("❌ Удаление отменено.")
    await state.clear()
    await callback.answer()
