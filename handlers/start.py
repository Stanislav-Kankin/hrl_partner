from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.partners import PARTNERS

router = Router()


class AuthStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()
    waiting_for_phone = State()


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    # Проверяем, авторизован ли пользователь
    if any(user['id'] == user_id for user in PARTNERS["users"].values()):
        await message.answer(
            "Используйте /dl_partner для подачи заявки на DealReg, "
            "или /my_dl для запроса статуса заявки."
        )
    else:
        await message.answer("Авторизуйтесь, пришлите своё Имя Фамилию")
        await state.set_state(AuthStates.waiting_for_name)


@router.message(AuthStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
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

    # По умолчанию новый пользователь получает доступ только к НН
    PARTNERS["users"][str(user_id)] = {
        'id': user_id,
        'name': user_data['name'],
        'email': user_data['email'],
        'phone_num': message.text,
        'allowed_partners': ["НН"]  # По умолчанию только НН
    }

    await message.answer(
        "Используйте /dl_partner для подачи заявки на DealReg, "
        "или /my_dl для запроса статуса заявки."
    )
    await state.clear()
