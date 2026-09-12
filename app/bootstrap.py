"""Initialize storage, logging, configuration, then the UI."""

import logging
import sys
from types import TracebackType

from app.application import Application
from app.core.config import AppConfig
from app.core.environment import check_environment
from app.core.logger import configure_logging
from app.core.paths import AppPaths
from app.core.version import get_version


def bootstrap(argv: list[str], smoke_test: bool = False, showcase: bool = False) -> int:
    check_environment()
    paths = AppPaths.default()
    paths.ensure_directories()
    logger = configure_logging(paths.logs)
    try:
        config = AppConfig.load(paths.config_file)
    except (ValueError, UnicodeError):
        logger.warning("Invalid configuration; using defaults without overwriting it")
        config = AppConfig()
    version = get_version()
    application = Application(argv, config, paths, version)
    previous_hook = sys.excepthook

    def report_error(
        kind: type[BaseException],
        error: BaseException,
        traceback: TracebackType | None,
    ) -> None:
        from PySide6.QtWidgets import QMessageBox

        logger.error("Unhandled application error", exc_info=(kind, error, traceback))
        QMessageBox.critical(
            application.window,
            "MelodyAI",
            "Đã xảy ra lỗi. Vui lòng kiểm tra nhật ký ứng dụng.",
        )

    sys.excepthook = report_error
    try:
        logger.info("Starting MelodyAI %s", version)
        return application.run(smoke_test=smoke_test, showcase=showcase)
    finally:
        sys.excepthook = previous_hook
        logger.info("MelodyAI stopped")
        logging.shutdown()
