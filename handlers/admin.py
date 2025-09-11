from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.partners import USERS, save_users

router = Router()


class AdminStates(StatesGroup):
    waiting_for_user_name = State()
    waiting_for_user_last_name = State()
    waiting_for_user_email = State()
    waiting_for_user_phone = State()
    waiting_for_user_partners = State()
    waiting_for_user_role = State()
    waiting_for_edit_user = State()
    waiting_for_delete_user = State()


# Главное меню админа с инлайн-кнопками
@router.message(Command("admin"))
async def admin_command(message: Message):
    user_id = message.from_user.id

    # Проверяем, является ли пользователь админом
    if any(
        user.get("id") == user_id and user.get(
            "email") == "admin" for user in USERS.values()):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Добавить пользователя 🙋‍♂️ 🙋‍♀️",
                callback_data="add_user")],
            [InlineKeyboardButton(
                text="Добавить наблюдателя 👀",
                callback_data="add_observer")],  # Новая кнопка
            [InlineKeyboardButton(
                text="Удалить пользователя ❌ ",
                callback_data="delete_user")],
            [InlineKeyboardButton(
                text="Список пользователей 🗂️",
                callback_data="list_users")]
        ])

        await message.answer(
            "🚀  Вы вошли как администратор. Выберите действие:",
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
    await callback.answer()


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
    await state.update_data(email=message.text)
    await message.answer(
        "Введите <b><u>рабочий телефон</u></b> нового пользователя:"
        )
    await state.set_state(AdminStates.waiting_for_user_phone)


@router.message(AdminStates.waiting_for_user_phone)
async def process_user_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    user_data = await state.get_data()
    user_role = user_data.get("role", "partner")  # Получаем роль

    if user_role == "observer":
        # Если наблюдатель, пропускаем ввод компаний
        await process_user_partners_observer(message, state)
    else:
        # Если партнёр, спрашиваем компании
        await message.answer("Введите <b><u>список партнеров</u></b> через запятую:")
        await state.set_state(AdminStates.waiting_for_user_partners)


@router.message(AdminStates.waiting_for_user_partners)
async def process_user_partners(message: Message, state: FSMContext):
    user_data = await state.get_data()
    role = user_data.get("role", "partner")  # Получаем роль
    partners = [partner.strip() for partner in message.text.split(",")] if role == "partner" else []  # Наблюдатели не имеют партнёров
    full_name = f"{user_data['name']} {user_data['last_name']}"
    USERS[full_name] = {
        "name": user_data['name'],
        "last_name": user_data['last_name'],
        "email": user_data['email'],
        "phone_num": user_data['phone'],
        "allowed_partners": partners,
        "role": role  # Сохраняем роль
    }
    save_users()  # Сохраняем изменения
    await message.answer(f"Пользователь {full_name} успешно добавлен.")
    await state.clear()


@router.callback_query(F.data == "list_users")
async def list_users_callback(callback: CallbackQuery):
    users_info = []
    for full_name, user_data in USERS.items():
        # Формируем информацию о каждом пользователе
        user_info = (
            f"👤 <b>{full_name}</b>\n"
            f"📞 Телефон: <code>{user_data.get('phone_num', 'Не указан')}</code>\n"
            f"📧 Почта: <code>{user_data.get('email', 'Не указана')}</code>\n"
            f"🔗 Роль: <b><u>{user_data.get('role', 'partner')}</u></b>\n"  # Отображаем роль
        )
        # Если пользователь — партнёр, показываем его партнёров
        if user_data.get("role") == "partner":
            user_info += f"🔗 Доступные партнеры: {', '.join(user_data.get('allowed_partners', []))}\n"
        users_info.append(user_info)

    # Формируем итоговое сообщение
    if users_info:
        response = "📋 <b>Список пользователей:</b>\n\n" + "\n".join(users_info)
    else:
        response = "Пользователи не найдены."

    await callback.message.answer(response, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "delete_user")
async def delete_user_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите имя пользователя для удаления:")
    await state.set_state(AdminStates.waiting_for_delete_user)
    await callback.answer()


@router.message(AdminStates.waiting_for_delete_user)
async def process_delete_user(message: Message, state: FSMContext):
    user_name = message.text

    # Проверяем, существует ли пользователь
    if user_name in USERS:
        del USERS[user_name]
        save_users()
        await message.answer(f"Пользователь {user_name} успешно удален.")
    else:
        await message.answer("Пользователь не найден.")

    await state.clear()


@router.callback_query(F.data == "add_observer")
async def add_observer_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите <b><u>имя</u></b> нового наблюдателя:")
    await state.set_state(AdminStates.waiting_for_user_name)
    await state.update_data(role="observer")  # Сохраняем роль
    await callback.answer()


async def process_user_partners_observer(message: Message, state: FSMContext):
    user_data = await state.get_data()
    full_name = f"{user_data['name']} {user_data['last_name']}"
    USERS[full_name] = {
        "name": user_data['name'],
        "last_name": user_data['last_name'],
        "email": user_data['email'],
        "phone_num": user_data['phone'],
        "allowed_partners": [],  # Пустой список для наблюдателей
        "role": "observer"      # Явно указываем роль
    }
    save_users()
    await message.answer(f"Наблюдатель {full_name} успешно добавлен!")
    await state.clear()
