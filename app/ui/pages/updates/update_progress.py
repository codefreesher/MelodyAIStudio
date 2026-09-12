"""Inline download progress: bar, percent, bytes, speed, Cancel — lives
inside the update card, never a full-screen or modal progress dialog."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from app.ui.widgets.text_link import TextLink


def format_bytes(value: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{int(value)}{unit}" if unit == "B" else f"{value:.1f}{unit}"
        value /= 1024
    return f"{value:.1f}GB"


class UpdateProgress(QWidget):
    cancel_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("updateProgress")
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(6)

        self.bar = QProgressBar()
        self.bar.setObjectName("updateProgressBar")
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        column.addWidget(self.bar)

        detail_row = QHBoxLayout()
        detail_row.setSpacing(10)
        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("updateProgressPercent")
        detail_row.addWidget(self.percent_label)
        detail_row.addStretch(1)
        self.size_label = QLabel("")
        self.size_label.setObjectName("updateProgressSize")
        detail_row.addWidget(self.size_label)
        self.speed_label = QLabel("")
        self.speed_label.setObjectName("updateProgressSpeed")
        detail_row.addWidget(self.speed_label)
        column.addLayout(detail_row)

        cancel_row = QHBoxLayout()
        cancel_row.addStretch(1)
        self.cancel_link = TextLink("Hủy")
        self.cancel_link.setObjectName("updateCancelLink")
        self.cancel_link.clicked.connect(self.cancel_requested.emit)
        cancel_row.addWidget(self.cancel_link)
        column.addLayout(cancel_row)

    def set_progress(self, percent: int, downloaded: int, total: int, speed_bps: float) -> None:
        self.bar.setValue(percent)
        self.percent_label.setText(f"{percent}%")
        self.size_label.setText(f"{format_bytes(downloaded)} / {format_bytes(total)}" if total else "")
        self.speed_label.setText(f"{format_bytes(speed_bps)}/s" if speed_bps > 0 else "")
