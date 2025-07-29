import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
from db import init_db
from handlers import add, common, edit, inspect, remove

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

dp = Dispatcher(storage=MemoryStorage())
bot = Bot(token=TOKEN)


def register_handlers():
    dp.include_router(add.router)
    dp.include_router(inspect.router)
    dp.include_router(edit.router)
    dp.include_router(remove.router)
    dp.include_router(common.router)


async def main():
    register_handlers()
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
