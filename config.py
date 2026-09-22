import os
from dotenv import load_dotenv

load_dotenv()

PROVERKACHEKA_TOKEN = os.getenv("PROVERKACHEKA_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DB_PATH", "bot_test.db")
TELEGRAM_PROXY = os.getenv("TELEGRAM_PROXY") or None
