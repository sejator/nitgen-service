import os
import time
import json
import pyodbc
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import hmac
import hashlib
import platform
import getpass

# Load environment variables
load_dotenv()

# Webhook and Telegram configurations
WEBHOOK_URLS = (
    os.getenv("WEBHOOK_URLS", "").split(",") if os.getenv("WEBHOOK_URLS") else []
)
SECRET_KEY = os.getenv("SECRET_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Database configurations
DB_PATH = os.getenv("DB_PATH", "")
DB_FILE = os.path.join(DB_PATH, os.getenv("DB_FILE", ""))
DB_PASS = os.getenv("DB_PASS")
DEBUG = os.getenv("DEBUG", "False") == "True"

# Connection string for ODBC
connection_string = (
    f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DB_FILE};PWD={DB_PASS}"
)

# Timestamp file path
TIMESTAMP_FILE_PATH = "timestamp.txt"

# Set up logging
LOG_FILE = None if DEBUG else "error.log"
LOG_LEVEL = logging.INFO if DEBUG else logging.ERROR

logging.basicConfig(
    filename=LOG_FILE, level=LOG_LEVEL, format="%(asctime)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Returns a new database connection."""
    try:
        conn = pyodbc.connect(connection_string)
        return conn, conn.cursor()
    except pyodbc.Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise


def save_last_checked_timestamp(timestamp: datetime):
    """Saves the last checked timestamp to a file."""
    try:
        with open(TIMESTAMP_FILE_PATH, "w") as file:
            file.write(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        logger.info(f"Last checked timestamp saved: {timestamp}")
    except Exception as e:
        logger.error(f"Error saving timestamp: {e}")


def read_last_checked_timestamp() -> datetime:
    """Reads the last checked timestamp from the file or initializes it."""
    try:
        if not os.path.exists(TIMESTAMP_FILE_PATH):
            logger.info(f"File {TIMESTAMP_FILE_PATH} not found, creating a new one.")
            save_last_checked_timestamp(datetime.now())
            return datetime.now()

        with open(TIMESTAMP_FILE_PATH, "r") as file:
            timestamp_str = file.read().strip()
            if not timestamp_str:
                save_last_checked_timestamp(datetime.now())
                return datetime.now()
            logger.info(f"Last checked timestamp: {timestamp_str}")
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Error reading timestamp: {e}")
        return datetime.now()


def send_to_telegram(message):
    """Sends fingerprint data to Telegram synchronously."""
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "html",
    }

    try:
        response = requests.post(telegram_url, data=payload, timeout=30)
        response.raise_for_status()
        logger.info("Data successfully sent to Telegram")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending data to Telegram: {e}")


def send_to_webhook(payload):
    """Sends fingerprint data to configured webhooks."""

    signature = hmac.new(
        SECRET_KEY.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Adms Server Nitgen/1.0(Adms Webhook Nitgen)",
        "Accept": "application/json",
        "X-Adms-Signature": signature,
    }

    for url in WEBHOOK_URLS:
        try:
            response = requests.post(url, data=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"Data successfully sent to {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending data to {url}: {e}")


def get_new_fingerprint_data(last_checked_timestamp: datetime) -> datetime:
    """Fetches new fingerprint data from the database."""
    try:
        conn, cursor = get_db_connection()
        query = """
            SELECT l.nodeid AS key, l.userid AS pin, l.logtime AS waktu, l.authresult AS status,
            l.authtype AS verifikasi, l.functionno AS workcode FROM NGAC_LOG l
            WHERE l.authresult = 0 AND l.logtime > ? ORDER BY l.logtime ASC
        """
        logger.info(f"Fetching data after: {last_checked_timestamp}")
        cursor.execute(query, last_checked_timestamp)
        rows = cursor.fetchall()

        if not rows:
            logger.info("No new data found.")
            conn.close()  # Close connection
            return last_checked_timestamp

        latest_timestamp = rows[-1].waktu

        for row in rows:
            fingerprint_data = {
                "key": row.key,
                "pin": row.pin[:-5] if row.pin is not None else "0",
                "waktu": row.waktu.strftime("%Y-%m-%d %H:%M:%S"),
                "status": row.status,
                "verifikasi": row.verifikasi,
                "workcode": int(row.workcode),
            }
            payload = json.dumps(
                fingerprint_data, separators=(",", ":"), sort_keys=True
            )
            send_to_webhook(payload)
            send_to_telegram(f"<pre>{payload}</pre>")

        save_last_checked_timestamp(latest_timestamp)
        conn.close()  # Close connection
        return latest_timestamp

    except Exception as e:
        logger.error(f"Error fetching fingerprint data: {e}")
        return last_checked_timestamp


class MDBFileHandler(FileSystemEventHandler):
    """Handles file system events for .mdb file modifications."""

    def on_modified(self, event):
        if str(event.src_path).endswith(".mdb"):
            logger.info(f".mdb file modified: {event.src_path}")
            global last_checked_timestamp
            last_checked_timestamp = get_new_fingerprint_data(last_checked_timestamp)


def read_mdb_file():
    """Monitors the .mdb file for changes."""
    event_handler = MDBFileHandler()
    observer = Observer()
    observer.schedule(event_handler, DB_PATH, recursive=False)
    observer.start()
    service = json.dumps(
        {
            "service": "Nitgen Webhook Windows Service Auto Run",
            "os": platform.system(),
            "user": getpass.getuser(),
            "timestamp": datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
        },
        separators=(",", ":"),
        sort_keys=True,
        indent=2,
    )
    logger.info(service)
    send_to_telegram(f"<pre>{service}</pre>")

    try:
        while True:
            time.sleep(1)  # sleep 1 detik
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    last_checked_timestamp = read_last_checked_timestamp()
    read_mdb_file()
