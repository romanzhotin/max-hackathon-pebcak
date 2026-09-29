import os
from dotenv import load_dotenv

use_dotenv = os.getenv("MANUAL_LAUNCH", "0")

if use_dotenv == "1":
    load_dotenv()

MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
if not MAX_BOT_TOKEN:
    raise ValueError("Не найден MAX_BOT_TOKEN в переменных окружения.")

API_BASE_URL = os.getenv("API_BASE_URL", "https://maxhack.livvyy.ru")
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "20"))