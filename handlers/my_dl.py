from aiogram import Router, F
from aiogram.types import (
    Message, InlineKeyboardMarkup,
    InlineKeyboardButton, CallbackQuery
)
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
import asyncio

router = Router()
logger = logging.getLogger(__name__)


class MyDealReg(StatesGroup):
    waiting_for_dealreg_number = State()


class TouchStates(StatesGroup):
    waiting_for_touch_deal_id = State()


def is_user_admin(user_id: int) -> bool:
    for user in USERS.values():
        if user.get("id") == user_id:
            user_email = user.get("email", "").lower()
            return user_email == "admin" or "admin" in user_email
    return False


async def get_partner_email_from_dealreg(
        dealreg_info: dict, bitrix: BitrixAPI) -> str:
    contact_id = dealreg_info.get('contactId')
    if not contact_id:
        logger.warning("No contact ID found in DealReg")
        return 'Неизвестно'
    logger.info(f"Getting contact info for ID: {contact_id}")
    contact_data = await bitrix.get_contact_info(contact_id)
    if not contact_data or not contact_data.get('result'):
        logger.warning(f"No contact data found for ID: {contact_id}")
        return 'Неизвестно'
    contact_info = contact_data['result']
    logger.info(f"Full contact info: {contact_info}")
    email_list = contact_info.get('EMAIL', [])
    email = email_list[0]['VALUE'] if email_list else None
    if email:
        logger.info(f"Found partner email in contact: {email}")
        return email
    for field_name, field_value in contact_info.items():
        if field_name.startswith('UF_') and field_value and isinstance(field_value, str) and '@' in field_value:
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', field_value):
                logger.info(f"Found partner email in custom field {field_name}: {field_value}")
                return field_value
    logger.warning("No partner email found in contact")
    return 'Неизвестно'


async def check_dealreg_access(user_email: str, dealreg_info: dict, bitrix: BitrixAPI) -> bool:
    logger.info(f"Проверка доступа для пользователя: {user_email}")
    if user_email.lower() == "admin":
        logger.info("Доступ разрешен: Пользователь — админ")
        return True
    for user in USERS.values():
        if user.get("email") == user_email and user.get("role") == "observer":
            logger.info(f"Доступ разрешен: Пользователь {user_email} — наблюдатель")
            return True
    partner_email = await get_partner_email_from_dealreg(dealreg_info, bitrix)
    logger.info(f"Email партнёра из DealReg: {partner_email}")
    if partner_email == 'Неизвестно':
        logger.info("Email партнёра неизвестен. Проверяем, является ли пользователь создателем или ответственным.")
        created_by_id = dealreg_info.get('createdById')
        if created_by_id:
            created_by_data = await bitrix.get_user(created_by_id)
            if created_by_data and created_by_data.get('result'):
                created_by_email = created_by_data['result'][0].get('EMAIL', '').lower()
                logger.info(f"Email создателя DealReg: {created_by_email}")
                if created_by_email == user_email.lower():
                    logger.info("Доступ разрешен: Пользователь — создатель DealReg")
                    return True
        assigned_by_id = dealreg_info.get('assignedById')
        if assigned_by_id:
            assigned_by_data = await bitrix.get_user(assigned_by_id)
            if assigned_by_data and assigned_by_data.get('result'):
                assigned_by_email = assigned_by_data['result'][0].get('EMAIL', '').lower()
                logger.info(f"Email ответственного за DealReg: {assigned_by_email}")
                if assigned_by_email == user_email.lower():
                    logger.info("Доступ разрешен: Пользователь — ответственный за DealReg")
                    return True
        logger.warning("Доступ запрещен: Пользователь не является партнёром, создателем или ответственным")
        return False
    access_granted = user_email.lower() == partner_email.lower() if isinstance(partner_email, str) else False
    if access_granted:
        logger.info(f"Доступ разрешен: Email пользователя {user_email} совпадает с email партнёра {partner_email}")
    else:
        logger.warning(f"Доступ запрещен: Email пользователя {user_email} не совпадает с email партнёра {partner_email}")
    return access_granted


@router.message(Command("my_dr"))
async def my_dl_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_email = None
    for user in USERS.values():
        if user.get("id") == user_id:
            user_email = user.get("email")
            break
    if not user_email:
        await message.answer("⚠️ Пожалуйста, авторизуйтесь с помощью команды /start ⚠️")
        return
    await state.update_data(user_email=user_email, is_admin=is_user_admin(user_id))
    await message.answer("Введите номер DealReg:")
    await state.set_state(MyDealReg.waiting_for_dealreg_number)


@router.message(MyDealReg.waiting_for_dealreg_number)
async def process_dealreg_number(message: Message, state: FSMContext):
    temp_message = await message.answer("⏳ Собираю информацию, ожидайте... ⏳")
    dealreg_number = message.text.strip()
    state_data = await state.get_data()
    user_email = state_data.get('user_email')
    is_admin = state_data.get('is_admin', False)
    bitrix = BitrixAPI(os.getenv("BITRIX_WEBHOOK"))
    dealreg_data = await bitrix.get_dealreg_by_id(dealreg_number)
    if not dealreg_data or not dealreg_data.get('result'):
        await temp_message.delete()
        await message.answer("DealReg с таким номером не найден. ❌")
        await state.clear()
        return
    dealreg_info = dealreg_data['result'].get('item', {})
    if not is_admin:
        has_access = await check_dealreg_access(user_email, dealreg_info, bitrix)
        if not has_access:
            await temp_message.delete()
            partner_email = await get_partner_email_from_dealreg(dealreg_info, bitrix)
            await message.answer(
                f"❌ У вас нет доступа для просмотра этого DealReg.\n"
                f"👤 Ваш email: {user_email}\n"
                f"📧 Ответственный партнер: {partner_email}\n"
                f"Обратитесь к администратору для получения доступа."
            )
            await state.clear()
            return
    dealreg_id = dealreg_info.get('id')
    dealreg_stage_id = dealreg_info.get('stageId')
    dealreg_previous_stage_id = dealreg_info.get('previousStageId')
    dealreg_company = dealreg_info.get('companyId')
    dealreg_created = dealreg_info.get('createdTime')
    dealreg_modified = dealreg_info.get('updatedTime')
    if dealreg_company:
        company_data = await bitrix.get_company_info(dealreg_company)
        company_name = company_data.get('result', {}).get('TITLE', 'Неизвестно') if company_data else 'Неизвестно'
    else:
        company_name = 'Неизвестно'
    stages = {
        'DT183_37:NEW': 'Начало',
        'DT183_37:PREPARATION': 'Прогрев партнёра',
        'DT183_37:UC_AAYY8N': 'Квалификация HRlink',
        'DT183_37:UC_92D1DY': 'Прогрев HRlink',
        'DT183_37:UC_XFDN2C': 'Назначена встреча',
        'DT183_37:16': 'Встреча не состоялась',
        'DT183_37:UC_GDQZQ3': 'Истекает',
        'DT183_37:UC_7O0GZ6': 'Продлён',
        'DT183_37:FAIL': 'Истёк(проигрыш)',
        'DT183_37:1': 'Подключения не требуется(проигрыш)',
        'DT183_37:UC_ENAKFX': 'Нет планов по переходу(проигрыш)',
        'DT183_37:2': 'Дубль(проигрыш)',
        'DT183_37:3': 'Компания на другом партнёре(проигрыш)',
        'DT183_37:6': 'ИНН и компания не совпадают(проигрыш)',
        'DT183_37:7': 'Квалификация(проигрыш)',
        'DT183_37:10': 'Не целевой(проигрыш)',
        'DT183_37:11': 'Не ЛПР/ГПР(проигрыш)',
        'DT183_37:12': 'Личный интерес(АРХИВНЫЙ)(проигрыш)',
        'DT183_37:13': 'Отложено предложение(проигрыш)',
        'DT183_37:14': 'НДЗ(проигрыш)',
        'DT183_37:18': 'Не продал(проигрыш)',
        'DT183_37:19': 'Выбрали конкурента(проигрыш)',
        'DT183_37:20': 'Клиент(проигрыш)',
        'DT183_37:SUCCESS': 'УСПЕХ'
    }
    stage_name = stages.get(dealreg_stage_id, 'Неизвестно')
    previous_stage_name = stages.get(dealreg_previous_stage_id, 'Неизвестно') if dealreg_previous_stage_id else 'Неизвестно'
    responsible_name = 'Не назначен менеджер'
    responsible_email = 'Неизвестно'
    responsible_telegram = 'Неизвестно'
    responsible_position = 'Неизвестно'
    deal_responsible_for_deal_id = dealreg_info.get('ufCrm27_1731395822')
    if deal_responsible_for_deal_id:
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
    deal_touches_info = []
    deal_id = dealreg_info.get('parentId2')
    if deal_id:
        deal_touches_data = await bitrix.get_deal_touches(deal_id)
        if deal_touches_data and deal_touches_data.get('result'):
            for touch in deal_touches_data['result']:
                touch_info = f"{touch.get('CREATED')}: {touch.get('COMMENT')}"
                touch_info = re.sub(r'<[^>]+>', '', touch_info)
                touch_info = re.sub(r'\[/?[A-Z]+\]', '', touch_info)
                deal_touches_info.append(touch_info)
    try:
        created_date = datetime.fromisoformat(dealreg_created).strftime('%d.%m.%Y %H:%M') if dealreg_created else 'Неизвестно'
        modified_date = datetime.fromisoformat(dealreg_modified).strftime('%d.%m.%Y %H:%M') if dealreg_modified else 'Неизвестно'
    except (TypeError, ValueError) as e:
        logger.error(f"Error parsing dates: {e}")
        created_date = 'Неизвестно'
        modified_date = 'Неизвестно'
    admin_note = "\n👑 <b>Просмотрено администратором</b>\n" if is_admin else ""
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
        f"📞 <b>Telegram:</b> <code>{responsible_telegram}</code>\n"
        "\n"
        f"<b>Дата создания:</b> {created_date}\n"
        f"<b>Дата изменения:</b> {modified_date}\n"
        f"{admin_note}"
        "\n"
    )
    if deal_touches_info:
        dealreg_message += "\n<b>Комментарии в сущности (Сделка):</b>\n" + "\n".join(deal_touches_info[:5])
    else:
        dealreg_message += "\n<b>Комментарии в сущности (Сделка):</b> Нет данных."
    keyboard = None
    if deal_id:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Показать касания с клиентом", callback_data=f"show_touches_{deal_id}")]
        ])
    await temp_message.delete()
    await message.answer(dealreg_message, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    await state.clear()


@router.callback_query(F.data.startswith("show_touches_"))
async def show_client_touches(callback: CallbackQuery, state: FSMContext):
    try:
        deal_id = callback.data.replace("show_touches_", "")
        await callback.answer("Загружаем касания...")
        bitrix = BitrixAPI(os.getenv("BITRIX_WEBHOOK"))
        touches_data = await bitrix.get_deal_client_touches(deal_id)
        if not touches_data or not touches_data.get('result') or not touches_data['result'].get('items'):
            await callback.message.answer("❌ Касания с клиентом не найдены")
            return
        touches = touches_data['result']['items']
        touches_info = []
        for touch in touches:
            touch_text = touch.get('ufCrm45_1663423811', '')
            if not touch_text:
                continue
            touch_text = re.sub(r'<[^>]+>', '', touch_text)
            touch_text = re.sub(r'\[/?[A-Z]+\]', '', touch_text)
            assigned_by_id = touch.get('assignedById')
            user_data = await bitrix.get_user(assigned_by_id)
            responsible_name = "Неизвестно"
            responsible_email = "Неизвестно"
            if user_data and user_data.get('result'):
                user_info = user_data['result'][0]
                responsible_name = f"{user_info.get('NAME', 'Неизвестно')} {user_info.get('LAST_NAME', 'Неизвестно')}"
                responsible_email = user_info.get('EMAIL', 'Неизвестно')
            created_time = touch.get('createdTime', '')
            if created_time:
                try:
                    created_date = datetime.fromisoformat(created_time).strftime('%d.%m.%Y %H:%M')
                    touch_info = (
                        f"📅 <b>{created_date}</b>\n"
                        f"👤 Ответственный: {responsible_name}\n"
                        f"📧 Email: <code>{responsible_email}</code>\n"
                        f"<b>Текст касания:</b>\n{touch_text}\n"
                    )
                except Exception:
                    touch_info = (
                        f"📅 Неизвестная дата\n"
                        f"👤 Ответственный: {responsible_name}\n"
                        f"📧 Email: {responsible_email}\n"
                        f"{touch_text}\n"
                    )
            else:
                touch_info = (
                    f"👤 Ответственный: {responsible_name}\n"
                    f"📧 Email: {responsible_email}\n"
                    f"{touch_text}\n"
                )
            touches_info.append(touch_info)
        if touches_info:
            full_message = "📋 <b>Касания с клиентом:</b>\n\n" + "\n".join(touches_info)
            if len(full_message) > 4096:
                parts = []
                current_part = ""
                for touch in touches_info:
                    if len(current_part) + len(touch) > 4000:
                        parts.append(current_part)
                        current_part = touch
                    else:
                        current_part += touch
                if current_part:
                    parts.append(current_part)
                for i, part in enumerate(parts, 1):
                    part_message = f"📋 <b>Касания с клиентом (часть {i}):</b>\n\n{part}"
                    await callback.message.answer(part_message, parse_mode=ParseMode.HTML)
                    await asyncio.sleep(0.5)
            else:
                await callback.message.answer(full_message, parse_mode=ParseMode.HTML)
        else:
            await callback.message.answer("❌ Нет информации о касаниях")
    except Exception as e:
        logger.error(f"Error showing touches: {e}")
        await callback.message.answer("⚠️ Произошла ошибка при загрузке касаний")


@router.callback_query(F.data == "load_more_touches")
async def load_more_touches(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Функция пагинации в разработке")
