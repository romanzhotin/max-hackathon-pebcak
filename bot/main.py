import asyncio
import logging

from maxapi import Bot, Dispatcher

from config import MAX_BOT_TOKEN
from handlers.start import router as start_router


logging.basicConfig(level=logging.INFO)

bot = Bot(token=MAX_BOT_TOKEN)
dp = Dispatcher()

dp.include_routers(start_router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())