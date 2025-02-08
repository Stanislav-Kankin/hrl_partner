from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.bitrix import BitrixAPI
import os
import logging
from datetime import datetime

router = Router()


class MyDealReg(StatesGroup):
    waiting_for_deal_id = State()


@router.message(Command("my_dl"))
async def my_dl_command(message: Message, state: FSMContext):
    await message.answer("Введите интересующий вас номер DealReg:")
    await state.set_state(MyDealReg.waiting_for_deal_id)


@router.message(MyDealReg.waiting_for_deal_id)
async def process_deal_id(message: Message, state: FSMContext):
    deal_id = message.text
    bitrix = BitrixAPI(os.getenv("BITRIX_WEBHOOK"))
    deal_data = await bitrix.get_deal(deal_id=deal_id)

    if not deal_data or not deal_data.get('result'):
        await message.answer("Сделка с таким номером не найдена.")
    else:
        result = deal_data['result']
        if isinstance(result, dict):  # Проверяем, что результат — это словарь
            deal_info = result

            responsible_id = deal_info.get('ASSIGNED_BY_ID')
            user_data = await bitrix.get_user(responsible_id)
            responsible_name = user_data.get(
                'result', [{}])[0].get('NAME', 'Неизвестно')

            # Форматирование даты и времени
            date_create = datetime.fromisoformat(
                deal_info.get('DATE_CREATE', '')
                ).strftime('%d.%m.%Y %H:%M')
            date_modify = datetime.fromisoformat(
                deal_info.get('DATE_MODIFY', '')
                ).strftime('%d.%m.%Y %H:%M')

            deal_message = (
                f"Информация о сделке:\n"
                f"Номер: {deal_info.get('ID', 'Не указано')}\n"
                f"Название: {deal_info.get('TITLE', 'Не указано')}\n"
                f"Статус: {deal_info.get('STAGE_ID', 'Не указано')}\n"
                f"Сумма: {deal_info.get('OPPORTUNITY', 'Не указано')} руб.\n"
                f"Компания: {deal_info.get('COMPANY_ID', 'Не указано')}\n"
                f"Дата создания: {date_create}\n"
                f"Дата изменения: {date_modify}\n"
                f"ID ответственного: {responsible_id}\n"
                f"Ответсвтенный: {responsible_name}\n"
                f"Контакт: {deal_info.get('CONTACT_ID', 'Не указано')}\n"
                f"Закрыта: {'Да' if deal_info.get('CLOSED') == 'Y' else 'Нет'}\n"
            )
            await message.answer(deal_message)
        else:
            logging.error(f"Unexpected response structure: {deal_data}")
            await message.answer("Произошла ошибка при получении информации о сделке.")

    await state.clear()
