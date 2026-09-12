"""Collapsed-by-default "Tùy chỉnh nâng cao" section for less-common fields."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLayout, QPushButton, QVBoxLayout, QWidget

_COLLAPSED = "▸ Tùy chỉnh nâng cao"
_EXPANDED = "▾ Tùy chỉnh nâng cao"


class AdvancedSection(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)
        self.toggle = QPushButton(_COLLAPSED)
        self.toggle.setObjectName("advancedToggle")
        self.toggle.setCheckable(True)
        self.toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle.setFlat(True)
        outer.addWidget(self.toggle)
        self.body = QWidget()
        self.body.setObjectName("advancedBody")
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 4, 0, 0)
        self.body_layout.setSpacing(8)
        self.body.setVisible(False)
        outer.addWidget(self.body)
        self.toggle.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked: bool) -> None:
        self.body.setVisible(checked)
        self.toggle.setText(_EXPANDED if checked else _COLLAPSED)

    def add_widget(self, widget: QWidget) -> None:
        self.body_layout.addWidget(widget)

    def add_layout(self, layout: QHBoxLayout | QLayout) -> None:
        self.body_layout.addLayout(layout)
