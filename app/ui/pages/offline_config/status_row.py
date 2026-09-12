"""Status indicator (colored dot + text) with an inline Test button and a
small "⋯" menu for Start/Stop — used identically by the Ollama/Stable
Diffusion/TTS forms. Start/Stop stay off the main row (per reference) but
still need *some* entry point — see OfflineConfigService.start/stop."""

from pathlib import Path

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QPushButton, QWidget

from app.ui.widgets.buttons import OutlineButton

_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"
_STATES = {
    "unknown": ("Chưa kiểm tra", "statusDotUnknown"),
    "checking": ("Đang kiểm tra…", "statusDotUnknown"),
    "running": ("Đang chạy", "statusDotRunning"),
    "stopped": ("Đã dừng", "statusDotStopped"),
}


class StatusRow(QWidget):
    test_requested = Signal()
    action_requested = Signal(str)  # "start" | "stop"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        self.dot = QLabel("●")
        self.dot.setObjectName("statusDotUnknown")
        row.addWidget(self.dot)
        self.text_label = QLabel(_STATES["unknown"][0])
        self.text_label.setObjectName("statusText")
        row.addWidget(self.text_label, 1)
        self.test_button = OutlineButton("Kiểm tra")
        self.test_button.setObjectName("statusTestButton")
        self.test_button.clicked.connect(self.test_requested.emit)
        row.addWidget(self.test_button)
        self.menu_button = QPushButton()
        self.menu_button.setObjectName("statusMenuButton")
        self.menu_button.setIcon(QIcon(str(_ICONS / "more.svg")))
        self.menu_button.setIconSize(QSize(13, 13))
        self.menu_button.setToolTip("Khởi động / dừng tiến trình")
        self.menu_button.clicked.connect(self._open_menu)
        row.addWidget(self.menu_button)
        self.state = "unknown"

    def _open_menu(self) -> None:
        menu = QMenu(self)
        menu.addAction("Khởi động", lambda: self.action_requested.emit("start"))
        menu.addAction("Dừng", lambda: self.action_requested.emit("stop"))
        menu.exec(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))

    def set_state(self, state: str) -> None:
        self.state = state
        text, object_name = _STATES.get(state, _STATES["unknown"])
        self.text_label.setText(text)
        self.dot.setObjectName(object_name)
        self.dot.style().unpolish(self.dot)
        self.dot.style().polish(self.dot)

    def set_enabled_controls(self, enabled: bool) -> None:
        self.test_button.setEnabled(enabled)
        self.menu_button.setEnabled(enabled)
