import sqlite3
from categories import categorize

DB_PATH = "bot.db"


def get_connection() -> sqlite3.Connection:
    """Открывает соединение с базой данных."""
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Создает таблицу, если их еще нет."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            purchased_at TEXT,
            shop TEXT,
            total REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )    
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL,
            quantity INTEGER,
            sum REAL,
            category TEXT DEFAULT "Без категории",
            FOREIGN KEY (receipt_id) REFERENCES receipts (id)
        )               
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            keyword TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def save_receipt(user_id: int, receipt: dict) -> int:
    """Сохраняет чек в базу данных

    Args:
        user_id: telegram id пользователя
        receipt: словарь из get_receipts: {shop, purchased_at, total, items}
    Return:
        id сохраненного чека
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO receipts (user_id, purchased_at, shop, total) VALUES (?, ?, ?, ?)",
        (user_id, receipt["purchased_at"], receipt["shop"], receipt["total"]),
    )
    receipt_id = cursor.lastrowid

    for item in receipt["items"]:
        category = categorize_for_user(user_id, item["name"])

        cursor.execute(
            "INSERT INTO items (receipt_id, name, price, quantity, sum, category) VALUES (?, ?, ?, ?, ?, ?)",
            (receipt_id, item["name"], item["price"], item["quantity"], item["sum"], category),
        )

    connection.commit()
    connection.close()

    return receipt_id


def get_user_rule(user_id: int, name: str) -> str | None:
    """Ищет личное правило пользователя для товара. None, если нет"""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT category FROM category_rules WHERE user_id = ? AND keyword = ?",
        (user_id, name.lower()),
    )

    row = cursor.fetchone()
    connection.close()

    return row[0] if row else None


def save_user_rule(user_id: int, name: str, category: str) -> None:
    """Сохраняет/обновляет личное правило пользователя"""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM category_rules WHERE user_id = ? AND keyword = ?",
        (user_id, name.lower()),
    )
    cursor.execute(
        "INSERT INTO category_rules (user_id, keyword, category) VALUES (?, ?, ?)",
        (user_id, name.lower(), category),
    )

    connection.commit()
    connection.close()


def categorize_for_user(user_id: int, name: str) -> str:
    """Категоризация с учетом личных правил"""
    rule = get_user_rule(user_id, name)

    if rule is not None:
        return rule
    return categorize(name)


def get_receipt_items(receipt_id: int) -> list[dict]:
    """Возвращает позиции чека из базы"""

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, name, sum, category FROM items WHERE receipt_id = ?",
        (receipt_id,),
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        {"id": r[0],
         "name": r[1],
         "sum": r[2],
         "category": r[3]
         } for r in rows
    ]

if __name__ == "__main__":
    from receipts import get_receipts
    from config import PROVERKACHEKA_TOKEN

    init_db()

    print("до правила:", categorize_for_user(1, "Молочный коктейль Черешня Акция"))
    save_user_rule(1, "Молочный коктейль Черешня Акция", "Напитки")
    print("после правила:", categorize_for_user(1, "Молочный коктейль Черешня Акция"))

