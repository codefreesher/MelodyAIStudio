"""TTS (local) engine configuration form.

No engine-picker dropdown (Coqui/Piper/XTTS/...): the app has no working
multi-engine TTS provider yet (``app/providers/local/local_tts_provider.py``
is a stub), so a dropdown like that would be UI with nothing real behind
it. Voice/model is a plain field, same as the other forms, backed by the
same generic ``load``/``save``/``test`` in OfflineConfigService.
"""

from pathlib import Path

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QWidget

from app.ui.pages.offline_config.advanced_section import AdvancedSection
from app.ui.pages.offline_config.path_field import PathField
from app.ui.pages.offline_config.status_row import StatusRow
from app.ui.widgets.buttons import PrimaryButton

_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"


class TTSLocalForm(QWidget):
    test_requested = Signal()
    save_requested = Signal()

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

        path_label = QLabel("Đường dẫn TTS engine")
        path_label.setObjectName("offlineFieldLabel")
        column.addWidget(path_label)
        self.executable = PathField("Đường dẫn tới engine", mode="file")
        column.addWidget(self.executable)
        column.addSpacing(10)

        folder_label = QLabel("Thư mục voice models")
        folder_label.setObjectName("offlineFieldLabel")
        column.addWidget(folder_label)
        self.models_folder = PathField("Thư mục chứa voice models", mode="folder")
        column.addWidget(self.models_folder)
        column.addSpacing(10)

        model_label = QLabel("Voice mặc định")
        model_label.setObjectName("offlineFieldLabel")
        column.addWidget(model_label)
        self.model = QLineEdit()
        self.model.setObjectName("offlineModelInput")
        column.addWidget(self.model)
        column.addSpacing(12)

        self.advanced = AdvancedSection()
        url_label = QLabel("API URL")
        url_label.setObjectName("offlineFieldLabel")
        self.advanced.add_widget(url_label)
        self.url = QLineEdit()
        self.url.setObjectName("offlineAdvancedInput")
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
            "models_folder": self.models_folder.text(),
            "model": self.model.text(),
            "url": self.url.text(),
            "arguments": self.arguments.text(),
        }

    def set_values(self, data: dict) -> None:
        self.executable.setText(str(data.get("executable", "")))
        self.models_folder.setText(str(data.get("models_folder", "")))
        self.model.setText(str(data.get("model", "")))
        self.url.setText(str(data.get("url", "")))
        self.arguments.setText(str(data.get("arguments", "")))
        self.status_row.set_state("unknown")
        self.status_message.setText("")

    def set_loading(self, loading: bool) -> None:
        for widget in (
            self.executable,
            self.models_folder,
            self.model,
            self.save_button,
            self.url,
            self.arguments,
        ):
            widget.setEnabled(not loading)
        self.status_row.set_enabled_controls(not loading)
