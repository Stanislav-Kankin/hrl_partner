from aiogram import Router
from aiogram.types import (
    Message, WebAppInfo,
    InlineKeyboardMarkup, InlineKeyboardButton
    )
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.partners import PARTNERS

router = Router()


class DlPartner(StatesGroup):
    waiting_for_partner_id = State()


@router.message(Command("dl_partner"))
async def dl_partner_command(message: Message, state: FSMContext):
    await message.answer("Введите Ваш ID партнёра:")
    await state.set_state(DlPartner.waiting_for_partner_id)


@router.message(DlPartner.waiting_for_partner_id)
async def process_partner_id(message: Message, state: FSMContext):
    partner_id = message.text

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
