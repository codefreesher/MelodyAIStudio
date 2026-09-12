"""A compact pink ON/OFF switch — visual replacement for QCheckBox."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QAbstractButton, QWidget


class ToggleSwitch(QAbstractButton):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(40, 22)

    def sizeHint(self) -> QSize:
        return QSize(40, 22)

    def paintEvent(self, event) -> None:  # noqa: ANN001 - Qt signature
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        on = self.isChecked()
        if not self.isEnabled():
            track_color = QColor("#F0E9EC")
        else:
            track_color = QColor("#FF4F95") if on else QColor("#D8D1D5")
        painter.setBrush(track_color)
        rect = self.rect().adjusted(0, 0, -1, -1)
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        knob_diameter = rect.height() - 4
        x = rect.width() - knob_diameter - 2 if on else 2
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(x, 2, knob_diameter, knob_diameter)
