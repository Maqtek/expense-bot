import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from db.base import Database
from categories import categorize, get_parent_category, DEFAULT_PARENT


class SQLiteDatabase(Database):
    """Реализация базы данных на SQLite."""
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path


    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Соединение с базой данных.

        Коммитит при нормальном выходе из блока, откатывает при исключении.
        Закрывает соединение в любом случае.
        """
        connection = sqlite3.connect(self.db_path)
        try:
            with connection:
                yield connection
        finally:
            connection.close()


    def init_db(self) -> None:
        with self._connect() as connection:
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
                    excluded INTEGER NOT NULL DEFAULT 0,
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

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS custom_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    parent TEXT NOT NULL,
                    name TEXT NOT NULL,
                    UNIQUE(user_id, name)
                )
            """)


    def save_receipt(self, user_id: int, receipt: dict) -> int:
        categorized = [
            (item, self.categorize_for_user(user_id, item["name"]))
            for item in receipt["items"]
        ]

        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                "INSERT INTO receipts (user_id, purchased_at, shop, total) VALUES (?, ?, ?, ?)",
                (user_id, receipt['purchased_at'], receipt['shop'], receipt['total'])
            )
            receipt_id = cursor.lastrowid

            for item, category in categorized:
                cursor.execute(
                    "INSERT INTO items (receipt_id, name, price, quantity, sum, category) VALUES (?, ?, ?, ?, ?, ?)",
                    (receipt_id, item["name"], item["price"], item["quantity"], item["sum"], category)
                )

        return receipt_id


    def get_receipt_items(self, receipt_id: int) -> list[dict]:
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT id, name, sum, category FROM items WHERE receipt_id = ?",
                (receipt_id,)
            )
            rows = cursor.fetchall()

        return [
            {"id": r[0],
             "name": r[1],
             "sum": r[2],
             "category": r[3],
            } for r in rows
        ]


    def get_item_name(self, item_id: int) -> str | None:
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT name FROM items WHERE id = ?",
                (item_id,)
            )
            row = cursor.fetchone()

        return row[0] if row else None


    def update_item_category(self, user_id: int, item_id: int, category: str) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                UPDATE items SET category = ? WHERE id = ?
                AND receipt_id IN (SELECT id FROM receipts WHERE user_id = ?)""",
                (category, item_id, user_id)
            )
            changed: bool = cursor.rowcount > 0

        return changed


    def get_user_rule(self, user_id: int, name: str) -> str | None:
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT category FROM category_rules WHERE user_id = ? AND keyword = ?",
                (user_id, name.lower())
            )
            row = cursor.fetchone()

        return row[0] if row else None


    def save_user_rule(self, user_id: int, name: str, category: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                "DELETE FROM category_rules WHERE user_id = ? AND keyword = ?",
                (user_id, name.lower())
            )
            cursor.execute(
                "INSERT INTO category_rules (user_id, keyword, category) VALUES (?, ?, ?)",
                (user_id, name.lower(), category)
            )


    def categorize_for_user(self, user_id: int, name: str) -> str:
        rule = self.get_user_rule(user_id, name)

        if rule is not None:
            return rule
        return categorize(name)


    def save_custom_category(self, user_id: int, parent: str, name: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                "INSERT OR IGNORE INTO custom_categories (user_id, parent, name) VALUES (?, ?, ?)",
                (user_id, parent, name)
            )


    def get_custom_category_parent(self, user_id: int, name: str) -> str | None:
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT parent from custom_categories WHERE user_id = ? AND name = ?",
                (user_id, name)
            )
            row = cursor.fetchone()

        return row[0] if row else None


    def get_parent_category(self, user_id: int, name: str) -> str:
        parent = get_parent_category(name)
        if parent is not None:
            return parent

        parent = self.get_custom_category_parent(user_id, name)
        if parent is not None:
            return parent

        return DEFAULT_PARENT


    def get_custom_categories(self, user_id: int, parent: str) -> list[str]:
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT name FROM custom_categories WHERE user_id = ? AND parent = ? ORDER BY name",
                (user_id, parent)
            )
            rows = cursor.fetchall()

        return [row[0] for row in rows]


if __name__ == "__main__":
    db = SQLiteDatabase("bot_test.db")
    db.init_db()
    print("До: ", db.categorize_for_user(1, "Молочный коктейль"))
    db.save_user_rule(1, "Молочный коктейль", "Напитки")
    print("После: ", db.categorize_for_user(1, "Молочный коктейль"))
