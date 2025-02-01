from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler, setup_application
)
from aiohttp import web
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


# Обработчик вебхука
async def handle_webhook(request: web.Request):
    try:
        data = await request.json()  # Получаем данные от Bitrix24
        logging.info(f"Received webhook data: {data}")

        # Пример обработки данных
        if data.get("event") == "ONCRMDEALUPDATE":
            deal_id = data.get("data", {}).get("FIELDS", {}).get("ID")
            if deal_id:
                await bot.send_message(
                    chat_id=os.getenv("ADMIN_CHAT_ID"),  # Замените на ID чата
                    text=f"Сделка {deal_id} была обновлена."
                )

        return web.Response(status=200)
    except Exception as e:
        logging.error(f"Error handling webhook: {e}")
        return web.Response(status=500)


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
    app.router.add_post("/webhook", handle_webhook)
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
