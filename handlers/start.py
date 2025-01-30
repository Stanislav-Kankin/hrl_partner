from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.database import get_db, get_partner_id

router = Router()


class DlPartner(StatesGroup):
    waiting_for_partner_id = State()


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    db = next(get_db())

    # Проверяем, есть ли партнер в базе данных
    partner_id = get_partner_id(db, user_id)
    if partner_id:
        await message.answer(
            "Привет! Я бот для работы с партнерами. "
            "Используйте /dl_partner для начала."
            )
    else:
        await message.answer(
            "Привет! Я бот для работы с партнерами. "
            "Введите Ваш ID партнёра:")
        await state.set_state(DlPartner.waiting_for_partner_id)
