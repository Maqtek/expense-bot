from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.categories import build_categories_keyboard
from deps import db

router = Router()


@router.callback_query(F.data.startswith("edit_receipt:"))
async def edit_receipt(callback: CallbackQuery):
    receipt_id = int(callback.data.split(":")[1])
    items = db.get_receipt_items(receipt_id)

    buttons = [
        [InlineKeyboardButton(
            text=item["name"],
            callback_data=f"edit_item:{item['id']}",
        )] for item in items
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer(
        "Выбери товар для изменения категории:",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_item:"))
async def edit_item(callback: CallbackQuery):
    item_id = int(callback.data.split(":")[1])
    keyboard = build_categories_keyboard(item_id, page=0)

    await callback.message.answer(
        "Выбери новую категорию",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category_page:"))
async def category_page(callback: CallbackQuery):
    data = callback.data.split(":")
    item_id, page = int(data[1]), int(data[2])
    keyboard = build_categories_keyboard(item_id, page)

    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("set_category:"))
async def set_category(callback: CallbackQuery):
    data = callback.data.split(":")
    item_id = int(data[1])
    category = data[2]

    changed = db.update_item_category(callback.from_user.id, item_id, category)
    if not changed:
        await callback.answer(
            "Это не твой чек",
            show_alert=True
        )
        return

    name = db.get_item_name(item_id)
    if name:
        db.save_user_rule(callback.from_user.id, name, category)

    await callback.message.answer(
        f"Готово: {name} теперь в категории {category}",
    )
    await callback.answer()

