"""Borderless inline link — styled and sized like plain text, not a button."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QWidget


class TextLink(QPushButton):
    def __init__(self, text: str = "", icon: QIcon | None = None, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("textLink")
        self.setProperty("role", "link")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        if icon is not None:
            self.setIcon(icon)
            self.setIconSize(QSize(14, 14))
