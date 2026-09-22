from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from categories import subcategories_of
from keyboards.categories import build_parents_keyboard, build_subcategories_keyboard, build_cancel_keyboard
from deps import db


MAX_CATEGORY_NAME_LENGTH = 20


router = Router()


class NewSubcategory(StatesGroup):
    waiting_name = State()


def available_subcategories(user_id: int, parent: str) -> list[str]:
    """Подкатегории родителя вместе с подкатегориями пользователя"""
    return subcategories_of(parent) + db.get_custom_categories(user_id, parent)


async def show_subcategories(callback: CallbackQuery, item_id: int, parent: str, page: int = 0):
    """Показывает список подкатегорий родителя в текущем сообщении."""
    subcategories = available_subcategories(callback.from_user.id, parent)

    await callback.message.edit_text(
        f"{parent} -> Выберите подкатегорию",
        reply_markup=build_subcategories_keyboard(item_id, parent, subcategories, page),
    )


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

    await callback.message.answer(
        "Выбери товар для изменения категории:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_item:"))
async def edit_item(callback: CallbackQuery):
    item_id = int(callback.data.split(":")[1])

    await callback.message.edit_text(
        "Выбери новую категорию",
        reply_markup=build_parents_keyboard(item_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("subcategory_page:"))
async def subcategory_page(callback: CallbackQuery):
    data = callback.data.split(":")
    item_id, parent, page = int(data[1]), data[2], int(data[3])
    subcategories = available_subcategories(callback.from_user.id, parent)

    await callback.message.edit_reply_markup(
        reply_markup=build_subcategories_keyboard(item_id, parent, subcategories, page)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("parent:"))
async def choose_parent(callback: CallbackQuery):
    data = callback.data.split(":")
    item_id, parent = int(data[1]), data[2]

    await show_subcategories(callback, item_id, parent)
    await callback.answer()


@router.callback_query(F.data.startswith("set_category:"))
async def set_category(callback: CallbackQuery):
    data = callback.data.split(":")
    item_id, category = int(data[1]), data[2]

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

    await callback.message.edit_text(
        f"Готово: {name} теперь в категории {category}",
    )
    await callback.answer()

@router.callback_query(F.data.startswith("new_subcategory:"))
async def new_subcategory(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split(":")
    item_id, parent = int(data[1]), data[2]

    await state.set_state(NewSubcategory.waiting_name)
    await state.update_data(item_id=item_id, parent=parent)

    await callback.message.edit_text(
        f"Введи название новой подкатегории в «{parent}» "
        f"(до {MAX_CATEGORY_NAME_LENGTH} символов, без двоеточий):",
        reply_markup=build_cancel_keyboard(item_id, parent),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_subcategory:"))
async def cancel_new_subcategory(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split(":")
    item_id, parent = int(data[1]), data[2]

    await state.clear()
    await show_subcategories(callback, item_id, parent)
    await callback.answer()

@router.message(NewSubcategory.waiting_name)
async def save_new_subcategory(message: Message, state: FSMContext):
    name = (message.text or "").strip()

    if not name or len(name) > MAX_CATEGORY_NAME_LENGTH or ":" in name:
        await message.answer(
            f"Название не подходит: длина должна быть от 1 до {MAX_CATEGORY_NAME_LENGTH} символов "
            f"и без двоеточий",
        )
        return

    data = await state.get_data()
    item_id, parent = data.get("item_id"), data.get("parent")
    if item_id is None or parent is None:
        await state.clear()
        await message.answer(
            "Потерял, к какому товару это относится. "
            "Начни заново с кнопки «Изменить категорию»",
        )
        return

    if name in available_subcategories(message.from_user.id, parent):
        await message.answer(
            f"Подкатегория «{name}» в «{parent}» уже есть — выбери её из списка",
        )
        return

    await state.clear()

    changed = db.update_item_category(message.from_user.id, item_id, name)
    if not changed:
        await message.answer("Это не твой чек")
        return

    db.save_custom_category(message.from_user.id, parent, name)

    item_name = db.get_item_name(item_id)
    if item_name:
        db.save_user_rule(message.from_user.id, item_name, name)

    await message.answer(
        f"Готово: подкатегория «{name}» создана в «{parent}», "
        f"{item_name} теперь в ней",
    )