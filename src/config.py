import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
# Webhook and Telegram configurations
WEBHOOK_URLS = (
    os.getenv("WEBHOOK_URLS", "").split(",") if os.getenv("WEBHOOK_URLS") else []
)
SECRET_KEY = os.getenv("SECRET_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Database configurations
DATABASE_SQLITE = os.path.join("db", "finger_log.db")
MDB_PATH = os.getenv("MDB_PATH", "")
MDB_FILE = os.path.join(MDB_PATH, os.getenv("MDB_FILE", ""))
MDB_PASS = os.getenv("MDB_PASS")
MAX_RETRY = os.getenv("MAX_RETRY", 3)
