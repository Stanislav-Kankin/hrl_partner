from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from services.bitrix import BitrixAPI
import os
import logging
from datetime import datetime

router = Router()
logger = logging.getLogger(__name__)


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
        if isinstance(result, dict):
            deal_info = result

            # Получение информации об ответственном
            responsible_id = deal_info.get('ASSIGNED_BY_ID')
            user_data = await bitrix.get_user(responsible_id)

            if user_data is None or not user_data.get('result'):
                responsible_name = 'Неизвестно'
                work_phone = 'Неизвестно'
                email = 'Неизвестно'
                position = 'Неизвестно'
                logger.error(
                    f"Failed to retrieve user data for ID: {responsible_id}")
            else:
                user_info = user_data.get('result', [{}])[0]
                responsible_name = f"{user_info.get('NAME', 'Неизвестно')} {
                    user_info.get('LAST_NAME', 'Неизвестно')}"
                work_phone = user_info.get('WORK_PHONE', 'Неизвестно')
                email = user_info.get('EMAIL', 'Неизвестно')
                position = user_info.get('WORK_POSITION', 'Неизвестно')

            # Форматирование даты и времени
            date_create = datetime.fromisoformat(
                deal_info.get('DATE_CREATE', '')
                ).strftime('%d.%m.%Y %H:%M')
            date_modify = datetime.fromisoformat(
                deal_info.get('DATE_MODIFY', '')
                ).strftime('%d.%m.%Y %H:%M')
            last_activity_date = deal_info.get(
                'LAST_ACTIVITY_TIME', 'Неизвестно')

            deal_message = (
                f"<b>Информация о сделке:</b>\n"
                f"<b>Номер:</b> {deal_info.get('ID', 'Не указано')}\n"
                f"<b>Название:</b> {deal_info.get('TITLE', 'Не указано')}\n"
                f"<b>Статус:</b> {deal_info.get('STAGE_ID', 'Не указано')}\n"
                f"<b>Компания</b>: {deal_info.get('COMPANY_ID', 'Не указано')}\n"
                f"<b>ID ответственного</b>: {responsible_id}\n"
                f"<b>Дата создания:</b> {date_create}\n"
                f"<b>Дата изменения:</b> {date_modify}\n"
                f"<b>Ответственный:</b> {responsible_name}\n"
                f"<b>Должность:</b> {position}\n"
                f"<b>Рабочий телефон:</b> <code>{work_phone}</code>\n"
                f"<b>Почта сотрудника:</b> <code>{email}</code>\n"
                f"<b>Дата последнего касания: <u>{last_activity_date}</u></b>\n"
                f"<b>Контакт:</b> {deal_info.get('CONTACT_ID', 'Не указано')}\n"
                f"<b>Закрыта:</b> {
                    'Да' if deal_info.get('CLOSED') == 'Y' else 'Нет'}\n"
            )
            await message.answer(deal_message, parse_mode=ParseMode.HTML)
        else:
            logging.error(f"Unexpected response structure: {deal_data}")
            await message.answer(
                "Произошла ошибка при получении информации о сделке.")

    await state.clear()
