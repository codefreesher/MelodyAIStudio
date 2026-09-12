"""Three selectable mode cards (Light/Dark/System) — visual theme picker.

Internal values stay the app's real theme ids (pink_light/pink_dark/system);
only the on-screen labels are user-facing Vietnamese names.

Built on QFrame rather than QPushButton: a QPushButton with a child layout
on top of it fights the button's own chrome painting and the icon/label
never actually show up — a plain clickable QFrame avoids that entirely.
"""

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

_ICONS = Path(__file__).resolve().parents[2] / "assets/icons"
_MODES = (
    ("pink_light", "sun.svg", "Hồng sáng"),
    ("pink_dark", "moon.svg", "Hồng tối"),
    ("system", "monitor.svg", "Theo hệ thống"),
)


class _ModeCard(QFrame):
    clicked = Signal()

    def __init__(self, icon_file: str, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("themeModeCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("checked", False)
        content = QVBoxLayout(self)
        content.setContentsMargins(14, 14, 14, 14)
        content.setSpacing(8)
        icon = QLabel()
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        path = _ICONS / icon_file
        if path.is_file():
            icon.setPixmap(QIcon(str(path)).pixmap(QSize(22, 22)))
        content.addWidget(icon)
        text = QLabel(label)
        text.setObjectName("themeModeLabel")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content.addWidget(text)

    def setChecked(self, checked: bool) -> None:
        self.setProperty("checked", checked)
        self.style().unpolish(self)
        self.style().polish(self)

    def isChecked(self) -> bool:
        return bool(self.property("checked"))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class ThemeSelector(QWidget):
    changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        self.cards: dict[str, _ModeCard] = {}
        for value, icon_file, label in _MODES:
            card = _ModeCard(icon_file, label)
            card.clicked.connect(lambda v=value: self._select(v))
            self.cards[value] = card
            row.addWidget(card, 1)

    def _select(self, value: str) -> None:
        self.set_value(value)
        self.changed.emit(value)

    def set_value(self, value: str) -> None:
        if value not in self.cards:
            value = "pink_light"
        for candidate, card in self.cards.items():
            card.setChecked(candidate == value)

    def value(self) -> str:
        for value, card in self.cards.items():
            if card.isChecked():
                return value
        return "pink_light"
