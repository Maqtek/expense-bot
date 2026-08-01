from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import CATEGORY_PER_PAGE
from categories import all_categories

CATEGORY_PER_PAGE = 8


def build_categories_keyboard(item_id: int, page: int) -> InlineKeyboardMarkup:
    """Клавиатура категорий для товара, одна страница"""
    categories = all_categories()

    start = page * CATEGORY_PER_PAGE
    end = start + CATEGORY_PER_PAGE
    page_categories = categories[start:end]

    buttons = [
        [InlineKeyboardButton(
            text=cat,
            callback_data=f"set_category:{item_id}:{cat}"
        )] for cat in page_categories
    ]

    navigation = []
    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"category_page:{item_id}:{page - 1}"
            )
        )
    if end < len(categories):
        navigation.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"category_page:{item_id}:{page + 1}"
            )
        )

    if navigation:
        buttons.append(navigation)

    return InlineKeyboardMarkup(inline_keyboard=buttons)
