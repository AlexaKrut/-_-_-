import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

API_TOKEN = "7548898545:AAEuDlHbqHy5QrCk3x9PgSm95xPhYALplvY"

async def main():
    bot = Bot(API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())