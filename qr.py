from pyzbar.pyzbar import decode
from PIL import Image

def read_qr(image_path: str) -> str:
    """Читает QR-код с картинки

    Args:
        image_path: Путь к файлу изображения
    Return:
        QR-строка или None, если QR не найден
    """
    image = Image.open(image_path)
    codes = decode(image)

    if not codes:
        return None

    return codes[0].data.decode("utf-8")