from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler, setup_application
    )
from aiohttp import web
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


# Обработчик вебхука
@dp.message_handler(content_types=['text'])
async def handle_webhook(message: types.Message):
    # Проверяем, что сообщение пришло от Bitrix24
    if message.from_user.is_bot:
        return

    # Извлекаем данные из сообщения
    deal_id = message.text.split('-')[1].strip()
    user_id = message.from_user.id

    # Отправляем сообщение пользователю
    await bot.send_message(
        user_id,
        "Спасибо за ваш запрос! Мы проверим список клиентов "
        "и свяжемся с вами по результатам.\n"
        f"Номер запроса - {deal_id}\n\nКоманда HRlink")


# Запуск вебхука
async def on_startup(dp):
    await bot.set_webhook(os.getenv("WEBHOOK_URL"))


async def on_shutdown(dp):
    logging.warning('Shutting down..')
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()


if __name__ == '__main__':
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
