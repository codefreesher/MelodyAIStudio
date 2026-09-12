"""Theme-palette waveform preview with no file or media I/O."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPalette, QPen
from PySide6.QtWidgets import QWidget


class Waveform(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.values: list[float] = []
        self.setMinimumHeight(60)
        self.setAccessibleName("Waveform preview")

    def set_values(self, values: list[float]) -> None:
        self.values = values
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(
            QPen(
                self.palette().color(QPalette.ColorRole.Accent),
                3,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        values = self.values or [0.04] * 60
        for index, value in enumerate(values):
            x = int((index + 0.5) * self.width() / len(values))
            half = max(2, int(min(1, value * 3) * self.height() * 0.42))
            painter.drawLine(x, self.height() // 2 - half, x, self.height() // 2 + half)
