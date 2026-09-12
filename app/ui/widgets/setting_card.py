"""A titled card container — the base unit for every settings section."""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class SettingCard(QFrame):
    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("settingCard")
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(20, 18, 20, 18)
        self.column.setSpacing(14)
        if title:
            title_label = QLabel(title)
            title_label.setObjectName("settingCardTitle")
            self.column.addWidget(title_label)

    def add_row(self, widget: QWidget) -> None:
        self.column.addWidget(widget)

    def add_row_layout(self, layout: QHBoxLayout) -> None:
        self.column.addLayout(layout)

    def add_divider(self) -> None:
        line = QFrame()
        line.setObjectName("settingCardDivider")
        line.setFixedHeight(1)
        self.column.addWidget(line)
