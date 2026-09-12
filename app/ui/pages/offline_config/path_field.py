"""A text field with a trailing browse button (file or folder picker)."""

from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QPushButton, QWidget

_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"


class PathField(QWidget):
    def __init__(self, placeholder: str = "", mode: str = "file", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._mode = mode
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        self.input = QLineEdit()
        self.input.setObjectName("offlinePathInput")
        self.input.setPlaceholderText(placeholder)
        row.addWidget(self.input, 1)
        self.browse_button = QPushButton()
        self.browse_button.setObjectName("offlineBrowseButton")
        self.browse_button.setIcon(QIcon(str(_ICONS / "folder.svg")))
        self.browse_button.setIconSize(QSize(15, 15))
        self.browse_button.setToolTip("Chọn thư mục" if mode == "folder" else "Chọn tệp")
        self.browse_button.clicked.connect(self._browse)
        row.addWidget(self.browse_button)

    def _browse(self) -> None:
        if self._mode == "folder":
            path = QFileDialog.getExistingDirectory(self, "Chọn thư mục", self.input.text())
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Chọn tệp", self.input.text())
        if path:
            self.input.setText(path)

    def text(self) -> str:
        return self.input.text()

    def setText(self, value: str) -> None:
        self.input.setText(value)
