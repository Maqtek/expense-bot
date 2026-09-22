from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from pathlib import Path

from config import PROVERKACHEKA_TOKEN
from receipts import get_receipts
from qr import read_qr, QRError
from deps import db

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Пришли мне фото чека с QR-кодом или QR-строку текстом"
    )


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    status = await message.answer("Обрабатываю фото...")

    photo = message.photo[-1]
    file_path = f"/tmp/{photo.file_id}.jpg"

    try:
        await bot.download(photo, destination=file_path)
        qr_raw = read_qr(file_path)
    except QRError as e:
        await status.edit_text(e.user_message)
        return
    finally:
        Path(file_path).unlink(missing_ok=True)

    await process_receipt(message, qr_raw)


@router.message(StateFilter(None))
async def handle_text(message: Message):
    qr_raw = message.text.strip()
    if not qr_raw.startswith("t="):
        await message.answer("Пришлите QR-строку (начинается с t=)")
        return

    await process_receipt(message, qr_raw)


async def process_receipt(message: Message, qr_raw: str):
    """Общая обработка чека"""
    try:
        receipt = get_receipts(qr_raw, PROVERKACHEKA_TOKEN)
        receipt_id = db.save_receipt(message.from_user.id, receipt)

        items = db.get_receipt_items(receipt_id)

        text = f"Чек сохранён: {len(items)} позиций в сумме на {receipt['total']:.2f} ₽\n\n"
        for item in items:
            text += f"{item['name']} - {item['sum']:.2f} ₽  [{item['category']}]\n"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Изменить категорию",
                callback_data=f"edit_receipt:{receipt_id}",
            )]
        ])
        await message.answer(text, reply_markup=keyboard)

    except Exception as e:
        await message.answer(f"Не получилось обработать чек: {e}")
