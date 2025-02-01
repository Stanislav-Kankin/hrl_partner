from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.bitrix import BitrixAPI
import os
import logging

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
    deal_data = bitrix.get_deal(deal_id=deal_id)

    if not deal_data or not deal_data.get('result'):
        await message.answer("Сделка с таким номером не найдена.")
    else:
        result = deal_data['result']
        if isinstance(result, list) and len(result) > 0:
            deal_info = result[0]
            deal_message = (
                f"Информация о сделке:\n"
                f"Номер: {deal_info['ID']}\n"
                f"Название: {deal_info['TITLE']}\n"
                f"Статус: {deal_info['STAGE_ID']}\n"
                f"Сумма: {deal_info.get('OPPORTUNITY', 'Не указано')}\n"
                f"Контакт: {deal_info.get('CONTACT_ID', 'Не указано')}\n"
                f"Компания: {deal_info.get('COMPANY_ID', 'Не указано')}\n"
                f"Дата создания: {deal_info.get('DATE_CREATE', 'Не указано')}\n"
                f"Дата изменения: {deal_info.get('DATE_MODIFY', 'Не указано')}\n"
            )
            await message.answer(deal_message)
        else:
            logging.error(f"Unexpected response structure: {deal_data}")
            await message.answer(
                "Произошла ошибка при получении информации о сделке."
            )

    await state.clear()
