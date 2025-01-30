import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
import logging
from handlers import start, dl_partner, my_dl
from models import Base, engine

load_dotenv()

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Инициализация базы данных
Base.metadata.create_all(bind=engine)

# Инициализация бота
bot = Bot(
    token=os.getenv("BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрация обработчиков
dp.include_router(start.router)
dp.include_router(dl_partner.router)
dp.include_router(my_dl.router)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
