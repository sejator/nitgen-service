import os
from time import sleep
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
import sqlite3

# Load environment variables
load_dotenv()
# buat folder db
if not os.path.exists("db"):
    os.makedirs("db")

# Webhook and Telegram configurations
WEBHOOK_URLS = (
    os.getenv("WEBHOOK_URLS", "").split(",") if os.getenv("WEBHOOK_URLS") else []
)
SECRET_KEY = os.getenv("SECRET_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Database configurations
DATABASE_SQLITE = os.path.join("db", "finger_log.db")
DB_PATH = os.getenv("DB_PATH", "")
DB_FILE = os.path.join(DB_PATH, os.getenv("DB_FILE", ""))
DB_PASS = os.getenv("DB_PASS")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
MAX_RETRY = os.getenv("MAX_RETRY", 3)

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


def create_db_finger_log():
    """Buat database sqlite"""
    try:
        conn = sqlite3.connect(DATABASE_SQLITE)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payload TEXT NOT NULL,
                signature TEXT NOT NULL,
                webhook_url TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                retry_count INTEGER NOT NULL DEFAULT 0
            )
        """
        )
        conn.commit()
        conn.close()
        logger.info("Tabel logs berhasil dibuat.")
    except sqlite3.Error as e:
        logger.error(f"Error creating SQLite table: {e}")


def get_db_connection():
    """Returns a new database connection."""
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        return conn, cursor
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


def save_failed_webhook(payload, signature, webhook_url):
    """Menyimpan data webhook yang gagal di kirim ke SQLite."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DATABASE_SQLITE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs (payload, signature, webhook_url, timestamp, retry_count) VALUES (?, ?, ?, ?, ?)",
            (payload, signature, webhook_url, timestamp, 0),
        )
        conn.commit()
        conn.close()
        logger.info("Data webhook yang gagal disimpan ke SQLite.")
    except sqlite3.Error as e:
        logger.error(f"Error menyimpan data gagal ke SQLite: {e}")


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
            save_failed_webhook(payload, signature, url)


def retry_send_to_webhook():
    """Mengulang pengiriman data webhook yang gagal."""
    try:
        conn = sqlite3.connect(DATABASE_SQLITE)
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id, payload, signature, webhook_url, retry_count FROM logs WHERE retry_count < {MAX_RETRY}"
        )
        rows = cursor.fetchall()

        for row in rows:
            id, payload, signature, webhook_url, retry_count = row
            logger.info(
                f"Mengulang pengiriman ID {id} ke {webhook_url}, percobaan ke {retry_count+1}"
            )

            try:
                response = requests.post(
                    webhook_url,
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Adms Server Nitgen/1.0(Adms Webhook Nitgen)",
                        "Accept": "application/json",
                        "X-Adms-Signature": signature,
                    },
                )
                response.raise_for_status()
                logger.info(f"Data berhasil dikirim ulang ke {webhook_url}")

                # Jika pengiriman berhasil, hapus dari tabel logs
                cursor.execute("DELETE FROM logs WHERE id = ?", (id,))
                conn.commit()

            except requests.exceptions.RequestException as e:
                logger.error(f"Retry gagal untuk data ID {id} ke {webhook_url}: {e}")
                retry_count += 1
                cursor.execute(
                    "UPDATE logs SET retry_count = ? WHERE id = ?", (retry_count, id)
                )
                conn.commit()

        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Error saat mencoba mengulang webhook yang gagal: {e}")


def get_new_fingerprint_data(last_checked_timestamp: datetime) -> datetime:
    """Fetches new fingerprint data from the database."""
    try:
        with pyodbc.connect(connection_string) as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT l.nodeid AS key, l.userid AS pin, l.logtime AS waktu, l.authresult AS status,
                    l.authtype AS verifikasi, l.functionno AS workcode, l.logindex, l.slogtime FROM NGAC_LOG l
                    WHERE l.authresult = 0 AND l.slogtime > ? ORDER BY l.logtime ASC
                """
                logger.info(f"Fetching data after: {last_checked_timestamp}")
                cursor.execute(query, last_checked_timestamp)
                rows = cursor.fetchall()

                if not rows:
                    logger.info("No new data found.")
                    last_timestamp = datetime.now()
                    save_last_checked_timestamp(last_timestamp)
                    return last_timestamp

                latest_timestamp = rows[-1].slogtime

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
                    send_to_telegram(f"<b>WEBHOOK NITGEN</b>\n\n<pre>{payload}</pre>")

                save_last_checked_timestamp(latest_timestamp)
                return latest_timestamp

    except Exception as e:
        logger.error(f"Error fetching fingerprint data: {e}")
        return last_checked_timestamp


class MDBFileHandler(FileSystemEventHandler):
    """Handles file system events for .mdb file modifications."""

    def __init__(self, last_checked_timestamp):
        self.last_checked_timestamp = last_checked_timestamp

    def on_modified(self, event):
        if str(event.src_path).endswith(".mdb"):
            logger.info(f".mdb file modified: {event.src_path}")
            self.last_checked_timestamp = get_new_fingerprint_data(
                self.last_checked_timestamp
            )


def read_mdb_file():
    """Monitors the .mdb file for changes."""
    last_checked_timestamp = read_last_checked_timestamp()
    event_handler = MDBFileHandler(last_checked_timestamp)
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
    send_to_telegram(f"<b>SERVICE NITGEN</b>\n\n<pre>{service}</pre>")

    try:
        while True:
            sleep(1)  # sleep 1 detik

            retry_send_to_webhook()
            sleep(60)  # Delay 60 detik untuk pengiriman ulang webhook
    except KeyboardInterrupt:
        logger.info("Service interrupted. Stopping observer.")
        observer.stop()
    finally:
        observer.join()


if __name__ == "__main__":
    create_db_finger_log()
    read_mdb_file()
