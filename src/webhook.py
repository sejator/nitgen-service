import hmac
import hashlib
import logging
import requests
import asyncio
from datetime import datetime
from src.database import DatabaseConnection
from src.timestamp import TimestampManager
from src.config import (
    WEBHOOK_URLS,
    SECRET_KEY,
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID,
    MAX_RETRY,
    DEBUG,
)

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Adms Server Nitgen/1.0(Adms Webhook Nitgen)",
    "Accept": "application/json",
}

logger = logging.getLogger(__name__)


class WebhookSender:
    @staticmethod
    async def async_send_to_telegram(message):
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "html",
        }
        try:
            response = requests.post(telegram_url, data=payload, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Gagal mengirim data ke Telegram: {e}")

    @staticmethod
    def send_to_telegram(message):

        asyncio.run(WebhookSender.async_send_to_telegram(message))

    @staticmethod
    def send_to_webhook(payload, latest_timestamp):
        signature = hmac.new(
            SECRET_KEY.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        HEADERS["X-Adms-Signature"] = signature
        for url in WEBHOOK_URLS:
            try:
                response = requests.post(url, data=payload, headers=HEADERS, timeout=30)
                response.raise_for_status()
                logger.info(f"Data berhasil di kirim ke {url}")

                if DEBUG:
                    WebhookSender.send_to_telegram(
                        f"<b>WEBHOOK NITGEN</b>\n\n<pre>{payload}</pre>"
                    )
            except requests.exceptions.RequestException as e:
                logger.error(f"Gagal mengirim data ke {url}: {e}")
                WebhookSender.save_to_database(payload, signature, url)
            finally:
                TimestampManager.write_last_timestamp(latest_timestamp)
                logger.info(f"Timestamp terakhir disimpan: {latest_timestamp}")

    @staticmethod
    def save_to_database(payload, signature, webhook_url):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = DatabaseConnection.get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO logs (payload, signature, webhook_url, timestamp, retry_count) VALUES (?, ?, ?, ?, ?)",
                (payload, signature, webhook_url, timestamp, 0),
            )
            conn.commit()
            conn.close()
            logger.info("Data webhook yang gagal disimpan ke SQLite.")
        except Exception as e:
            logger.error(f"Error menyimpan data gagal ke SQLite: {e}")

    @staticmethod
    def retry_send_to_webhook():
        try:
            conn = DatabaseConnection.get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT id, payload, signature, webhook_url, retry_count FROM logs WHERE retry_count < {MAX_RETRY} LIMIT 30"
            )
            rows = cursor.fetchall()

            if not rows:
                return None

            for row in rows:
                id, payload, signature, webhook_url, retry_count = row
                HEADERS["X-Adms-Signature"] = signature
                try:
                    response = requests.post(
                        webhook_url,
                        data=payload,
                        headers=HEADERS,
                    )
                    response.raise_for_status()
                    logger.info(f"Data berhasil dikirim ulang ke {webhook_url}")

                    # Jika pengiriman berhasil, hapus dari tabel logs
                    cursor.execute("DELETE FROM logs WHERE id = ?", (id,))
                    conn.commit()

                    if DEBUG:
                        WebhookSender.send_to_telegram(
                            f"<b>RETRY WEBHOOK NITGEN</b>\n\n<pre>{payload}</pre>"
                        )

                except requests.exceptions.RequestException as e:
                    logger.error(f"Kirim ulang gagal ID {id} ke {webhook_url}: {e}")
                    retry_count += 1
                    cursor.execute(
                        "UPDATE logs SET retry_count = ? WHERE id = ?",
                        (retry_count, id),
                    )
                    conn.commit()

            conn.close()
        except Exception as e:
            logger.error(f"Gagal mengirim ulang ke webhook: {e}")
