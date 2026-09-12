"""Application preferences and storage maintenance controls."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QFormLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.widgets.buttons import OutlineButton, PrimaryButton
from app.ui.widgets.dropdown import ComboBox
from app.ui.widgets.inputs import TextInput
from app.ui.widgets.toast import Toast


class SettingsPage(QWidget):
    save_requested = Signal(dict)
    action = Signal(str)
    folder_action = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        title = QLabel("Cài đặt")
        title.setProperty("role", "heading")
        root.addWidget(title)
        self.toast = Toast()
        root.addWidget(self.toast)
        form = QFormLayout()
        root.addLayout(form)
        self.theme = ComboBox(["pink_light", "pink_dark", "system"])
        self.accent = TextInput("#FF4F9A")
        self.language = ComboBox(["vi", "en"])
        self.auto_update = QCheckBox("Tự kiểm tra cập nhật")
        self.start_windows = QCheckBox("Khởi động cùng Windows")
        for name, widget in [
            ("Giao diện", self.theme),
            ("Màu chủ đạo", self.accent),
            ("Ngôn ngữ", self.language),
            ("Chung", self.auto_update),
            ("", self.start_windows),
        ]:
            form.addRow(name, widget)
        save = PrimaryButton("Lưu cài đặt")
        save.clicked.connect(lambda: self.save_requested.emit(self.values()))
        root.addWidget(save)
        for name in ["projects", "downloads", "models", "cache"]:
            row = QHBoxLayout()
            row.addWidget(QLabel(name), 1)
            for action, caption in [("open", "Mở thư mục"), ("change", "Đổi thư mục")]:
                button = OutlineButton(caption)
                button.clicked.connect(lambda checked=False, n=name, a=action: self.folder_action.emit(n, a))
                row.addWidget(button)
            root.addLayout(row)
        for key, caption in [
            ("clear_credentials", "Xóa credentials"),
            ("clear_session", "Xóa session / Đăng xuất"),
            ("clear_cache", "Xóa cache"),
            ("logs", "Xem logs"),
        ]:
            button = OutlineButton(caption)
            button.clicked.connect(lambda checked=False, action=key: self.action.emit(action))
            root.addWidget(button)
        root.addStretch()

    def values(self) -> dict:
        return {
            "theme": self.theme.currentText(),
            "accent": self.accent.text(),
            "language": self.language.currentText(),
            "auto_update": self.auto_update.isChecked(),
            "start_windows": self.start_windows.isChecked(),
        }

    def set_values(self, data: dict) -> None:
        self.theme.setCurrentText(data.get("theme", "pink_light"))
        self.accent.setText(data.get("accent", "#FF4F9A"))
        self.language.setCurrentText(data.get("language", "vi"))
        self.auto_update.setChecked(data.get("auto_update", True))
        self.start_windows.setChecked(data.get("start_windows", False))
