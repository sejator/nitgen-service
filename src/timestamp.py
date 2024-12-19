import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TimestampManager:
    TIMESTAMP_FILE = "timestamp.txt"

    @staticmethod
    def write_last_timestamp(timestamp: datetime):
        try:
            with open(TimestampManager.TIMESTAMP_FILE, "w") as file:
                file.write(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            logger.info(f"Timestamp terakhir: {timestamp}")
        except Exception as e:
            logger.error(f"Gagal menyimpan timestamp: {e}")

    @staticmethod
    def read_last_timestamp() -> datetime:
        try:
            if not os.path.exists(TimestampManager.TIMESTAMP_FILE):
                logger.info(f"File {TimestampManager.TIMESTAMP_FILE} berhasil dibuat.")
                TimestampManager.write_last_timestamp(datetime.now())
                return datetime.now()

            with open(TimestampManager.TIMESTAMP_FILE, "r") as file:
                timestamp_str = file.read().strip()
                if not timestamp_str:
                    TimestampManager.write_last_timestamp(datetime.now())
                    return datetime.now()
                return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Gagal memabaca timestamp: {e}")
            return datetime.now()
