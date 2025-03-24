from aiogram import Router
from aiogram.types import (
    Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from services.partners import USERS, PARTNERS

router = Router()


@router.message(Command("dr_partner"))
async def dl_partner_command(message: Message):
    user_id = message.from_user.id

    # Ищем пользователя в словаре USERS
    user_data = None
    for user in USERS.values():
        if user.get("id") == user_id:
            user_data = user
            break

    if not user_data:
        await message.answer(
            "⚠️ Пожалуйста, авторизуйтесь с помощью команды /start ⚠️"
        )
        return

    # Получаем доступные ссылки для пользователя
    allowed_partners = user_data.get("allowed_partners", [])
    if not allowed_partners:
        await message.answer("У вас нет доступа к подаче DealReg.")
        return

    # Создаем инлайн-кнопки для доступных ссылок
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for partner in allowed_partners:
        if partner in PARTNERS:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=partner,
                    web_app=WebAppInfo(url=PARTNERS[partner]))
            ])

    await message.answer(
        "Нажмите на кнопку ниже для запуска процесса подачи DealReg'a",
        reply_markup=keyboard
    )
