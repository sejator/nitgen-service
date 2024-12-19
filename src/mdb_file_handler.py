import logging
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from src.fingerprint_handler import FingerprintHandler
from src.timestamp import TimestampManager

logger = logging.getLogger(__name__)


class MDBFileHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_timestamp = TimestampManager.read_last_timestamp()

    def on_modified(self, event: FileSystemEvent):
        if event.src_path.endswith(".mdb"):
            logger.info(f".mdb file modified: {event.src_path}")
            FingerprintHandler.find(self.last_timestamp)
