import sqlite3
import pyodbc
import logging
import os
from src.config import DATABASE_SQLITE, MDB_FILE, MDB_PASS

logger = logging.getLogger(__name__)


class DatabaseConnection:
    @staticmethod
    def get_sqlite_connection():
        try:
            conn = sqlite3.connect(DATABASE_SQLITE)
            return conn
        except sqlite3.Error as e:
            logger.error(f"Gagal koneksi ke database SQLite: {e}")
            raise

    @staticmethod
    def get_odbc_connection():
        try:
            conn = pyodbc.connect(
                f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={MDB_FILE};PWD={MDB_PASS}"
            )
            return conn
        except pyodbc.Error as e:
            logger.error(f"Gagal koneksi ke database ODBC: {e}")
            raise

    @staticmethod
    def create_db():
        """Buat database sqlite"""
        try:
            if not os.path.exists("db"):
                os.makedirs("db")
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
            logger.error(f"Gagal membuat table SQLite: {e}")
