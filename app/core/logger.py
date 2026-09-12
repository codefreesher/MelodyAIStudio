"""Application-owned rotating file logging."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(log_directory: Path) -> logging.Logger:
    log_directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("melodyai")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    handler = RotatingFileHandler(
        log_directory / "app.log",
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
    return logger
