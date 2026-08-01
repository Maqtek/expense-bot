import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from deps import db
from handlers import receipts, categories


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(receipts.router)
    dp.include_router(categories.router)

    db.init_db()

    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())