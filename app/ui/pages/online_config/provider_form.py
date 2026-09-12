"""Reusable single-provider config form — the compact reference panel
(API key + inline test, model, base URL, default toggle, save), reused
across provider tabs by swapping its values rather than duplicating it.
"""

from pathlib import Path

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from app.ui.widgets.buttons import OutlineButton, PrimaryButton
from app.ui.widgets.dropdown import ComboBox
from app.ui.widgets.inputs import PasswordInput

_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"

# Curated presets per provider; anything already saved (including a custom
# value) still loads fine since the combo box is editable.
_MODEL_PRESETS = {
    "OpenAI": ["gpt-4o", "gpt-4.1", "gpt-4.1-mini", "gpt-5"],
    "Claude": ["claude-sonnet", "claude-opus"],
    "Gemini": ["gemini-pro", "gemini-flash"],
}


class ProviderForm(QWidget):
    test_requested = Signal()
    save_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("providerForm")
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)

        key_label = QLabel("API Key")
        key_label.setObjectName("providerFieldLabel")
        column.addWidget(key_label)
        key_row = QHBoxLayout()
        key_row.setSpacing(8)
        self.api_key = PasswordInput("API Key")
        self.api_key.setObjectName("providerApiKey")
        key_row.addWidget(self.api_key, 1)
        self.test_button = OutlineButton("Kiểm tra")
        self.test_button.setObjectName("providerTestButton")
        self.test_button.clicked.connect(self.test_requested.emit)
        key_row.addWidget(self.test_button)
        column.addLayout(key_row)
        column.addSpacing(10)

        model_label = QLabel("Model mặc định")
        model_label.setObjectName("providerFieldLabel")
        column.addWidget(model_label)
        self.model = ComboBox()
        self.model.setObjectName("providerModel")
        self.model.setEditable(True)
        column.addWidget(self.model)
        column.addSpacing(10)

        base_label = QLabel("Base URL (nếu có)")
        base_label.setObjectName("providerFieldLabel")
        column.addWidget(base_label)
        self.base_url = QLineEdit()
        self.base_url.setObjectName("providerBaseUrl")
        self.base_url.setPlaceholderText("https://api.openai.com/v1")
        column.addWidget(self.base_url)
        column.addSpacing(12)

        self.is_default = QCheckBox("Sử dụng làm mặc định")
        self.is_default.setObjectName("providerDefaultToggle")
        column.addWidget(self.is_default)
        column.addSpacing(12)

        self.save_button = PrimaryButton("Lưu cấu hình")
        self.save_button.setObjectName("providerSaveButton")
        self.save_button.setIcon(QIcon(str(_ICONS / "save-white.svg")))
        self.save_button.setIconSize(QSize(14, 14))
        self.save_button.clicked.connect(self.save_requested.emit)
        column.addWidget(self.save_button)
        column.addSpacing(6)

        self.status_label = QLabel("")
        self.status_label.setObjectName("providerStatus")
        self.status_label.setWordWrap(True)
        column.addWidget(self.status_label)

    def set_model_presets(self, provider: str) -> None:
        current = self.model.currentText()
        self.model.blockSignals(True)
        self.model.clear()
        self.model.addItems(_MODEL_PRESETS.get(provider, []))
        self.model.setCurrentText(current)
        self.model.blockSignals(False)

    def values(self) -> dict:
        return {
            "api_key": self.api_key.text(),
            "model": self.model.currentText(),
            "base_url": self.base_url.text(),
            "is_default": self.is_default.isChecked(),
        }

    def set_values(self, data: dict) -> None:
        self.api_key.setText(str(data.get("api_key") or ""))
        self.model.setCurrentText(str(data.get("model", "")))
        self.base_url.setText(str(data.get("base_url", "")))
        self.is_default.setChecked(bool(data.get("is_default", False)))
        self.status_label.setText("")

    def set_loading(self, loading: bool) -> None:
        for widget in (
            self.api_key,
            self.model,
            self.base_url,
            self.is_default,
            self.save_button,
            self.test_button,
        ):
            widget.setEnabled(not loading)
