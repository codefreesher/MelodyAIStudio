"""Overview tab: general preferences + update summary card."""

import sys

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.core.constants import UPDATE_CHANNEL
from app.core.version import get_version
from app.ui.widgets.buttons import OutlineButton
from app.ui.widgets.dropdown import ComboBox
from app.ui.widgets.setting_card import SettingCard
from app.ui.widgets.setting_row import SettingRow
from app.ui.widgets.toggle_switch import ToggleSwitch

_LANGUAGES = (("vi", "Tiếng Việt"), ("en", "English"))
# Auto-start is only wired up on a frozen Windows build (see
# SettingsService.save) — reflect that here instead of letting the switch
# look like it works everywhere and only failing after the fact.
_STARTUP_SUPPORTED = sys.platform == "win32" and getattr(sys, "frozen", False)
_STARTUP_LABEL = "Khởi động cùng Windows" if sys.platform == "win32" else "Khởi động cùng hệ thống"


class GeneralSettings(QWidget):
    changed = Signal()
    check_update_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(16)

        general_card = SettingCard("Cài đặt chung")
        self.language = ComboBox([label for _, label in _LANGUAGES])
        self.language.setObjectName("settingsCombo")
        self.language.currentIndexChanged.connect(lambda _index: self.changed.emit())
        general_card.add_row(SettingRow("languages.svg", "Ngôn ngữ", "Ngôn ngữ hiển thị của MelodyAI", self.language))
        general_card.add_divider()

        self.auto_update = ToggleSwitch()
        self.auto_update.toggled.connect(lambda _checked: self.changed.emit())
        general_card.add_row(
            SettingRow(
                "refresh-cw.svg",
                "Tự động kiểm tra cập nhật",
                "Kiểm tra phiên bản mới khi mở MelodyAI",
                self.auto_update,
            )
        )
        general_card.add_divider()

        self.start_windows = ToggleSwitch()
        self.start_windows.setEnabled(_STARTUP_SUPPORTED)
        if not _STARTUP_SUPPORTED:
            self.start_windows.setToolTip("Chưa hỗ trợ trên hệ điều hành/bản chạy này.")
        self.start_windows.toggled.connect(lambda _checked: self.changed.emit())
        general_card.add_row(
            SettingRow(
                "monitor.svg",
                _STARTUP_LABEL,
                "Tự động mở MelodyAI khi đăng nhập",
                self.start_windows,
            )
        )
        column.addWidget(general_card)

        update_card = SettingCard("Cập nhật")
        version_row = QHBoxLayout()
        version_label = QLabel("Phiên bản")
        version_label.setObjectName("settingRowTitle")
        version_row.addWidget(version_label)
        version_row.addStretch(1)
        value = QLabel(f"v{get_version()}")
        value.setObjectName("settingValue")
        version_row.addWidget(value)
        update_card.add_row_layout(version_row)

        channel_row = QHBoxLayout()
        channel_label = QLabel("Kênh cập nhật")
        channel_label.setObjectName("settingRowTitle")
        channel_row.addWidget(channel_label)
        channel_row.addStretch(1)
        channel_value = QLabel(UPDATE_CHANNEL.capitalize())
        channel_value.setObjectName("settingValue")
        channel_row.addWidget(channel_value)
        update_card.add_row_layout(channel_row)

        check_row = QHBoxLayout()
        check_row.addStretch(1)
        self.check_update_button = OutlineButton("Kiểm tra cập nhật")
        self.check_update_button.setObjectName("settingsCheckUpdate")
        self.check_update_button.clicked.connect(self.check_update_requested.emit)
        check_row.addWidget(self.check_update_button)
        update_card.add_row_layout(check_row)
        column.addWidget(update_card)
        column.addStretch(1)

    def values(self) -> dict:
        language_code = _LANGUAGES[self.language.currentIndex()][0] if self.language.currentIndex() >= 0 else "vi"
        return {
            "language": language_code,
            "auto_update": self.auto_update.isChecked(),
            "start_windows": self.start_windows.isChecked(),
        }

    def set_values(self, data: dict) -> None:
        # Programmatic updates still emit currentIndexChanged/toggled —
        # block them so loading saved values doesn't itself trigger an
        # auto-save round-trip (and a spurious "Đã lưu cài đặt." toast).
        for widget in (self.language, self.auto_update, self.start_windows):
            widget.blockSignals(True)
        try:
            codes = [code for code, _ in _LANGUAGES]
            language = data.get("language", "vi")
            self.language.setCurrentIndex(codes.index(language) if language in codes else 0)
            self.auto_update.setChecked(bool(data.get("auto_update", True)))
            self.start_windows.setChecked(bool(data.get("start_windows", False)) and _STARTUP_SUPPORTED)
        finally:
            for widget in (self.language, self.auto_update, self.start_windows):
                widget.blockSignals(False)
