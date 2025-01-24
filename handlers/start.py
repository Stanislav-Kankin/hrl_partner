from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

# Создаем объект Router
router = Router()


# Регистрируем обработчик команды /start
@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Привет! Я бот для работы с партнерами. "
        "Используйте /dl_partner для начала."
        )
