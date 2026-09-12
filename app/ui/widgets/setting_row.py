"""icon | title/description | control — the reusable settings row."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

_ICONS = Path(__file__).resolve().parents[2] / "assets/icons"


class SettingRow(QWidget):
    def __init__(
        self,
        icon_file: str,
        title: str,
        description: str = "",
        control: QWidget | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        if icon_file:
            icon = QLabel()
            icon.setObjectName("settingRowIcon")
            icon.setFixedSize(32, 32)
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            path = _ICONS / icon_file
            if path.is_file():
                icon.setPixmap(QIcon(str(path)).pixmap(QSize(18, 18)))
            row.addWidget(icon)
        text_column = QVBoxLayout()
        text_column.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("settingRowTitle")
        text_column.addWidget(title_label)
        self.description_label = None
        if description:
            self.description_label = QLabel(description)
            self.description_label.setObjectName("settingRowDescription")
            self.description_label.setWordWrap(True)
            text_column.addWidget(self.description_label)
        row.addLayout(text_column, 1)
        self.control = control
        if control is not None:
            row.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)
