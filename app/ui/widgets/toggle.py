"""Animated accessible toggle switch using the active theme palette."""

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPaintEvent, QPalette, QPen
from PySide6.QtWidgets import QAbstractButton, QWidget


class ToggleSwitch(QAbstractButton):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._position = 0.0
        self._animation = QPropertyAnimation(self, b"position", self)
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._animate)

    def sizeHint(self) -> QSize:
        width = 44 + QFontMetrics(self.font()).horizontalAdvance(self.text())
        return QSize(width, 28)

    def get_position(self) -> float:
        return self._position

    def set_position(self, value: float) -> None:
        self._position = value
        self.update()

    position = Property(float, get_position, set_position)

    def _animate(self, checked: bool) -> None:
        self._animation.stop()
        self._animation.setStartValue(self._position)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002 - Qt signature
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QRectF(1, 5, 36, 18)
        accent = self.palette().color(QPalette.ColorRole.Accent)
        if not accent.isValid():
            accent = QColor("#FF4F9A")
        if not self.isEnabled():
            accent = self.palette().color(QPalette.ColorRole.Mid)
        off = self.palette().color(QPalette.ColorRole.Midlight)
        painter.setPen(QPen(accent if self.isChecked() else off, 1))
        painter.setBrush(accent if self.isChecked() else off)
        painter.drawRoundedRect(track, 9, 9)
        knob_x = 3 + self._position * 16
        painter.setPen(QPen(QColor(0, 0, 0, 18), 1))
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QRectF(knob_x, 7, 14, 14))
        text_color = self.palette().color(
            QPalette.ColorRole.Text if self.isEnabled() else QPalette.ColorRole.PlaceholderText
        )
        painter.setPen(text_color)
        painter.drawText(QRectF(45, 0, self.width() - 45, self.height()), Qt.AlignmentFlag.AlignVCenter, self.text())
