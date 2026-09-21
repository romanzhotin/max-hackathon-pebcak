import os
from dotenv import load_dotenv

use_dotenv = os.getenv("MANUAL_LAUNCH", "0")

if (use_dotenv == "1"):
    load_dotenv()

MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
if not MAX_BOT_TOKEN:
    raise ValueError(f"Не найден MAX_BOT_TOKEN в переменных окружения. {"Проверьте файл .env" if use_dotenv == "1" else ""}")