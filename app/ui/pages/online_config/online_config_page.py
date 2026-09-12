"""Online AI provider configuration — a compact, left-aligned panel.

Presentation only: :class:`app.controllers.config_controller.ConfigController`
(shared with the Offline config page) drives load/save/test/set_default —
this page just exposes the same ``selected``/``action`` signals and
``values()``/``set_values()``/``set_loading()``/``status``/``buttons``
surface the controller already expects, unchanged.
"""

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.pages.online_config.provider_form import ProviderForm
from app.ui.pages.online_config.provider_tabs import ProviderTabs
from app.ui.widgets.toast import Toast

_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"
_PROVIDERS = ["OpenAI", "Claude", "Gemini", "Suno", "Stability", "Khác"]


class OnlineConfigPage(QWidget):
    selected = Signal(str)
    action = Signal(str, str, dict)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("onlineConfigPage")
        self.names = _PROVIDERS
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 24)
        root.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(10)
        icon = QLabel()
        icon.setObjectName("onlineConfigHeadingIcon")
        icon.setFixedSize(32, 32)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setPixmap(QIcon(str(_ICONS / "gear.svg")).pixmap(QSize(18, 18)))
        heading = QLabel("Cấu hình AI Online")
        heading.setObjectName("onlineConfigHeading")
        header.addWidget(icon)
        header.addWidget(heading)
        header.addStretch(1)
        root.addLayout(header)

        self.toast = Toast(plain=True)
        root.addWidget(self.toast)

        self.tabs = ProviderTabs(self.names)
        root.addWidget(self.tabs)

        # Fixed max-width, left-aligned — the reference's compact panel,
        # not a form stretched across the whole content area. 480px read as
        # too cramped against the real (sidebar-adjacent) window, so this
        # sits a bit wider while still stopping well short of full width.
        panel = QWidget()
        panel.setObjectName("providerPanel")
        panel.setMaximumWidth(640)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 4, 0, 0)
        self.form = ProviderForm()
        panel_layout.addWidget(self.form)
        root.addWidget(panel)
        root.addStretch(1)

        # ConfigController expects these exact attributes/signals — see
        # app/controllers/config_controller.py — regardless of how the
        # page itself is laid out.
        self.status = self.form.status_label
        self.buttons = {"save": self.form.save_button, "test": self.form.test_button}

        self.tabs.changed.connect(self._on_tab_changed)
        self.form.test_requested.connect(lambda: self.action.emit("test", self.current(), self.values()))
        self.form.save_requested.connect(lambda: self.action.emit("save", self.current(), self.values()))
        self._on_tab_changed(self.tabs.current())

    def _on_tab_changed(self, name: str) -> None:
        self.form.set_model_presets(name)
        self.selected.emit(name)

    def current(self) -> str:
        return self.tabs.current()

    def values(self) -> dict:
        return self.form.values()

    def set_values(self, data: dict) -> None:
        self.form.set_values(data)

    def set_loading(self, loading: bool) -> None:
        self.tabs.set_enabled(not loading)
        self.form.set_loading(loading)
