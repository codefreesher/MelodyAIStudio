"""Layered backdrop for the startup page: soft glows instead of a flat fill."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QRadialGradient
from PySide6.QtWidgets import QWidget


class StartupBackground(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002 - Qt signature
        width, height = self.width(), self.height()
        if width <= 0 or height <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#FFF8FB"))

        glows = (
            # center, radius fraction of max(width,height), color, alpha
            (QPointF(width * 0.82, height * 0.35), 0.62, "#FFE4F0", 200),
            (QPointF(width * 0.12, height * 0.2), 0.5, "#FFFFFF", 235),
            (QPointF(width * 0.28, height * 0.85), 0.45, "#FFD9E9", 130),
        )
        span = max(width, height)
        for center, ratio, hex_color, alpha in glows:
            radius = span * ratio
            gradient = QRadialGradient(center, radius)
            color = QColor(hex_color)
            color.setAlpha(alpha)
            transparent = QColor(hex_color)
            transparent.setAlpha(0)
            gradient.setColorAt(0.0, color)
            gradient.setColorAt(1.0, transparent)
            painter.fillRect(self.rect(), gradient)

        self._draw_petals(painter, width, height)

    @staticmethod
    def _draw_petals(painter: QPainter, width: int, height: int) -> None:
        """A handful of soft translucent petals; decorative, never dense."""
        petal_color = QColor("#FF9AC4")
        spots = (
            (0.06, 0.16, 10), (0.1, 0.62, 7), (0.86, 0.1, 8),
            (0.94, 0.58, 11), (0.35, 0.06, 6), (0.7, 0.92, 9),
        )
        painter.setPen(Qt.PenStyle.NoPen)
        for fx, fy, size in spots:
            color = QColor(petal_color)
            color.setAlpha(46)
            painter.setBrush(color)
            cx, cy = width * fx, height * fy
            painter.drawEllipse(QRectF(cx - size / 2, cy - size / 1.4, size, size * 1.4))
