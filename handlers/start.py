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
            "Добро пожаловать! 🚀\n"
            "<b>Используйте команды ниже для работы в боте:</b>\n"
            "\n"
            "/dl_partner - <u>для подачи заявки на DealReg.</u> 📄\n"
            "/my_dl - <u>для запроса статуса заявки.</u> 💡"
        )
    else:
        await message.answer("Авторизуйтесь, пришлите своё <b>Имя</b> 👤")
        await state.set_state(AuthStates.waiting_for_name)


@router.message(AuthStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Теперь пришлите свою <b>Фамилию</b> 👤")
    await state.set_state(AuthStates.waiting_for_last_name)


@router.message(AuthStates.waiting_for_last_name)
async def process_last_name(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await message.answer("Укажите Вашу <b>рабочую почту</b> 📧")
    await state.set_state(AuthStates.waiting_for_email)


@router.message(AuthStates.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer(
        "Укажите <b>номер сотового телефона</b>"
        " <u>в формате 89111234455</u> 📞"
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

            await message.answer("✅<b>Авторизация успешна!</b>✅")
            await message.answer(
                "/dl_partner - <u>для подачи заявки на DealReg</u> 📄 "
                "/my_dl для - <u>запроса статуса заявки.</u> 💡"
            )
        else:
            await message.answer(
                "⚠️<b>Неверная почта или телефон. Авторизация не удалась.</b>⚠️"
                )
    else:
        await message.answer("⚠️<b>Не удалось провести авторизацию.</b>⚠️")

    await state.clear()
