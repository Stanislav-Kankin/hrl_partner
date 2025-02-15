from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.partners import USERS

router = Router()


class AuthStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_last_name = State()
    waiting_for_email = State()
    waiting_for_phone = State()


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Проверяем, авторизован ли пользователь
    if any(user.get("id") == user_id for user in USERS.values()):
        await message.answer(
            "Используйте /dl_partner для подачи заявки на DealReg, "
            "или /my_dl для запроса статуса заявки."
        )
    else:
        await message.answer("Авторизуйтесь, пришлите своё Имя")
        await state.set_state(AuthStates.waiting_for_name)


@router.message(AuthStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Теперь пришлите свою Фамилию")
    await state.set_state(AuthStates.waiting_for_last_name)


@router.message(AuthStates.waiting_for_last_name)
async def process_last_name(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await message.answer("Укажите Вашу рабочую почту")
    await state.set_state(AuthStates.waiting_for_email)


@router.message(AuthStates.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer(
        "Укажите номер сотового телефона в формате 89111234455"
    )
    await state.set_state(AuthStates.waiting_for_phone)


@router.message(AuthStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    user_data = await state.get_data()
    user_id = message.from_user.id

    # Формируем полное имя пользователя
    full_name = f"{user_data['name']} {user_data['last_name']}"

    # Проверяем, есть ли пользователь в списке USERS
    if full_name in USERS:
        user_info = USERS[full_name]

        # Проверяем почту и телефон
        if (user_info["email"] == user_data["email"] and
                user_info["phone_num"] == message.text):
            # Добавляем ID пользователя в данные
            USERS[full_name]['id'] = user_id

            await message.answer("Авторизация успешна!")
            await message.answer(
                "Используйте /dl_partner для подачи заявки на DealReg, "
                "или /my_dl для запроса статуса заявки."
            )
        else:
            await message.answer(
                "Неверная почта или телефон. Авторизация не удалась."
                )
    else:
        await message.answer("Не удалось провести авторизацию.")

    await state.clear()
