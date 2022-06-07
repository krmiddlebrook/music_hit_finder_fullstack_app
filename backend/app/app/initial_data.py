import logging
import shutil
from pathlib import Path  # noqa: F401

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_directories(remake_audio_dir: bool = True) -> None:
    if settings.AUDIO_DIR.exists() and remake_audio_dir:
        shutil.rmtree(settings.AUDIO_DIR)
    settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    settings.MP3_DIR.mkdir(parents=True, exist_ok=True)
    settings.WAV_DIR.mkdir(parents=True, exist_ok=True)


def init() -> None:
    db = SessionLocal()
    init_db(db)

    init_directories()


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
