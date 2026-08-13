from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from database import async_session
from models import User
from states.register import RegisterState
from keyboards.reply import main_menu_kb, remove_kb, choose_name_kb, choose_phone_kb
from config import ADMIN_IDS
import os, re

router = Router()

async def start_registration(message: types.Message, state: FSMContext):
    await state.set_state(RegisterState.choose_name_method)
    await message.answer(
        "Давайте зарегистрируемся.\nКак вы хотите указать своё имя?",
        reply_markup=choose_name_kb()
    )

@router.message(RegisterState.choose_name_method, F.text.in_(["👤 Использовать имя из Telegram", "✏️ Ввести вручную"]))
async def process_name_method(message: types.Message, state: FSMContext):
    if message.text == "👤 Использовать имя из Telegram":
        first = message.from_user.first_name or ""
        last = message.from_user.last_name or ""
        full_name = f"{first} {last}".strip()
        if not full_name:
            await message.answer("В вашем профиле не указано имя. Пожалуйста, введите вручную:")
            await state.set_state(RegisterState.full_name_manual)
            return
        await state.update_data(full_name=full_name)
        await ask_phone(message, state)
    else:
        await state.set_state(RegisterState.full_name_manual)
        await message.answer("Введите ваше полное ФИО (только буквы, пробелы и дефисы):", reply_markup=remove_kb())

@router.message(RegisterState.full_name_manual, F.text)
async def process_full_name_manual(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not re.match(r"^[A-Za-zА-Яа-яЁё\s\-']{2,50}$", name):
        await message.answer("Имя должно содержать только буквы, пробелы и дефисы (от 2 до 50 символов). Попробуйте снова:")
        return
    await state.update_data(full_name=name)
    await ask_phone(message, state)

async def ask_phone(message: types.Message, state: FSMContext):
    await state.set_state(RegisterState.choose_phone_method)
    await message.answer(
        "Теперь укажите номер телефона.\nВы можете отправить его через Telegram или ввести вручную:",
        reply_markup=choose_phone_kb()
    )

@router.message(RegisterState.choose_phone_method, F.text.in_(["📱 Отправить номер", "✏️ Ввести вручную"]))
async def process_phone_method(message: types.Message, state: FSMContext):
    if message.text == "📱 Отправить номер":
        await message.answer("Нажмите кнопку «Отправить номер» ниже.", reply_markup=choose_phone_kb())
        await state.set_state(RegisterState.waiting_contact)
    else:
        await state.set_state(RegisterState.phone_manual)
        await message.answer("Введите номер в формате +7XXXXXXXXXX:", reply_markup=remove_kb())

@router.message(RegisterState.waiting_contact, F.contact)
async def process_contact(message: types.Message, state: FSMContext):
    contact = message.contact
    phone = contact.phone_number
    await state.update_data(phone=phone)
    await ask_passport(message, state)

@router.message(RegisterState.phone_manual, F.text)
async def process_phone_manual(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    if not re.match(r"^\+?\d{10,15}$", phone):
        await message.answer("Некорректный номер. Введите в формате +7XXXXXXXXXX (10-15 цифр):")
        return
    if not phone.startswith('+'):
        phone = '+' + phone
    await state.update_data(phone=phone)
    await ask_passport(message, state)

async def ask_passport(message: types.Message, state: FSMContext):
    await state.set_state(RegisterState.passport)
    await message.answer(
        "Загрузите скан/фото вашего удостоверения личности (PDF, до 20 МБ):",
        reply_markup=remove_kb()
    )

@router.message(RegisterState.passport, F.document)
async def process_passport(message: types.Message, state: FSMContext, bot):
    document = message.document
    if document.mime_type != 'application/pdf':
        await message.answer("Пожалуйста, загрузите файл в формате PDF.")
        return
    if document.file_size > 20 * 1024 * 1024:
        await message.answer("Файл слишком большой. Максимальный размер 20 МБ.")
        return
    file_info = await bot.get_file(document.file_id)
    file_path = file_info.file_path
    os.makedirs("media/passports", exist_ok=True)
    local_filename = f"media/passports/{message.from_user.id}_{document.file_name}"
    await bot.download_file(file_path, local_filename)
    
    data = await state.get_data()
    full_name = data['full_name']
    phone = data['phone']
    
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
    
    await state.clear()
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer(
        f"✅ Регистрация завершена, {full_name}!\nТеперь вы можете пользоваться ботом.",
        reply_markup=main_menu_kb(is_admin)
    )

@router.message(RegisterState.passport)
async def incorrect_passport(message: types.Message):
    await message.answer("Пожалуйста, загрузите файл PDF.")
