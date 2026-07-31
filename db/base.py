from abc import ABC, abstractmethod


class Database(ABC):
    """Контракт для любой базы данных.
    Описывает, что должна уметь база данных.
    """

    @abstractmethod
    def init_db(self) -> None:
        """Создает таблицы, если их нет."""

    @abstractmethod
    def save_receipt(self, user_id: int, receipt: dict) -> int:
        """Сохраняет чек в базу данных.

        Args:
            user_id: telegram id пользователя
            receipt: словарь из get_receipts: {shop, purchased_at, total, items}
        Return:
            id сохраненного чека
        """

    @abstractmethod
    def get_receipt_items(self, receipt_id: int) -> list[dict]:
        """Возвращает позиции чека из базы."""

    @abstractmethod
    def get_item_name(self, item_id: int) -> str | None:
        """Возвращает название товара по его id."""

    @abstractmethod
    def update_item_category(self, user_id: int, item_id: int, category: str) -> bool:
        """Меняет категорию товара, только если товар принадлежит пользователю.

        Return:
            True, если изменено, в противном случае False
        """

    @abstractmethod
    def get_user_rule(self, user_id: int, name: str) -> str | None:
        """Ищет личное правило пользователя для товара."""

    @abstractmethod
    def save_user_rule(self, user_id: int, name: str, category: str) -> None:
        """Сохраняет/обновляет личное правило пользователя."""

    @abstractmethod
    def categorize_for_user(self, user_id: int, name: str) -> str:
        """Категоризация с учетом личных правил, при этом личное правило имеет высший приоритет."""