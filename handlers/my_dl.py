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
    waiting_for_dealreg_number = State()


@router.message(Command("my_dl"))
async def my_dl_command(message: Message, state: FSMContext):
    await message.answer("Введите номер DealReg:")
    await state.set_state(MyDealReg.waiting_for_dealreg_number)


@router.message(MyDealReg.waiting_for_dealreg_number)
async def process_dealreg_number(message: Message, state: FSMContext):
    dealreg_number = message.text
    bitrix = BitrixAPI(os.getenv("BITRIX_WEBHOOK"))

    # Пытаемся найти DealReg по ID
    dealreg_data = await bitrix.get_dealreg_by_id(dealreg_number)

    if not dealreg_data or not dealreg_data.get('result'):
        await message.answer("DealReg с таким номером не найден.")
        await state.clear()
        return

    dealreg_info = dealreg_data['result'].get('item', {})
    dealreg_id = dealreg_info.get('id')
    dealreg_title = dealreg_info.get('title')
    dealreg_stage = dealreg_info.get('stageId')
    dealreg_company = dealreg_info.get('companyId')
    dealreg_created = dealreg_info.get('createdTime')
    dealreg_modified = dealreg_info.get('updatedTime')
    contact_ids = dealreg_info.get('contactIds', [0])

    # Получаем информацию о компании
    if dealreg_company:
        company_data = await bitrix.get_company_info(dealreg_company)
        company_name = company_data.get('result', {}).get('TITLE', 'Неизвестно') if company_data else 'Неизвестно'
    else:
        company_name = 'Неизвестно'

    # Получаем информацию о статусе
    stage_data = await bitrix.get_deal_stage(dealreg_stage)
    stage_name = stage_data.get('result', {}).get('NAME', 'Неизвестно') if stage_data else 'Неизвестно'

    # Получаем информацию об ответственном за сделку
    responsible_name = 'Не назначен менеджер'
    deal_responsible_for_deal_id = dealreg_info.get('ufCrm27_1731395822')  # Замените на правильное поле

    if deal_responsible_for_deal_id:
        # Если есть ID ответственного за сделку, получаем его данные
        responsible_data = await bitrix.get_user(deal_responsible_for_deal_id)
        if responsible_data and responsible_data.get('result'):
            responsible_name = (
                f"{responsible_data.get('result', [{}])[0].get('NAME', 'Неизвестно')} "
                f"{responsible_data.get('result', [{}])[0].get('LAST_NAME', 'Неизвестно')}"
            )
    elif dealreg_info.get('assignedById'):
        # Если ответственный за сделку не найден, используем обычного ответственного
        responsible_data = await bitrix.get_user(dealreg_info.get('assignedById'))
        if responsible_data and responsible_data.get('result'):
            responsible_name = (
                f"{responsible_data.get('result', [{}])[0].get('NAME', 'Неизвестно')} "
                f"{responsible_data.get('result', [{}])[0].get('LAST_NAME', 'Неизвестно')}"
            )
    elif contact_ids:
        # Если ответственный не назначен, проверяем контакты
        for contact_id in contact_ids:
            contact_data = await bitrix.get_contact_info(contact_id)
            if contact_data and contact_data.get('result'):
                responsible_name = (
                    f"{contact_data.get('result', {}).get('NAME', 'Неизвестно')} "
                    f"{contact_data.get('result', {}).get('LAST_NAME', 'Неизвестно')}"
                )
                break

    # Форматируем даты
    try:
        created_date = datetime.fromisoformat(dealreg_created).strftime('%d.%m.%Y %H:%M') if dealreg_created else 'Неизвестно'
        modified_date = datetime.fromisoformat(dealreg_modified).strftime('%d.%m.%Y %H:%M') if dealreg_modified else 'Неизвестно'
    except (TypeError, ValueError) as e:
        logger.error(f"Error parsing dates: {e}")
        created_date = 'Неизвестно'
        modified_date = 'Неизвестно'

    # Формируем сообщение
    dealreg_message = (
        f"<b>Информация о DealReg:</b>\n"
        f"<b>Номер:</b> {dealreg_id}\n"
        f"<b>Название:</b> {dealreg_title}\n"
        f"<b>Статус:</b> {stage_name}\n"
        f"<b>Компания:</b> {company_name}\n"
        f"<b>Ответственный за сделку:</b> {responsible_name}\n"
        f"<b>Дата создания:</b> {created_date}\n"
        f"<b>Дата изменения:</b> {modified_date}\n"
    )
    await message.answer(dealreg_message, parse_mode=ParseMode.HTML)

    await state.clear()
