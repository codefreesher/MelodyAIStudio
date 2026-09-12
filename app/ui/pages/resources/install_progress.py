"""Reusable inline download/install progress row — no modal dialog."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget

from app.ui.widgets.text_link import TextLink


class InstallProgress(QWidget):
    """A thin progress bar + percent + Cancel, meant to live inside a
    ResourceItem row in place of its status/action area while a job runs."""

    cancel_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("installProgress")
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        self.bar = QProgressBar()
        self.bar.setObjectName("installProgressBar")
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        row.addWidget(self.bar, 1)

        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("installProgressPercent")
        row.addWidget(self.percent_label)

        self.cancel_link = TextLink("Hủy")
        self.cancel_link.setObjectName("installProgressCancel")
        self.cancel_link.clicked.connect(self.cancel_requested.emit)
        row.addWidget(self.cancel_link)

    def set_value(self, value: int) -> None:
        value = max(0, min(100, int(value)))
        self.bar.setValue(value)
        self.percent_label.setText(f"{value}%")
