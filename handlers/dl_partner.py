from aiogram import Router
from aiogram.types import (
    Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
    )
from aiogram.filters import Command
from services.partners import PARTNERS

router = Router()


@router.message(Command("dl_partner"))
async def dl_partner_command(message: Message):
    # Создаем инлайн-кнопки для каждой компании
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="НН",
                    web_app=WebAppInfo(url=PARTNERS["НН"])
                )
            ],
            [
                InlineKeyboardButton(
                    text="СБЕР РЕШЕНИЯ",
                    web_app=WebAppInfo(url=PARTNERS["СБЕР РЕШЕНИЯ"])
                )
            ],
            [
                InlineKeyboardButton(
                    text="БФТ",
                    web_app=WebAppInfo(url=PARTNERS["БФТ"])
                )
            ],
            [
                InlineKeyboardButton(
                    text="МТС",
                    web_app=WebAppInfo(url=PARTNERS["МТС"])
                )
            ]
        ]
    )

    await message.answer(
        "Выберите ссылку, актуальную для Вашей компании:",
        reply_markup=keyboard
    )
