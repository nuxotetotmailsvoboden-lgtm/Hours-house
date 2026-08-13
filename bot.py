import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import init_db
from handlers import start, register, menu
from handlers import admin, catalog
from handlers import callback
from handlers import booking

async def main():
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Инициализация БД
    await init_db()
    
    # Подключаем роутеры
    dp.include_router(start.router)
    dp.include_router(register.router)
    dp.include_router(menu.router)
    dp.include_router(admin.router)
    dp.include_router(catalog.router)
    dp.include_router(callback.router)
    dp.include_router(booking.router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
