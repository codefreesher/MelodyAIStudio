"""Offline (local engine) configuration — compact per-provider forms behind
a small pill tab row, not one generic field-set shared by all three engines.

Exposes exactly what the shared
:class:`app.controllers.config_controller.ConfigController` (unchanged)
expects — ``selected``/``action`` signals, ``values()``/``set_values()``/
``set_loading()``, ``status``, ``buttons``, ``toast`` — so it keeps driving
load/save/test/start/stop unchanged. ``manage_models_requested`` has no
shared-controller equivalent; see ``ModelManagerController``.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget

from app.ui.pages.offline_config.ollama_config import OllamaForm
from app.ui.pages.offline_config.sd_config import StableDiffusionForm
from app.ui.pages.offline_config.tts_config import TTSLocalForm
from app.ui.pages.online_config.provider_tabs import ProviderTabs
from app.ui.widgets.toast import Toast


class _StatusProxy:
    """Adapter so ConfigController's ``page.status.setText(value)`` — only
    ever called after a *successful* result — reaches the active form's
    status dot/message instead of one shared label."""

    def __init__(self, page: "OfflineConfigPage") -> None:
        self._page = page

    def setText(self, value: str) -> None:
        form = self._page.forms[self._page.current()]
        if self._page.last_action in ("test", "start", "stop"):
            form.status_row.set_state("running" if self._page.last_action != "stop" else "stopped")
        form.status_message.setText(str(value))


class OfflineConfigPage(QWidget):
    selected = Signal(str)
    action = Signal(str, str, dict)
    manage_models_requested = Signal(str, dict)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("offlineConfigPage")
        # Internal identifiers only — must match the keys OfflineConfigService
        # already stores settings under ("offline:Ollama", etc); the tab
        # button label for the third one is cosmetically shortened below.
        self.names = ["Ollama", "Stable Diffusion", "TTS Local"]
        self.last_action: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 24)
        root.setSpacing(14)

        heading = QLabel("Cấu hình AI Offline")
        heading.setObjectName("offlineConfigHeading")
        root.addWidget(heading)

        self.toast = Toast(plain=True)
        root.addWidget(self.toast)

        self.tabs = ProviderTabs(self.names)
        root.addWidget(self.tabs)

        panel = QWidget()
        panel.setObjectName("offlineProviderPanel")
        panel.setMaximumWidth(640)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 4, 0, 0)

        self.stack = QStackedWidget()
        self.ollama_form = OllamaForm()
        self.sd_form = StableDiffusionForm()
        self.tts_form = TTSLocalForm()
        self.forms = {
            "Ollama": self.ollama_form,
            "Stable Diffusion": self.sd_form,
            "TTS Local": self.tts_form,
        }
        for form in self.forms.values():
            self.stack.addWidget(form)
        panel_layout.addWidget(self.stack)
        root.addWidget(panel)
        root.addStretch(1)

        # ConfigController only ever does `"cancel" in self.page.buttons` —
        # offline no longer routes pull/delete/cancel through it (see
        # ModelManagerDialog), so there is nothing to register here.
        self.buttons: dict = {}
        self.status = _StatusProxy(self)

        for name, form in self.forms.items():
            form.test_requested.connect(lambda _=False, n=name: self._request_action("test", n))
            form.save_requested.connect(lambda _=False, n=name: self._request_action("save", n))
            form.status_row.action_requested.connect(lambda action, n=name: self._request_action(action, n))
        self.ollama_form.manage_requested.connect(
            lambda: self.manage_models_requested.emit("Ollama", self.ollama_form.values())
        )

        self.tabs.changed.connect(self._on_tab_changed)
        self._on_tab_changed(self.tabs.current())

    def _on_tab_changed(self, name: str) -> None:
        self.stack.setCurrentWidget(self.forms[name])
        self.selected.emit(name)

    def _request_action(self, action: str, name: str) -> None:
        self.last_action = action
        if action == "test":
            self.forms[name].status_row.set_state("checking")
        self.action.emit(action, name, self.forms[name].values())

    def current(self) -> str:
        return self.tabs.current()

    def values(self) -> dict:
        return self.forms[self.current()].values()

    def set_values(self, data: dict) -> None:
        self.forms[self.current()].set_values(data)

    def set_loading(self, loading: bool) -> None:
        self.tabs.set_enabled(not loading)
        self.forms[self.current()].set_loading(loading)
        if not loading and self.last_action == "test":
            row = self.forms[self.current()].status_row
            if row.state == "checking":
                row.set_state("stopped")
