import json
import logging
from datetime import datetime
from src.database import DatabaseConnection
from src.webhook import WebhookSender

logger = logging.getLogger(__name__)


class FingerprintHandler:
    @staticmethod
    def find(last_checked_time: datetime) -> datetime:
        try:
            conn = DatabaseConnection.get_odbc_connection()
            cursor = conn.cursor()

            query = """
                SELECT l.nodeid AS key, l.userid AS pin, l.logtime AS waktu, l.authresult AS status,
                l.authtype AS verifikasi, l.functionno AS workcode, l.logindex, l.slogtime 
                FROM NGAC_LOG l
                WHERE l.authresult = 0 AND l.slogtime > ? 
                ORDER BY l.slogtime ASC
            """

            logger.info(f"Mengambil data setelah waktu: {last_checked_time}")
            cursor.execute(query, (last_checked_time,))
            rows = cursor.fetchall()

            if not rows:
                logger.info("Tidak ada data baru.")
                return None

            latest_timestamp = rows[-1].slogtime

            for row in rows:
                fingerprint_data = {
                    "key": row.key,
                    "pin": row.pin[:-5] if row.pin else "0",
                    "waktu": row.waktu.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": row.status,
                    "verifikasi": row.verifikasi,
                    "workcode": int(row.workcode),
                }
                payload = json.dumps(
                    fingerprint_data, separators=(",", ":"), sort_keys=True
                )
                WebhookSender.send_to_webhook(payload, latest_timestamp)

        except Exception as e:
            logger.error(f"Gagal mengambil data: {e}")

    @staticmethod
    def find_pooling(last_checked_time: datetime) -> datetime:
        try:
            conn = DatabaseConnection.get_odbc_connection()
            cursor = conn.cursor()

            query = """
                SELECT TOP 30 l.nodeid AS key, l.userid AS pin, l.logtime AS waktu, l.authresult AS status,
                l.authtype AS verifikasi, l.functionno AS workcode, l.logindex, l.slogtime 
                FROM NGAC_LOG l
                WHERE l.authresult = 0 AND l.slogtime > ? 
                ORDER BY l.slogtime ASC
            """

            logger.info(f"Mengambil data setelah waktu: {last_checked_time}")
            cursor.execute(query, (last_checked_time,))
            rows = cursor.fetchall()

            if not rows:
                logger.info("Tidak ada data baru.")
                return None

            latest_timestamp = rows[-1].slogtime

            for row in rows:
                fingerprint_data = {
                    "key": row.key,
                    "pin": row.pin[:-5] if row.pin else "0",
                    "waktu": row.waktu.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": row.status,
                    "verifikasi": row.verifikasi,
                    "workcode": int(row.workcode),
                }
                payload = json.dumps(
                    fingerprint_data, separators=(",", ":"), sort_keys=True
                )
                WebhookSender.send_to_webhook(payload, latest_timestamp)

        except Exception as e:
            logger.error(f"Gagal mengambil data: {e}")
