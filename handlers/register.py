from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from sqlalchemy import select
from database import async_session
from models import User
from states.register import RegisterState
from keyboards.reply import main_menu_kb, remove_kb
from config import ADMIN_IDS
import os

router = Router()

async def start_registration(message: types.Message, state: FSMContext):
    await state.set_state(RegisterState.full_name)
    await message.answer(
        "Введите ваше полное ФИО:",
        reply_markup=remove_kb()
    )

# Обработчик, когда пользователь только начал и ввел /start – сработает, если нет пользователя
# Мы переопределим обработку /start в start.py, но вызовем start_registration оттуда.
# Для простоты оставим здесь отдельный хендлер на /start, но тогда нужно убрать из start.py.
# Сделаем так: в start.py оставим проверку, если нет пользователя – вызовем сюда.

@router.message(RegisterState.full_name, F.text)
async def process_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await state.set_state(RegisterState.phone)
    await message.answer(
        "Теперь введите ваш номер телефона (в формате +7XXXXXXXXXX):"
    )

@router.message(RegisterState.phone, F.text)
async def process_phone(message: types.Message, state: FSMContext):
    # Простая валидация
    phone = message.text.strip()
    if not phone.startswith('+') or not phone[1:].isdigit():
        await message.answer("Пожалуйста, введите номер в формате +7XXXXXXXXXX")
        return
    await state.update_data(phone=phone)
    await state.set_state(RegisterState.passport)
    await message.answer(
        "Загрузите скан/фото вашего удостоверения личности (PDF-файл):"
    )

@router.message(RegisterState.passport, F.document)
async def process_passport(message: types.Message, state: FSMContext, bot):
    document = message.document
    if document.mime_type != 'application/pdf':
        await message.answer("Пожалуйста, загрузите файл в формате PDF.")
        return
    # Скачиваем файл
    file_info = await bot.get_file(document.file_id)
    file_path = file_info.file_path
    # Сохраняем локально (для Railway лучше использовать облачное хранилище, но пока так)
    os.makedirs("media/passports", exist_ok=True)
    local_filename = f"media/passports/{message.from_user.id}_{document.file_name}"
    await bot.download_file(file_path, local_filename)
    
    # Получаем данные из состояния
    data = await state.get_data()
    full_name = data['full_name']
    phone = data['phone']
    
    # Сохраняем в БД
    async with async_session() as session:
        new_user = User(
            tg_id=message.from_user.id,
            full_name=full_name,
            phone=phone,
            passport_file=local_filename,
            is_admin=message.from_user.id in ADMIN_IDS
        )
        session.add(new_user)
        await session.commit()
    
    # Завершаем состояние
    await state.clear()
    
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer(
        f"✅ Регистрация завершена, {full_name}!\n"
        "Теперь вы можете пользоваться ботом.",
        reply_markup=main_menu_kb(is_admin)
    )

# Обработчик на случай, если пользователь отправил не документ
@router.message(RegisterState.passport)
async def incorrect_passport(message: types.Message):
    await message.answer("Пожалуйста, загрузите файл PDF.")
