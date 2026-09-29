import asyncio
import logging

from maxapi import Bot, Dispatcher

from api_client import backend
from config import MAX_BOT_TOKEN
from handlers import start, callbacks, text_input

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

bot = Bot(token=MAX_BOT_TOKEN)
dp = Dispatcher()

dp.include_routers(
    callbacks.router,
    start.router,
    text_input.router,
)


async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await backend.close()


if __name__ == "__main__":
    asyncio.run(main())