"""Compact pill-style provider tab row — not a full-width QTabBar."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget


class ProviderTabs(QWidget):
    changed = Signal(str)

    def __init__(self, names: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.names = list(names)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons: dict[str, QPushButton] = {}
        for index, name in enumerate(self.names):
            button = QPushButton(name)
            button.setObjectName("providerTab")
            button.setCheckable(True)
            button.setChecked(index == 0)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.group.addButton(button)
            self.buttons[name] = button
            layout.addWidget(button)
        layout.addStretch(1)
        self.group.buttonClicked.connect(lambda button: self.changed.emit(button.text()))

    def current(self) -> str:
        for name, button in self.buttons.items():
            if button.isChecked():
                return name
        return self.names[0]

    def set_enabled(self, enabled: bool) -> None:
        for button in self.buttons.values():
            button.setEnabled(enabled)
