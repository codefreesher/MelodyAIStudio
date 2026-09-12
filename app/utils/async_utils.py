"""Reusable QRunnable; UI slots receive results on their owning thread."""

import logging
import traceback
from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    started = Signal()
    progress = Signal(int)
    result = Signal(object)
    error = Signal(object)
    finished = Signal()


class Worker(QRunnable):
    def __init__(self, function: Callable[[], object]) -> None:
        super().__init__()
        self.function = function
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        self.signals.started.emit()
        try:
            self.signals.result.emit(self.function())
        except Exception as error:
            # Record stack locations without the exception message or local values,
            # which may contain provider credentials or user prompts.
            frames = traceback.extract_tb(error.__traceback__)
            location = " -> ".join(f"{frame.filename}:{frame.lineno} in {frame.name}" for frame in frames)
            logging.getLogger("melodyai").warning("Task failed (%s): %s", type(error).__name__, location)
            self.signals.error.emit(error)
        finally:
            self.function = lambda: None
            self.signals.finished.emit()
