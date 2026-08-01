"""Общие объекты проекта"""
from pathlib import Path
from db.sqlite import SQLiteDatabase

BASE_DIR = Path(__file__).resolve().parent

db = SQLiteDatabase(str(BASE_DIR / "bot_test.db"))