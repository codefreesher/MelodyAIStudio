"""GitHub update controls and release notes."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QLabel, QPlainTextEdit, QProgressBar, QVBoxLayout, QWidget

from app.ui.widgets.buttons import OutlineButton, PrimaryButton
from app.ui.widgets.inputs import TextInput
from app.ui.widgets.toast import Toast


class UpdatePage(QWidget):
    action = Signal(str)

    def __init__(self, version: str) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.addWidget(QLabel(f"Cập nhật ứng dụng · Hiện tại v{version}"))
        self.toast = Toast()
        root.addWidget(self.toast)
        form = QFormLayout()
        self.owner = TextInput("GitHub owner")
        self.repository = TextInput("Repository")
        form.addRow("Owner", self.owner)
        form.addRow("Repository", self.repository)
        root.addLayout(form)
        self.latest = QLabel("Chưa kiểm tra")
        root.addWidget(self.latest)
        self.notes = QPlainTextEdit()
        self.notes.setReadOnly(True)
        root.addWidget(self.notes)
        self.progress = QProgressBar()
        root.addWidget(self.progress)
        self.buttons = {}
        for key, caption in [
            ("check", "Kiểm tra cập nhật"),
            ("download", "Tải cập nhật"),
            ("install", "Cài cập nhật"),
            ("cancel", "Hủy tải"),
        ]:
            button = PrimaryButton(caption) if key == "check" else OutlineButton(caption)
            button.clicked.connect(lambda checked=False, action=key: self.action.emit(action))
            root.addWidget(button)
            self.buttons[key] = button
        self.buttons["download"].setEnabled(False)
        self.buttons["install"].setEnabled(False)
        self.buttons["cancel"].setEnabled(False)
