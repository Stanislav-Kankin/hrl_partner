from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Используйте /dl_partner для подачи заявки на DealReg, "
        "или /my_dl для запроса статуса заявки."
    )
