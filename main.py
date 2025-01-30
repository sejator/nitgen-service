import sys
import logging
import platform
import getpass
import json
import threading
from time import sleep
from datetime import datetime
from src.webhook import WebhookSender
from src.database import DatabaseConnection
from logging.handlers import RotatingFileHandler
from src.config import MDB_PATH, DEBUG
# from src.mdb_file_handler import MDBFileHandler
from watchdog.observers import Observer
from src.fingerprint_handler import FingerprintHandler
from src.timestamp import TimestampManager

# Set up logging with rotation
LOG_FILE = None if DEBUG else "error.log"
LOG_LEVEL = logging.DEBUG if DEBUG else logging.ERROR
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

if LOG_FILE:
    handler = RotatingFileHandler(LOG_FILE, maxBytes=10**6, backupCount=3)
    logging.basicConfig(handlers=[handler], level=LOG_LEVEL, format=LOG_FORMAT)
else:
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)

logger = logging.getLogger(__name__)

# Event to signal threads to stop gracefully
stop_event = threading.Event()


def retry_send_webhook():
    while not stop_event.is_set():
        try:
            WebhookSender.retry_send_to_webhook()
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
            sleep(180)
        sleep(60)


def read_mdb_file():
    # menggunakan metode event perubahan file
    # event_handler = MDBFileHandler()
    # observer = Observer()
    # observer.schedule(event_handler, MDB_PATH, recursive=False)
    # observer.start()

    # try:
    #     observer.join()
    # except Exception as e:
    #     logger.error(f"Error in MDB file reading loop: {e}")
    # finally:
    #     observer.stop()
    #     observer.join()

    # menggunakan metode pooling
    while not stop_event.is_set():
        try:
            last_timestamp = TimestampManager.read_last_timestamp()
            FingerprintHandler.find_pooling(last_timestamp)
        except Exception as e:
            logger.error(f"Error pooling: {e}")
            sleep(180)
        logger.info("Delay 20 detik...")
        sleep(20)


def log_service_info():
    service_info = json.dumps(
        {
            "service": "Nitgen Service Auto Run",
            "os": platform.system(),
            "user": getpass.getuser(),
            "timestamp": datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
        },
        separators=(",", ":"),
        sort_keys=True,
        indent=2,
    )
    logger.info(service_info)
    WebhookSender.send_to_telegram(
        f"<b>NITGEN SERVICE</b>\n\n<pre>{service_info}</pre>"
    )


def start_threads():
    mdb_thread = threading.Thread(target=read_mdb_file, daemon=True)
    mdb_thread.start()

    webhook_thread = threading.Thread(target=retry_send_webhook, daemon=True)
    webhook_thread.start()

    return mdb_thread, webhook_thread


def main():
    log_service_info()
    start_threads()

    try:
        while not stop_event.is_set():
            sleep(1)
    except KeyboardInterrupt:
        logger.info("Program stopped by user (CTRL + C).")
        stop_event.set()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        stop_event.set()


if __name__ == "__main__":
    try:
        DatabaseConnection.create_db()
        main()
    except KeyboardInterrupt:
        logger.info("Program stopped by user (CTRL + C).")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        sys.exit(0)
