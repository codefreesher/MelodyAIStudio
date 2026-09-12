"""Reusable asynchronous dialogs: connect accepted/rejected, then call open()."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.widgets.buttons import DangerButton, OutlineButton, PrimaryButton
from app.ui.widgets.inputs import PasswordInput, TextInput
from app.ui.widgets.toast import Toast


class ConfirmDialog(QDialog):
    def __init__(
        self, title: str, message: str, parent: QWidget | None = None, destructive: bool = False
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(440, 180)
        layout = QVBoxLayout(self)
        label = QLabel(message)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setWordWrap(True)
        layout.addWidget(label)
        row = QHBoxLayout()
        row.addStretch()
        self.cancel_button = OutlineButton("Hủy")
        self.confirm_button = (DangerButton if destructive else PrimaryButton)("Xác nhận")
        self.cancel_button.clicked.connect(self.reject)
        self.confirm_button.clicked.connect(self.accept)
        row.addWidget(self.cancel_button)
        row.addWidget(self.confirm_button)
        layout.addLayout(row)
        self.cancel_button.setFocus()


class ErrorDialog(QDialog):
    def __init__(self, message: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("MelodyAI — Lỗi")
        self.resize(440, 180)
        layout = QVBoxLayout(self)
        label = QLabel(message)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setWordWrap(True)
        layout.addWidget(label)
        close = PrimaryButton("Đóng")
        close.clicked.connect(self.accept)
        layout.addWidget(close)


class ProfileDialog(QDialog):
    save_requested = Signal(dict)

    def __init__(self, username: str, email: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("profileDialog")
        self.setWindowTitle("Thông tin tài khoản")
        self.setModal(True)
        self.setMinimumWidth(500)
        root = QVBoxLayout(self)
        title = QLabel("Thông tin tài khoản")
        title.setProperty("role", "heading")
        root.addWidget(title)
        subtitle = QLabel("Cập nhật tên hiển thị hoặc thay đổi mật khẩu của bạn.")
        subtitle.setProperty("role", "muted")
        root.addWidget(subtitle)
        self.toast = Toast(plain=True)
        root.addWidget(self.toast)
        form = QFormLayout()
        form.setSpacing(12)
        self.email = TextInput()
        self.email.setText(email)
        self.email.setReadOnly(True)
        self.email.setClearButtonEnabled(False)
        self.username = TextInput("Tên tài khoản")
        self.username.setText(username)
        self.current_password = PasswordInput("Mật khẩu hiện tại")
        self.new_password = PasswordInput("Mật khẩu mới (để trống nếu không đổi)")
        self.confirm_password = PasswordInput("Nhập lại mật khẩu mới")
        form.addRow("Email", self.email)
        form.addRow("Tên tài khoản", self.username)
        form.addRow("Mật khẩu hiện tại", self.current_password)
        form.addRow("Mật khẩu mới", self.new_password)
        form.addRow("Xác nhận mật khẩu", self.confirm_password)
        root.addLayout(form)
        actions = QHBoxLayout()
        actions.addStretch(1)
        self.cancel_button = OutlineButton("Hủy")
        self.save_button = PrimaryButton("Lưu thay đổi")
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(lambda: self.save_requested.emit(self.values()))
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.save_button)
        root.addLayout(actions)

    def values(self) -> dict:
        return {
            "username": self.username.text().strip(),
            "current_password": self.current_password.text(),
            "new_password": self.new_password.text(),
            "confirm_password": self.confirm_password.text(),
        }

    def set_loading(self, loading: bool) -> None:
        self.save_button.set_loading(loading, "Đang lưu…")
        for widget in (
            self.username,
            self.current_password,
            self.new_password,
            self.confirm_password,
            self.cancel_button,
        ):
            widget.setEnabled(not loading)
