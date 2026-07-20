import sqlite3

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
            purchased_date TEXT,
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
        cursor.execute(
            "INSERT INTO items (receipt_id, name, price, quantity, sum) VALUES (?, ?, ?, ?, ?)",
            (receipt_id, item["name"], item["price"], item["quantity"], item["sum"]),
        )

    connection.commit()
    connection.close()

    return receipt_id

if __name__ == "__main__":
    from receipts import get_receipts
    from config import PROVERKACHEKA_TOKEN

    init_db()

    qr = "t=20260717T2130&s=1045.00&fn=7380440903306678&i=165583&fp=1923294927&n=1"
    receipt = get_receipts(qr, PROVERKACHEKA_TOKEN)

    receipt_id = save_receipt(user_id=1, receipt=receipt)
    print(f'Чек сохранен, id = {receipt_id}')

