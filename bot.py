import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from config import BOT_TOKEN, PROVERKACHEKA_TOKEN
from database import init_db, save_receipt, get_receipt_items
from receipts import get_receipts
from qr import read_qr

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Пришли мне фото чека с QR-кодом или QR-строку текстом"
    )


@dp.callback_query(F.data.startswith("edit_receipt:"))
async def edit_receipt(callback: CallbackQuery):
    receipt_id = int(callback.data.split(":")[1])

    items = get_receipt_items(receipt_id)

    buttons = [
        [InlineKeyboardButton(
            text=f"{it['name']}",
            callback_data=f"edit_item:{it['id']}",
        )] for it in items
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer(
        "Выбери товар для изменения категории: ", reply_markup=keyboard
    )
    await callback.answer()


@dp.message(F.photo)
async def handle_photo(message: Message):
    await message.answer(
        "Обрабатываю фото..."
    )

    photo = message.photo[-1]

    file_path = (f"/tmp/{photo.file_id}.jpg")
    await bot.download(photo, destination=file_path)

    qr_raw = read_qr(file_path)
    if qr_raw is None:
        await message.answer(
            "Не удалось распознать QR-код с фото."
            "Попробуйте снять чётче при хорошем свете или пришлите QR-строку текстом"
        )
        return

    await process_receipt(message, qr_raw)

@dp.message()
async def handle_text(message: Message):
    qr_raw = message.text.strip()

    if not qr_raw.startswith("t="):
        await message.answer(
            "Пришли QR-строку (начинается с t=)"
        )
        return

    await process_receipt(message, qr_raw)


async def process_receipt(message: Message, qr_raw: str):
    """Общая обработка чека"""
    try:
        receipt = get_receipts(qr_raw, PROVERKACHEKA_TOKEN)
        receipt_id = save_receipt(user_id=message.from_user.id, receipt=receipt)

        items = get_receipt_items(receipt_id)

        text = f"Чек сохранен: {len(items)} позиций в сумме на {receipt['total']:.2f} ₽\n\n"
        for it in items:
            text += f"{it['name']} - {it['sum']:.2f} ₽  [{it['category']}]\n"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Изменить категорию",
                callback_data=f"edit_receipt:{receipt_id}",
            )]
        ])

        await message.answer(text, reply_markup=keyboard)

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