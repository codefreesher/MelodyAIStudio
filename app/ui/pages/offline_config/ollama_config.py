"""Ollama configuration form: status, path, default model, advanced, save.

Presentation only — :class:`app.controllers.config_controller.ConfigController`
drives load/save/test; :class:`ModelManagerController` drives the model
manager dialog opened from here. Field keys (``executable``, ``model``,
``url``, ``arguments``) match what
:class:`app.services.offline_config_service.OfflineConfigService` already
reads/writes — nothing renamed at the service boundary.
"""

from pathlib import Path

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from app.ui.pages.offline_config.advanced_section import AdvancedSection
from app.ui.pages.offline_config.path_field import PathField
from app.ui.pages.offline_config.status_row import StatusRow
from app.ui.widgets.buttons import OutlineButton, PrimaryButton

_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"


class OllamaForm(QWidget):
    test_requested = Signal()
    save_requested = Signal()
    manage_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)

        status_label = QLabel("Trạng thái")
        status_label.setObjectName("offlineFieldLabel")
        column.addWidget(status_label)
        self.status_row = StatusRow()
        self.status_row.test_requested.connect(self.test_requested.emit)
        column.addWidget(self.status_row)
        column.addSpacing(10)

        path_label = QLabel("Đường dẫn Ollama")
        path_label.setObjectName("offlineFieldLabel")
        column.addWidget(path_label)
        self.executable = PathField("Đường dẫn tới ollama", mode="file")
        column.addWidget(self.executable)
        column.addSpacing(10)

        model_label = QLabel("Model mặc định")
        model_label.setObjectName("offlineFieldLabel")
        column.addWidget(model_label)
        model_row = QHBoxLayout()
        model_row.setSpacing(8)
        self.model = QLineEdit()
        self.model.setObjectName("offlineModelInput")
        self.model.setPlaceholderText("llama3")
        model_row.addWidget(self.model, 1)
        self.manage_button = OutlineButton("Quản lý model")
        self.manage_button.setObjectName("offlineManageButton")
        self.manage_button.clicked.connect(self.manage_requested.emit)
        model_row.addWidget(self.manage_button)
        column.addLayout(model_row)
        column.addSpacing(12)

        self.advanced = AdvancedSection()
        url_label = QLabel("API URL")
        url_label.setObjectName("offlineFieldLabel")
        self.advanced.add_widget(url_label)
        self.url = QLineEdit()
        self.url.setObjectName("offlineAdvancedInput")
        self.url.setPlaceholderText("http://127.0.0.1:11434")
        self.advanced.add_widget(self.url)
        args_label = QLabel("Launch arguments")
        args_label.setObjectName("offlineFieldLabel")
        self.advanced.add_widget(args_label)
        self.arguments = QLineEdit()
        self.arguments.setObjectName("offlineAdvancedInput")
        self.advanced.add_widget(self.arguments)
        column.addWidget(self.advanced)
        column.addSpacing(12)

        self.save_button = PrimaryButton("Lưu cấu hình")
        self.save_button.setObjectName("offlineSaveButton")
        self.save_button.setIcon(QIcon(str(_ICONS / "save-white.svg")))
        self.save_button.setIconSize(QSize(14, 14))
        self.save_button.clicked.connect(self.save_requested.emit)
        column.addWidget(self.save_button)
        column.addSpacing(6)

        self.status_message = QLabel("")
        self.status_message.setObjectName("offlineStatusMessage")
        self.status_message.setWordWrap(True)
        column.addWidget(self.status_message)

    def values(self) -> dict:
        return {
            "executable": self.executable.text(),
            "model": self.model.text(),
            "url": self.url.text(),
            "arguments": self.arguments.text(),
        }

    def set_values(self, data: dict) -> None:
        self.executable.setText(str(data.get("executable", "")))
        self.model.setText(str(data.get("model", "")))
        self.url.setText(str(data.get("url", "")))
        self.arguments.setText(str(data.get("arguments", "")))
        self.status_row.set_state("unknown")
        self.status_message.setText("")

    def set_loading(self, loading: bool) -> None:
        for widget in (self.executable, self.model, self.manage_button, self.save_button, self.url, self.arguments):
            widget.setEnabled(not loading)
        self.status_row.set_enabled_controls(not loading)
