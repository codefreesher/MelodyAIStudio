"""Reusable text fields; validation remains in controllers/services."""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLineEdit, QWidget


class TextInput(QLineEdit):
    def __init__(self, placeholder: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setAccessibleName(placeholder)
        self.setClearButtonEnabled(True)


class PasswordInput(TextInput):
    def __init__(self, placeholder: str = "Mật khẩu", parent: QWidget | None = None) -> None:
        super().__init__(placeholder, parent)
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self.setClearButtonEnabled(False)
        self.visibility_action = self.addAction(
            QIcon(str(Path(__file__).resolve().parents[2] / "assets/icons/eye.svg")),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self.visibility_action.setText("Hiện mật khẩu")
        self.visibility_action.setCheckable(True)
        self.visibility_action.toggled.connect(self._toggle_visibility)

    def _toggle_visibility(self, visible: bool) -> None:
        self.setEchoMode(QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password)
        self.visibility_action.setText("Ẩn mật khẩu" if visible else "Hiện mật khẩu")


class SearchInput(TextInput):
    search_requested = Signal(str)

    def __init__(self, placeholder: str = "Tìm kiếm…", parent: QWidget | None = None) -> None:
        super().__init__(placeholder, parent)
        self.returnPressed.connect(lambda: self.search_requested.emit(self.text().strip()))
