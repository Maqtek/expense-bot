"""Общие объекты проекта"""
from pathlib import Path
from db.sqlite import SQLiteDatabase
from config import DB_PATH

BASE_DIR = Path(__file__).resolve().parent

_db_path = Path(DB_PATH)
if not _db_path.is_absolute():
    _db_path = BASE_DIR / _db_path

db = SQLiteDatabase(str(_db_path))