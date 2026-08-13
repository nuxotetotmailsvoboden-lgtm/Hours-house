from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

router = Router()

@router.callback_query(F.data.startswith("choose_apt_"))
async def choose_apartment(callback: types.CallbackQuery, state: FSMContext):
    apt_id = int(callback.data.split("_")[2])
    await callback.message.answer(f"Вы выбрали квартиру #{apt_id}. Функция бронирования будет добавлена в Шаге 3.")
    await callback.answer()

# Обработка админских действий (редактирование/удаление) – пока заглушки
@router.callback_query(F.data.startswith("edit_apt_"))
async def edit_apartment(callback: types.CallbackQuery):
    apt_id = int(callback.data.split("_")[2])
    await callback.message.answer(f"Редактирование квартиры #{apt_id} в разработке.")
    await callback.answer()

@router.callback_query(F.data.startswith("delete_apt_"))
async def delete_apartment(callback: types.CallbackQuery):
    apt_id = int(callback.data.split("_")[2])
    # Здесь можно реализовать подтверждение и удаление
    await callback.message.answer(f"Удаление квартиры #{apt_id} в разработке.")
    await callback.answer()
