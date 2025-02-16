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
    waiting_for_edit_user = State()
    waiting_for_delete_user = State()


# Главное меню админа с инлайн-кнопками
@router.message(Command("admin"))
async def admin_command(message: Message):
    user_id = message.from_user.id

    # Проверяем, является ли пользователь админом
    if any(user.get("id") == user_id and user.get("email") == "admin" for user in USERS.values()):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Добавить пользователя", callback_data="add_user")],
            [InlineKeyboardButton(
                text="Редактировать пользователя", callback_data="edit_user")],
            [InlineKeyboardButton(
                text="Удалить пользователя", callback_data="delete_user")],
            [InlineKeyboardButton(
                text="Список пользователей", callback_data="list_users")]
        ])
        await message.answer(
            "Вы вошли как администратор. Выберите действие:",
            reply_markup=keyboard)
    else:
        await message.answer("У вас нет прав администратора.")


# Обработка инлайн-кнопок
@router.callback_query(F.data == "add_user")
async def add_user_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите имя нового пользователя:")
    await state.set_state(AdminStates.waiting_for_user_name)
    await callback.answer()


@router.message(AdminStates.waiting_for_user_name)
async def process_user_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите фамилию нового пользователя:")
    await state.set_state(AdminStates.waiting_for_user_last_name)


@router.message(AdminStates.waiting_for_user_last_name)
async def process_user_last_name(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await message.answer("Введите рабочую почту нового пользователя:")
    await state.set_state(AdminStates.waiting_for_user_email)


@router.message(AdminStates.waiting_for_user_email)
async def process_user_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Введите рабочий телефон нового пользователя:")
    await state.set_state(AdminStates.waiting_for_user_phone)


@router.message(AdminStates.waiting_for_user_phone)
async def process_user_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Введите список партнеров через запятую:")
    await state.set_state(AdminStates.waiting_for_user_partners)


@router.message(AdminStates.waiting_for_user_partners)
async def process_user_partners(message: Message, state: FSMContext):
    user_data = await state.get_data()
    partners = [partner.strip() for partner in message.text.split(",")]

    # Создаем нового пользователя
    full_name = f"{user_data['name']} {user_data['last_name']}"
    USERS[full_name] = {
        "name": user_data['name'],
        "last_name": user_data['last_name'],
        "email": user_data['email'],
        "phone_num": user_data['phone'],
        "allowed_partners": partners
    }

    # Сохраняем изменения
    save_users()

    await message.answer(f"Пользователь {full_name} успешно добавлен.")
    await state.clear()


@router.callback_query(F.data == "list_users")
async def list_users_callback(callback: CallbackQuery):
    users_list = "\n".join([f"{user['name']} {user['last_name']}" for user in USERS.values()])
    await callback.message.answer(f"Список пользователей:\n{users_list}")
    await callback.answer()


@router.callback_query(F.data == "edit_user")
async def edit_user_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Введите имя пользователя для редактирования:")
    await state.set_state(AdminStates.waiting_for_edit_user)
    await callback.answer()


@router.message(AdminStates.waiting_for_edit_user)
async def process_edit_user(message: Message, state: FSMContext):
    user_name = message.text

    # Проверяем, существует ли пользователь
    if user_name in USERS:
        await state.update_data(edit_user_name=user_name)
        await message.answer(
            f"Редактирование пользователя {user_name}. Введите новые данные.\n"
            "Введите новое имя:"
        )
        await state.set_state(AdminStates.waiting_for_user_name)
    else:
        await message.answer("Пользователь не найден.")
        await state.clear()


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
