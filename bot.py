import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from config import BOT_TOKEN, PROVERKACHEKA_TOKEN
from database import init_db, save_receipt, get_receipt_items, update_item_category, get_item_name, save_user_rule
from receipts import get_receipts
from qr import read_qr
from categories import all_categories

CATEGORY_PER_PAGE = 4

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


@dp.callback_query(F.data.startswith("category_page:"))
async def category_page(callback: CallbackQuery):
    data = callback.data.split(":")
    item_id = int(data[1])
    page = int(data[2])

    keyboard = build_categories_keyboard(item_id, page)

    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data.startswith("edit_item:"))
async def edit_item(callback: CallbackQuery):
    item_id = int(callback.data.split(":")[1])

    keyboard = build_categories_keyboard(item_id, page=0)

    await callback.message.answer(
        "Выбери новую категорию", reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("set_category:"))
async def set_category(callback: CallbackQuery):
    data = callback.data.split(":")
    item_id = int(data[1])
    category = data[2]

    changed = update_item_category(callback.from_user.id, item_id, category)
    if not changed:
        await callback.answer(
            "Это не твой чек", show_alert=True
        )
        return

    name = get_item_name(item_id)
    if name:
        save_user_rule(callback.from_user.id, name, category)

    await callback.message.answer(
        f"Готово: {name} теперь в категории {category}"
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


def build_categories_keyboard(item_id: int, page: int) -> InlineKeyboardMarkup:
    """Клавиатура категорий для товаров"""
    categories = all_categories()

    start = page * CATEGORY_PER_PAGE
    end = start + CATEGORY_PER_PAGE
    page_categories = categories[start:end]

    buttons = [
        [InlineKeyboardButton(
            text=cat,
            callback_data=f"category_page:{item_id}:{page + 1}",
        )] for cat in page_categories
    ]

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text="⬅️", callback_data=f"category_page:{item_id}:{page - 1}"))
    if end < len(categories):
        nav.append(InlineKeyboardButton(
            text="➡️", callback_data=f"category_page:{item_id}:{page + 1}"))

    if nav:
        buttons.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def main():
    init_db()
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())