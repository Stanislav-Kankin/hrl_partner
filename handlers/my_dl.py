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
            await message.answer(
                f"Информация о сделке:\nНомер: {
                    deal_info['ID']
                    }\nНазвание: {
                        deal_info['TITLE']
                        }\nСтатус: {deal_info['STAGE_ID']}")
        else:
            logging.error(f"Unexpected response structure: {deal_data}")
            await message.answer(
                "Произошла ошибка при получении информации о сделке."
                )

    await state.clear()
