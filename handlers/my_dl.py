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
import re
from services.partners import USERS

router = Router()
logger = logging.getLogger(__name__)


class MyDealReg(StatesGroup):
    waiting_for_dealreg_number = State()


@router.message(Command("my_dl"))
async def my_dl_command(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Проверяем, авторизован ли пользователь
    if not any(user.get("id") == user_id for user in USERS.values()):
        await message.answer(
            "⚠️ Пожалуйста, авторизуйтесь с помощью команды /start ⚠️")
        return

    await message.answer("Введите номер DealReg:")
    await state.set_state(MyDealReg.waiting_for_dealreg_number)


@router.message(MyDealReg.waiting_for_dealreg_number)
async def process_dealreg_number(message: Message, state: FSMContext):
    dealreg_number = message.text
    bitrix = BitrixAPI(os.getenv("BITRIX_WEBHOOK"))

    # Пытаемся найти DealReg по ID
    dealreg_data = await bitrix.get_dealreg_by_id(dealreg_number)

    if not dealreg_data or not dealreg_data.get('result'):
        await message.answer("DealReg с таким номером не найден. ❌")
        await state.clear()
        return

    dealreg_info = dealreg_data['result'].get('item', {})
    dealreg_id = dealreg_info.get('id')
    dealreg_stage_id = dealreg_info.get('stageId')  # ID стадии
    dealreg_previous_stage_id = dealreg_info.get('previousStageId')
    dealreg_company = dealreg_info.get('companyId')
    dealreg_created = dealreg_info.get('createdTime')
    dealreg_modified = dealreg_info.get('updatedTime')
    contact_ids = dealreg_info.get('contactIds', [0])

    # Логируем данные DealReg
    logger.info(f"DealReg Info: {dealreg_info}")

    # Получаем информацию о компании
    if dealreg_company:
        company_data = await bitrix.get_company_info(dealreg_company)
        company_name = company_data.get('result', {}).get('TITLE', 'Неизвестно') if company_data else 'Неизвестно'
    else:
        company_name = 'Неизвестно'

    # Ручное сопоставление стадий
    stages = {
        'DT183_37:NEW': 'Начало',
        'DT183_37:PREPARATION': 'Прогрев партнёра',
        'DT183_37:UC_AAYY8N': 'Квалификация HRlink',
        'DT183_37:UC_92D1DY': 'Прогрев HRlink',
        'DT183_37:UC_XFDN2C': 'Назначена встреча',
        'DT183_37:16': 'Встреча не состоялась',
        'DT183_37:UC_GDQZQ3': 'Истекает',
        'DT183_37:UC_7O0GZ6': 'Продлён'
    }

    # Получаем название стадии
    stage_name = stages.get(dealreg_stage_id, 'Неизвестно')
    previous_stage_name = stages.get(dealreg_previous_stage_id, 'Неизвестно') if dealreg_previous_stage_id else 'Неизвестно'

    # Получаем информацию об ответственном за сделку
    responsible_name = 'Не назначен менеджер'
    responsible_email = 'Неизвестно'
    responsible_telegram = 'Неизвестно'
    responsible_position = 'Неизвестно'
    deal_responsible_for_deal_id = dealreg_info.get('ufCrm27_1731395822')  # Ответственный за сделку

    if deal_responsible_for_deal_id:
        # Если есть ID ответственного за сделку, получаем его данные
        responsible_data = await bitrix.get_user(deal_responsible_for_deal_id)
        if responsible_data and responsible_data.get('result'):
            responsible_info = responsible_data.get('result', [{}])[0]
            responsible_name = f"{responsible_info.get('NAME', 'Неизвестно')} {responsible_info.get('LAST_NAME', 'Неизвестно')}"
            responsible_email = responsible_info.get('EMAIL', 'Неизвестно')
            responsible_telegram = responsible_info.get('UF_USR_1665651064433', 'Неизвестно')
            responsible_position = responsible_info.get('WORK_POSITION', 'Неизвестно')
    elif dealreg_info.get('assignedById'):
        responsible_data = await bitrix.get_user(dealreg_info.get('assignedById'))
        if responsible_data and responsible_data.get('result'):
            responsible_info = responsible_data.get('result', [{}])[0]
            responsible_name = f"{responsible_info.get('NAME', 'Неизвестно')} {responsible_info.get('LAST_NAME', 'Неизвестно')}"
            responsible_email = responsible_info.get('EMAIL', 'Неизвестно')
            responsible_telegram = responsible_info.get('UF_USR_1665651064433', 'Неизвестно')
            responsible_position = responsible_info.get('WORK_POSITION', 'Неизвестно')
    elif contact_ids:
        # Если ответственный не назначен, проверяем контакты
        for contact_id in contact_ids:
            contact_data = await bitrix.get_contact_info(contact_id)
            if contact_data and contact_data.get('result'):
                responsible_info = contact_data.get('result', {})
                responsible_name = f"{responsible_info.get('NAME', 'Неизвестно')} {responsible_info.get('LAST_NAME', 'Неизвестно')}"
                responsible_email = responsible_info.get('EMAIL', 'Неизвестно')
                responsible_telegram = responsible_info.get('UF_USR_1665651064433', 'Неизвестно')
                responsible_position = responsible_info.get('WORK_POSITION', 'Неизвестно')
                break

    # Получаем информацию о касаниях с клиентом из сделки
    deal_id = dealreg_info.get('parentId2')  # Используем parentId2 как ID сделки
    if deal_id:
        deal_touches_data = await bitrix.get_deal_touches(deal_id)
        deal_touches_info = []
        if deal_touches_data and deal_touches_data.get('result'):
            for touch in deal_touches_data['result']:
                touch_info = f"{touch.get('CREATED')}: {touch.get('COMMENT')}"
                # Удаляем HTML-теги
                touch_info = re.sub(r'<[^>]+>', '', touch_info)
                touch_info = re.sub(r'\[/?[A-Z]+\]', '', touch_info)
                deal_touches_info.append(touch_info)
        else:
            logger.error(f"No touches data found for deal ID: {deal_id}")
    else:
        logger.error("Deal ID not found in DealReg data.")

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
        f"<b>Компания:</b> {company_name}\n"
        "\n"
        f"<b>Текущая стадия:</b> <u>{stage_name}</u>\n"
        f"<b>Предыдущая стадия:</b> {previous_stage_name}\n"
        "\n"
        f"👤 <b>Ответственный за сделку:</b> {responsible_name}\n"
        f"🤝 <b>Должность:</b> {responsible_position}\n"
        f"📧 <b>Email:</b> <code>{responsible_email}</code>\n"
        f"📞<b>Telegram:</b> <code>{responsible_telegram}</code>\n"
        "\n"
        f"<b>Дата создания:</b> {created_date}\n"
        f"<b>Дата изменения:</b> {modified_date}\n"
        "\n"
    )

    # Добавляем информацию о касаниях с клиентом из сделки
    if deal_touches_info:
        dealreg_message += "\n<b>Касания с клиентом (Сделка):</b>\n" + "\n".join(deal_touches_info)
        print(deal_touches_info)
    else:
        dealreg_message += "\n<b>Касания с клиентом (Сделка):</b> Нет данных."

    # Разбиваем сообщение на части, если оно слишком длинное
    max_length = 4096  # Максимальная длина сообщения в Telegram
    if len(dealreg_message) > max_length:
        messages = [dealreg_message[i:i + max_length] for i in range(0, len(dealreg_message), max_length)]
        for msg in messages:
            await message.answer(msg, parse_mode=ParseMode.HTML)text
    else:
        await message.answer(dealreg_message, parse_mode=ParseMode.HTML)

    await state.clear()
