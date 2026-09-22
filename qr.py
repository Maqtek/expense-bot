from pyzbar.pyzbar import decode
from PIL import Image


class QRError(Exception):
    """Базовая ошибка чтения QR-кода."""

    user_message = (
        "Не получилось прочитать изображение. "
        "Пришлите фото еще раз или QR-строку текстом"
    )

class ImageOpenError(QRError):
    """Файл не удалось открыть как изображение."""


class QRNotFoundError(QRError):
    """Не удалось найти QR-код на изображении."""

    user_message = (
        "Не удалось распознать QR-код с фото. "
        "Попробуйте снять чётче или пришлите QR-строку текстом"
    )

class QRDecodeError(QRError):
    """QR-код найден, но не получилось получить содержимое."""


def read_qr(image_path: str) -> str:
    """Читает QR-код с картинки.

    Args:
        image_path: Путь к файлу изображения.
    Return:
        QR-строка.
    Raises:
        ImageOpenError: файл отсутствует, поврежден или не является изображением.
        QRNotFoundError: если QR на изображении не найден.
        QRDecodeError: QR-код найден, но не декодируется в UTF-8.
    """
    try:
        with Image.open(image_path) as img:
            codes = decode(img)
    except OSError as e:
        raise ImageOpenError(f"Не удалось открыть изображение {image_path}: {e}") from e

    if not codes:
        raise QRNotFoundError(f"QR-код не найден: {image_path}")

    try:
        return codes[0].data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise QRDecodeError(f"Не получилось декодировать данные из QR-код: {image_path}") from e