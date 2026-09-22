from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from categories import all_parents

SUBCATEGORY_PER_PAGE = 8


def build_parents_keyboard(item_id: int) -> InlineKeyboardMarkup:
    """Список родительских категорий"""
    buttons = [
        [InlineKeyboardButton(
            text=parent,
            callback_data=f"parent:{item_id}:{parent}",
        )] for parent in all_parents()
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def build_subcategories_keyboard(
        item_id: int,
        parent: str,
        subcategories: list[str],
        page: int
    ) -> InlineKeyboardMarkup:
    """Подкатегории выбранного родителя, постранично."""
    start = page * SUBCATEGORY_PER_PAGE
    end = start + SUBCATEGORY_PER_PAGE
    page_subcategories = subcategories[start:end]

    buttons = [
        [InlineKeyboardButton(
            text=subcategory,
            callback_data=f"set_category:{item_id}:{subcategory}",
        )] for subcategory in page_subcategories
    ]

    navigation = []
    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"subcategory_page:{item_id}:{parent}:{page - 1}",
            )
        )

    if end < len(subcategories):
        navigation.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"subcategory_page:{item_id}:{parent}:{page + 1}",
            )
        )

    if navigation:
        buttons.append(navigation)

    buttons.append([
        InlineKeyboardButton(
            text="Своя категория",
            callback_data=f"new_subcategory:{item_id}:{parent}",
        )
    ])
    buttons.append([
        InlineKeyboardButton(
            text="К категориям",
            callback_data=f"edit_item:{item_id}",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def build_cancel_keyboard(item_id: int, parent: str) -> InlineKeyboardMarkup:
    """Выход мз ввода названия своей категории"""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="Отмена",
            callback_data=f"cancel_subcategory:{item_id}:{parent}",
        )
    ]])