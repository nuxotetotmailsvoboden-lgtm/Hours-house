import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")  # например, sqlite+aiosqlite:///./db.sqlite3
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
