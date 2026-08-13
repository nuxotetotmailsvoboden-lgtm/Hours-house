from aiogram import Router, types, F

router = Router()

@router.callback_query(F.data.startswith("edit_apt_"))
async def edit_apartment(callback: types.CallbackQuery):
    apt_id = int(callback.data.split("_")[2])
    await callback.message.answer(f"✏️ Редактирование квартиры #{apt_id} в разработке.")
    await callback.answer()

@router.callback_query(F.data.startswith("delete_apt_"))
async def delete_apartment(callback: types.CallbackQuery):
    apt_id = int(callback.data.split("_")[2])
    await callback.message.answer(f"🗑 Удаление квартиры #{apt_id} в разработке.")
    await callback.answer()
