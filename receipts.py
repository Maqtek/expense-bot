from config import PROVERKACHEKA_TOKEN
import requests
from datetime import datetime

API_URL = "https://proverkacheka.com/api/v1/check/get"

def get_receipts(qr_raw: str, token: str) -> dict:
    """Получает позиции чека по QR-строке через сайт proverckacheka.com.

    Args:
        qr_raw: строка QR-кода
        token: список позиций
    Return:
        Список позиций
    """
    response = requests.post(
        API_URL,
        data = {"token" : token, "qrraw" : qr_raw },
        timeout = 30
    )
    response.raise_for_status()
    payload = response.json()

    receipt = payload["data"]["json"]

    raw_date = receipt.get("dateTime")
    purchased_at = datetime.fromisoformat(raw_date).strftime("%Y-%m-%d %H:%M")

    items = []
    for item in receipt["items"]:
        items.append({
            "name": item["name"],
            "price": item["price"] / 100,
            "quantity": item["quantity"],
            "sum": item["sum"] / 100,
        })

    return {
        "shop": receipt.get("user"),
        "purchased_at": purchased_at,
        "total": receipt.get("totalSum", 0) / 100,
        "items": items,
    }

if __name__ == "__main__":
    result = get_receipts("t=20260717T2130&s=1045.00&fn=7380440903306678&i=165583&fp=1923294927&n=1", PROVERKACHEKA_TOKEN)

