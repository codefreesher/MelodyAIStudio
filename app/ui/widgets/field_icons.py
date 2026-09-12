"""Explicitly sized field icons, independent of Qt's internal action buttons."""

from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QSize, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QLabel, QLineEdit, QToolButton


class FieldIcons(QObject):
    def __init__(self, field: QLineEdit, path: Path, action: QAction | None = None) -> None:
        super().__init__(field)
        self.field = field
        self.leading = QLabel(field)
        self.leading.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.leading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.leading.setFixedSize(32, 32)
        pixmap = QIcon(str(path)).pixmap(QSize(56, 56))
        pixmap.setDevicePixelRatio(2)
        self.leading.setPixmap(pixmap)
        self.trailing = None
        if action is not None:
            field.removeAction(action)
            self.trailing = QToolButton(field)
            self.trailing.setObjectName("fieldVisibility")
            self.trailing.setDefaultAction(action)
            self.trailing.setIconSize(QSize(24, 24))
            self.trailing.setFixedSize(32, 32)
            self.trailing.setCursor(Qt.CursorShape.PointingHandCursor)
        field.setTextMargins(36, 0, 36 if action else 0, 0)
        field.installEventFilter(self)
        self._position()

    def _position(self) -> None:
        y = (self.field.height() - 32) // 2
        self.leading.move(10, y)
        if self.trailing is not None:
            self.trailing.move(self.field.width() - 42, y)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            self._position()
        return super().eventFilter(watched, event)
