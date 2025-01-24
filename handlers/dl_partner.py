# handlers/dl_partner.py
from aiogram import Router
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.partners import PARTNERS
from services.database import get_db, get_partner_id, add_partner
from models import Partner

router = Router()


class DlPartner(StatesGroup):
    waiting_for_partner_id = State()


@router.message(Command("dl_partner"))
async def dl_partner_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    db = next(get_db())  # Получаем сессию базы данных

    # Проверяем, есть ли партнер в базе данных
    partner_id = get_partner_id(db, user_id)
    if partner_id:
        # Если партнер уже есть в базе, используем его ID
        await process_partner_id(message, state, partner_id)
    else:
        # Если партнера нет, запрашиваем ID
        await message.answer("Введите Ваш ID партнёра:")
        await state.set_state(DlPartner.waiting_for_partner_id)


@router.message(DlPartner.waiting_for_partner_id)
async def process_partner_id(
    message: Message, state: FSMContext, partner_id=None
    ):
    if not partner_id:
        partner_id = message.text
        user_id = message.from_user.id
        db = next(get_db())  # Получаем сессию базы данных

        # Сохраняем партнера в базу данных
        add_partner(db, user_id, partner_id)

    # Проверяем, есть ли партнер в базе данных
    if partner_id in PARTNERS:
        # Получаем ссылку для партнера
        partner_link = PARTNERS[partner_id]

        # Создаем кнопку с веб-приложением
        web_app_info = WebAppInfo(url=partner_link)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(
                text="Заполнить форму", web_app=web_app_info
            )]]
        )

        await message.answer(
            "Заполните форму, нажмите на приложение в кнопке ниже:",
            reply_markup=keyboard
        )
    else:
        await message.answer("Партнер с таким ID не найден.")

    await state.clear()
