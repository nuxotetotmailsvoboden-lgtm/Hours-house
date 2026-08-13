from handlers.register import start_registration

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if user:
            is_admin = tg_id in ADMIN_IDS
            await message.answer(
                f"С возвращением, {user.full_name}! 👋",
                reply_markup=main_menu_kb(is_admin)
            )
        else:
            await start_registration(message, state)
