from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.partners import USERS, save_users
import re
import logging

router = Router()
logger = logging.getLogger(__name__)


class AdminStates(StatesGroup):
    # Состояния для создания пользователя
    waiting_for_user_name = State()
    waiting_for_user_last_name = State()
    waiting_for_user_email = State()
    waiting_for_user_phone = State()
    waiting_for_user_partners = State()
    waiting_for_user_role = State()

    # Состояния для редактирования пользователя
    waiting_for_edit_name = State()
    waiting_for_edit_last_name = State()
    waiting_for_edit_email = State()
    waiting_for_edit_phone = State()
    waiting_for_edit_role = State()
    waiting_for_edit_partners = State()

    waiting_for_delete_user = State()
    waiting_for_search_query = State()
    waiting_for_change_role = State()


# Логирование действий админа
def log_admin_action(user_id: int, action: str, details: str = ""):
    logger.info(
        f"Admin {user_id} performed action: {action}. Details: {details}")


# Проверка корректности email
def is_valid_email(email: str) -> bool:
    return bool(
        re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))


# Проверка корректности телефона
def is_valid_phone(phone: str) -> bool:
    return bool(re.match(r'^\+?[0-9\s\-()]{10,}$', phone))


# Главное меню админа с инлайн-кнопками
@router.message(Command("admin"))
async def admin_command(message: Message):
    user_id = message.from_user.id
    if any(
        user.get(
            "id") == user_id and user.get(
                "email") == "admin" for user in USERS.values()):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="👥 Добавить пользователя",
                callback_data="add_user")],
            [InlineKeyboardButton(
                text="👀 Добавить наблюдателя",
                callback_data="add_observer")],
            [InlineKeyboardButton(
                text="🔍 Поиск пользователя",
                callback_data="search_user")],
            [InlineKeyboardButton(
                text="📋 Список пользователей",
                callback_data="list_users")],
        ])
        await message.answer(
            "🚀 Вы вошли как администратор. Выберите действие:",
            reply_markup=keyboard)
    else:
        await message.answer("У вас нет прав администратора.")


# Обработка инлайн-кнопок
@router.callback_query(F.data == "add_user")
async def add_user_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Введите <b><u>имя</u></b> нового пользователя:"
        )
    await state.set_state(AdminStates.waiting_for_user_name)
    await state.update_data(role="partner")
    await callback.answer()


@router.callback_query(F.data == "add_observer")
async def add_observer_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Введите <b><u>имя</u></b> нового наблюдателя:"
        )
    await state.set_state(AdminStates.waiting_for_user_name)
    await state.update_data(role="observer")
    await callback.answer()


# Обработчики для создания пользователя
@router.message(AdminStates.waiting_for_user_name)
async def process_user_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите <b><u>фамилию</u></b> нового пользователя:")
    await state.set_state(AdminStates.waiting_for_user_last_name)


@router.message(AdminStates.waiting_for_user_last_name)
async def process_user_last_name(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await message.answer(
        "Введите <b><u>рабочую почту</u></b> нового пользователя:"
        )
    await state.set_state(AdminStates.waiting_for_user_email)


@router.message(AdminStates.waiting_for_user_email)
async def process_user_email(message: Message, state: FSMContext):
    email = message.text.strip()
    if not is_valid_email(email):
        await message.answer(
            "❌ Некорректный формат email. Попробуйте ещё раз:")
        return
    await state.update_data(email=email)
    await message.answer(
        "Введите <b><u>рабочий телефон</u></b> нового пользователя:")
    await state.set_state(AdminStates.waiting_for_user_phone)


@router.message(AdminStates.waiting_for_user_phone)
async def process_user_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not is_valid_phone(phone):
        await message.answer(
            "❌ Некорректный формат телефона. Попробуйте ещё раз:")
        return
    await state.update_data(phone=phone)
    user_data = await state.get_data()
    user_role = user_data.get("role", "partner")

    if user_role == "observer":
        await process_user_partners_observer(message, state)
    else:
        await message.answer(
            "Введите <b><u>список партнеров</u></b> через запятую:")
        await state.set_state(AdminStates.waiting_for_user_partners)


@router.message(AdminStates.waiting_for_user_partners)
async def process_user_partners(message: Message, state: FSMContext):
    user_data = await state.get_data()
    role = user_data.get("role", "partner")
    partners = [
        partner.strip() for partner in message.text.split(
            ","
            )] if role == "partner" else []
    full_name = f"{user_data['name']} {user_data['last_name']}"
    USERS[full_name] = {
        "name": user_data['name'],
        "last_name": user_data['last_name'],
        "email": user_data['email'],
        "phone_num": user_data['phone'],
        "allowed_partners": partners,
        "role": role
    }
    save_users()
    log_admin_action(
        message.from_user.id,
        "add_user",
        f"Added user: {full_name}")
    await message.answer(f"✅ Пользователь {full_name} успешно добавлен.")
    await state.clear()


async def process_user_partners_observer(message: Message, state: FSMContext):
    user_data = await state.get_data()
    full_name = f"{user_data['name']} {user_data['last_name']}"
    USERS[full_name] = {
        "name": user_data['name'],
        "last_name": user_data['last_name'],
        "email": user_data['email'],
        "phone_num": user_data['phone'],
        "allowed_partners": [],
        "role": "observer"
    }
    save_users()
    log_admin_action(
        message.from_user.id,
        "add_observer",
        f"Added observer: {full_name}")
    await message.answer(f"✅ Наблюдатель {full_name} успешно добавлен!")
    await state.clear()


@router.callback_query(F.data == "list_users")
async def list_users_callback(callback: CallbackQuery):
    if not USERS:
        await callback.message.answer("📋 Список пользователей пуст.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{name}",
            callback_data=f"user_info_{name}")]
        for name in USERS.keys()
    ])
    await callback.message.answer(
        "📋 <b>Список пользователей:</b>\nВыберите пользователя для просмотра:",
        reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("user_info_"))
async def show_user_info(callback: CallbackQuery):
    user_name = callback.data.replace("user_info_", "")
    if user_name not in USERS:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    user_data = USERS[user_name]
    user_info = (
        f"👤 <b>{user_name}</b>\n"
        f"📞 Телефон: <code>{user_data.get('phone_num', 'Не указан')}</code>\n"
        f"📧 Почта: <code>{user_data.get('email', 'Не указана')}</code>\n"
        f"🔗 Роль: <b><u>{user_data.get('role', 'partner')}</u></b>\n"
    )
    if user_data.get("role") == "partner":
        user_info += f"🔗 Доступные партнеры: {
            ', '.join(user_data.get('allowed_partners', []))}\n"

    action_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📝 Редактировать",
            callback_data=f"edit_user_{user_name}")],
        [InlineKeyboardButton(
            text="🗑️ Удалить",
            callback_data=f"delete_user_{user_name}")],
        [InlineKeyboardButton(
            text="🔄 Сменить роль",
            callback_data=f"change_role_{user_name}")],
        [InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="list_users")],
    ])

    await callback.message.edit_text(
        f"📋 <b>Информация о пользователе:</b>\n\n{user_info}",
        reply_markup=action_keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_user_"))
async def edit_user_callback(callback: CallbackQuery, state: FSMContext):
    user_name = callback.data.replace("edit_user_", "")
    if user_name not in USERS:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return
    await state.update_data(editing_user=user_name)
    user_data = USERS[user_name]
    # Добавляем проверку на наличие ключа 'role'
    role = user_data.get('role', 'partner')  # Значение по умолчанию: 'partner'
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Далее", callback_data="edit_skip_name")]
    ])
    await callback.message.answer(
        f"📝 <b>Редактирование пользователя {user_name}</b>\n\n"
        f"📌 Текущие данные:\n"
        f"👤 Имя: {user_data['name']}\n"
        f"👤 Фамилия: {user_data['last_name']}\n"
        f"📧 Email: {user_data['email']}\n"
        f"📞 Телефон: {user_data['phone_num']}\n"
        f"🔗 Роль: {role}\n"  # Используем переменную role
        f"🔗 Партнеры: {', '.join(user_data.get('allowed_partners', []))}\n\n"
        f"Введите <b>новое имя</b> или нажмите ➡️ Далее, чтобы оставить без изменений:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_edit_name)


@router.callback_query(F.data == "edit_skip_name")
async def edit_skip_name(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    user_name = state_data.get("editing_user")
    if user_name not in USERS:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    user_data = USERS[user_name]
    await state.update_data(new_name=user_data["name"])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="➡️ Далее",
            callback_data="edit_skip_last_name")]
    ])

    await callback.message.edit_text(
        f"Введите <b>новую фамилию</b> или нажмите ➡️ Далее, чтобы оставить без изменений:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_edit_last_name)


@router.message(AdminStates.waiting_for_edit_name)
async def process_edit_name(message: Message, state: FSMContext):
    state_data = await state.get_data()
    user_name = state_data.get("editing_user")
    if user_name not in USERS:
        await message.answer("❌ Пользователь не найден.")
        await state.clear()
        return

    new_name = message.text.strip()
    if new_name:
        await state.update_data(new_name=new_name)
    else:
        user_data = USERS[user_name]
        await state.update_data(new_name=user_data["name"])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="➡️ Далее",
            callback_data="edit_skip_last_name")]
    ])

    await message.answer(
        "Введите <b>новую фамилию</b> или нажмите ➡️ Далее, чтобы оставить без изменений:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_edit_last_name)


@router.callback_query(F.data == "edit_skip_last_name")
async def edit_skip_last_name(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    user_name = state_data.get("editing_user")
    if user_name not in USERS:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    user_data = USERS[user_name]
    await state.update_data(new_last_name=user_data["last_name"])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Далее", callback_data="edit_skip_email")]
    ])

    await callback.message.edit_text(
        f"Введите <b>новый email</b> или нажмите ➡️ Далее, чтобы оставить без изменений:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_edit_email)


@router.message(AdminStates.waiting_for_edit_last_name)
async def process_edit_last_name(message: Message, state: FSMContext):
    state_data = await state.get_data()
    user_name = state_data.get("editing_user")
    if user_name not in USERS:
        await message.answer("❌ Пользователь не найден.")
        await state.clear()
        return

    new_last_name = message.text.strip()
    if new_last_name:
        await state.update_data(new_last_name=new_last_name)
    else:
        user_data = USERS[user_name]
        await state.update_data(new_last_name=user_data["last_name"])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Далее", callback_data="edit_skip_email")]
    ])

    await message.answer(
        "Введите <b>новый email</b> или нажмите ➡️ Далее, чтобы оставить без изменений:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_edit_email)


@router.callback_query(F.data == "edit_skip_email")
async def edit_skip_email(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    user_name = state_data.get("editing_user")
    if user_name not in USERS:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    user_data = USERS[user_name]
    await state.update_data(new_email=user_data["email"])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="➡️ Далее",
            callback_data="edit_skip_phone")]
    ])

    await callback.message.edit_text(
        f"Введите <b>новый телефон</b> или нажмите ➡️ Далее, чтобы оставить без изменений:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_edit_phone)


@router.message(AdminStates.waiting_for_edit_email)
async def process_edit_email(message: Message, state: FSMContext):
    state_data = await state.get_data()
    user_name = state_data.get("editing_user")
    if user_name not in USERS:
        await message.answer("❌ Пользователь не найден.")
        await state.clear()
        return

    new_email = message.text.strip()
    if new_email and not is_valid_email(new_email):
        await message.answer(
            "❌ Некорректный формат email. Попробуйте ещё раз:")
        return

    if new_email:
        await state.update_data(new_email=new_email)
    else:
        user_data = USERS[user_name]
        await state.update_data(new_email=user_data["email"])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Далее", callback_data="edit_skip_phone")]
    ])

    await message.answer(
        "Введите <b>новый телефон</b> или нажмите ➡️ Далее, чтобы оставить без изменений:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_edit_phone)


@router.callback_query(F.data == "edit_skip_phone")
async def edit_skip_phone(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    user_name = state_data.get("editing_user")
    if user_name not in USERS:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    user_data = USERS[user_name]
    await state.update_data(new_phone=user_data["phone_num"])

    # Спрашиваем роль пользователя
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="👥 Партнёр",
            callback_data="edit_set_role_partner")],
        [InlineKeyboardButton(
            text="👀 Наблюдатель",
            callback_data="edit_set_role_observer")],
    ])

    await callback.message.edit_text(
        "Выберите роль пользователя:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_edit_role)
    await callback.answer()


@router.message(AdminStates.waiting_for_edit_phone)
async def process_edit_phone(message: Message, state: FSMContext):
    state_data = await state.get_data()
    user_name = state_data.get("editing_user")
    if user_name not in USERS:
        await message.answer("❌ Пользователь не найден.")
        await state.clear()
        return

    new_phone = message.text.strip()
    if new_phone and not is_valid_phone(new_phone):
        await message.answer(
            "❌ Некорректный формат телефона. Попробуйте ещё раз:")
        return

    if new_phone:
        await state.update_data(new_phone=new_phone)
    else:
        user_data = USERS[user_name]
        await state.update_data(new_phone=user_data["phone_num"])

    # Спрашиваем роль пользователя
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="👥 Партнёр",
            callback_data="edit_set_role_partner")],
        [InlineKeyboardButton(
            text="👀 Наблюдатель",
            callback_data="edit_set_role_observer")],
    ])

    await message.answer(
        "Выберите роль пользователя:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_edit_role)


@router.callback_query(F.data.startswith("edit_set_role_"))
async def process_edit_user_role(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    user_name = state_data.get("editing_user")
    if user_name not in USERS:
        await callback.answer(
            "Пользователь не найден.", show_alert=True)
        return

    role = "partner" if callback.data == "edit_set_role_partner" else "observer"
    await state.update_data(new_role=role)

    if role == "observer":
        # Если роль "наблюдатель", завершаем редактирование
        await save_edit_user(callback.message, state)
    else:
        # Если роль "партнёр", спрашиваем список партнёров
        await callback.message.answer(
            "Введите <b>список партнёров</b> через запятую:")
        await state.set_state(AdminStates.waiting_for_edit_partners)

    await callback.answer()


@router.message(AdminStates.waiting_for_edit_partners)
async def process_edit_partners(message: Message, state: FSMContext):
    await save_edit_user(message, state)


async def save_edit_user(message: Message, state: FSMContext):
    state_data = await state.get_data()
    user_name = state_data.get("editing_user")
    if user_name not in USERS:
        await message.answer("❌ Пользователь не найден.")
        await state.clear()
        return
    updated_data = await state.get_data()
    old_user_data = USERS[user_name]
    # Проверяем наличие ключа 'role' в old_user_data
    old_role = old_user_data.get("role", "partner")  # Значение по умолчанию: 'partner'
    # Формируем новое имя пользователя
    new_full_name = f"{updated_data.get('new_name', old_user_data['name'])} {updated_data.get('new_last_name', old_user_data['last_name'])}"
    # Если имя изменилось, обновляем ключ в словаре
    if new_full_name != user_name:
        USERS[new_full_name] = USERS.pop(user_name)
    # Обновляем данные пользователя
    USERS[new_full_name].update({
        "name": updated_data.get("new_name", old_user_data["name"]),
        "last_name": updated_data.get("new_last_name", old_user_data["last_name"]),
        "email": updated_data.get("new_email", old_user_data["email"]),
        "phone_num": updated_data.get("new_phone", old_user_data["phone_num"]),
        "role": updated_data.get("new_role", old_role),  # Используем old_role
    })
    # Если роль "партнёр", обновляем список партнёров
    current_role = updated_data.get("new_role", old_role)
    if current_role == "partner":
        if state_data.get("waiting_for_edit_partners"):
            partners = [partner.strip() for partner in message.text.split(",")]
            USERS[new_full_name]["allowed_partners"] = partners
        else:
            USERS[new_full_name]["allowed_partners"] = old_user_data.get("allowed_partners", [])
    else:
        USERS[new_full_name]["allowed_partners"] = []
    save_users()
    log_admin_action(message.from_user.id, "edit_user", f"Edited user: {new_full_name}")
    await message.answer(f"✅ Пользователь {new_full_name} успешно отредактирован!")
    await state.clear()


@router.callback_query(F.data == "search_user")
async def search_user_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔍 Введите имя, email или телефон для поиска:")
    await state.set_state(AdminStates.waiting_for_search_query)
    await callback.answer()

@router.message(AdminStates.waiting_for_search_query)
async def process_search_query(message: Message, state: FSMContext):
    query = message.text.strip().lower()
    found_users = []

    for full_name, user_data in USERS.items():
        if (query in full_name.lower() or
            query in user_data.get('email', '').lower() or
            query in user_data.get('phone_num', '').lower()):
            found_users.append((full_name, user_data))

    if found_users:
        for full_name, user_data in found_users:
            user_info = (
                f"👤 <b>{full_name}</b>\n"
                f"📞 Телефон: <code>{user_data.get(
                    'phone_num', 'Не указан')}</code>\n"
                f"📧 Почта: <code>{user_data.get(
                    'email', 'Не указана')}</code>\n"
                f"🔗 Роль: <b><u>{user_data.get(
                    'role', 'partner')}</u></b>\n"
            )
            if user_data.get("role") == "partner":
                user_info += f"🔗 Доступные партнеры: {', '.join(user_data.get('allowed_partners', []))}\n"

            # Кнопки для управления пользователем - для КАЖДОГО найденного пользователя
            action_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 Редактировать",
                        callback_data=f"edit_user_{full_name}"),
                    InlineKeyboardButton(
                        text="🗑️ Удалить",
                        callback_data=f"delete_user_{full_name}")
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 Сменить роль",
                        callback_data=f"change_role_{full_name}"),
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="list_users")
                ]
            ])

            await message.answer(
                f"🔍 <b>Результат поиска:</b>\n\n{user_info}",
                reply_markup=action_keyboard,
                parse_mode="HTML"
            )
    else:
        await message.answer(
            f"🔍 Пользователи по запросу '{query}' не найдены.")

    await state.clear()


@router.callback_query(F.data.startswith("delete_user_"))
async def delete_user_callback(callback: CallbackQuery):
    user_name = callback.data.replace("delete_user_", "")
    if user_name not in USERS:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data=f"confirm_delete_{user_name}")],
        [InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"user_info_{user_name}")],
    ])
    await callback.message.edit_text(
        f"⚠️ Вы уверены, что хотите удалить пользователя <b>{user_name}</b>?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_user(callback: CallbackQuery):
    user_name = callback.data.replace("confirm_delete_", "")
    if user_name in USERS:
        del USERS[user_name]
        save_users()
        log_admin_action(
            callback.from_user.id, "delete_user", f"Deleted user: {user_name}")
        await callback.message.edit_text(
            f"✅ Пользователь {user_name} успешно удален.")
    else:
        await callback.message.edit_text(
            "❌ Пользователь не найден.")
    await callback.answer()


@router.callback_query(F.data.startswith("user_info_"))
async def show_user_info_from_search(callback: CallbackQuery):
    user_name = callback.data.replace("user_info_", "")
    if user_name not in USERS:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    user_data = USERS[user_name]
    user_info = (
        f"👤 <b>{user_name}</b>\n"
        f"📞 Телефон: <code>{user_data.get('phone_num', 'Не указан')}</code>\n"
        f"📧 Почта: <code>{user_data.get('email', 'Не указана')}</code>\n"
        f"🔗 Роль: <b><u>{user_data.get('role', 'partner')}</u></b>\n"
    )
    if user_data.get("role") == "partner":
        user_info += f"🔗 Доступные партнеры: {
            ', '.join(user_data.get('allowed_partners', []))}\n"

    action_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📝 Редактировать",
            callback_data=f"edit_user_{user_name}")],
        [InlineKeyboardButton(
            text="🗑️ Удалить",
            callback_data=f"delete_user_{user_name}")],
        [InlineKeyboardButton(
            text="🔄 Сменить роль",
            callback_data=f"change_role_{user_name}")],
        [InlineKeyboardButton(
            text="🔙 Назад к поиску",
            callback_data="search_user")],
    ])

    await callback.message.edit_text(
        f"📋 <b>Информация о пользователе:</b>\n\n{user_info}",
        reply_markup=action_keyboard,
        parse_mode="HTML"
    )
    await callback.answer()
