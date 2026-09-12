"""Compact, card-based Settings — compact pill tabs over four sub-pages
instead of one long full-width form.

Keeps the exact signal/method surface SettingsController already drives
(``save_requested``, ``action``, ``folder_action``, ``toast``,
``set_values()``) so the controller needed only additive changes (reading
folder paths for display, mapping check-update) — see settings_controller.py.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget

from app.ui.pages.online_config.provider_tabs import ProviderTabs
from app.ui.pages.settings.advanced_settings import AdvancedSettings
from app.ui.pages.settings.appearance_settings import AppearanceSettings
from app.ui.pages.settings.general_settings import GeneralSettings
from app.ui.pages.settings.storage_settings import StorageSettings
from app.ui.widgets.toast import Toast

_TABS = ("Tổng quan", "Giao diện", "Lưu trữ", "Nâng cao")


class SettingsPage(QWidget):
    save_requested = Signal(dict)
    action = Signal(str)
    folder_action = Signal(str, str)
    check_update_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("settingsPage")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(14)

        heading = QLabel("Cài đặt")
        heading.setObjectName("settingsHeading")
        root.addWidget(heading)

        self.toast = Toast(plain=True)
        root.addWidget(self.toast)

        self.tabs = ProviderTabs(list(_TABS))
        self.tabs.setObjectName("settingsTabs")
        root.addWidget(self.tabs)

        content = QWidget()
        content.setObjectName("settingsContent")
        content.setMaximumWidth(960)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 4, 0, 0)

        self.stack = QStackedWidget()
        self.general = GeneralSettings()
        self.appearance = AppearanceSettings()
        self.storage = StorageSettings()
        self.advanced = AdvancedSettings()
        for page in (self.general, self.appearance, self.storage, self.advanced):
            self.stack.addWidget(page)
        content_layout.addWidget(self.stack)
        root.addWidget(content)
        root.addStretch(1)

        self.tabs.changed.connect(lambda name: self.stack.setCurrentIndex(_TABS.index(name)))

        self.general.changed.connect(self._save)
        self.appearance.changed.connect(self._save)
        self.general.check_update_requested.connect(self.check_update_requested.emit)
        self.storage.folder_action.connect(self.folder_action.emit)
        self.advanced.action_requested.connect(self.action.emit)

    def _save(self) -> None:
        self.save_requested.emit(self.values())

    def values(self) -> dict:
        return {**self.general.values(), **self.appearance.values()}

    def set_values(self, data: dict) -> None:
        self.general.set_values(data)
        self.appearance.set_values(data)
