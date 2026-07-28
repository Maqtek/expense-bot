import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from config import BOT_TOKEN, PROVERKACHEKA_TOKEN
from database import init_db, save_receipt
from receipts import get_receipts

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Скоро научусь принимать чеки"
    )

@dp.message()
async def handle_text(message: Message):
    qr_raw = message.text.strip()

    if not qr_raw.startswith("t="):
        await message.answer(
            "Пришли мне QR-строку (начинается с t=)"
        )

        return

    await message.answer("Обрабатываю чек...")

    try:
        receipt = get_receipts(qr_raw, PROVERKACHEKA_TOKEN)
        receipt_id = save_receipt(user_id=message.from_user.id, receipt=receipt)

        items = receipt["items"]
        text = f"Чек сохранен: {len(items)} позиций в сумме на {receipt['total']:.2f} ₽\n\n"
        for it in items:
            text += f"{it["name"]} - {it["sum"]:.2f} ₽\n"

        await message.answer(text)

    except Exception as e:
        await message.answer(
            f"Не получилось обработать чек: {e}"
        )


async def main():
    init_db()
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())