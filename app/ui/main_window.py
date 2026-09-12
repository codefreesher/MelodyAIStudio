"""Application shell hosting startup; future routes register with the shell."""

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from app.controllers.startup_controller import StartupController
from app.core.constants import APP_NAME, APP_SUBTITLE
from app.ui.pages.startup.startup_page import StartupPage
from app.ui.widgets.titlebar import TitleBar

if TYPE_CHECKING:
    from app.controllers.login_controller import LoginController
    from app.ui.pages.login.login_page import LoginPage

_ICON_PATH = Path(__file__).resolve().parents[1] / "assets/icons/melodyai.ico"


class MainWindow(QMainWindow):
    navigation_requested = Signal(str)
    authentication_successful = Signal(object)

    def __init__(self, version: str) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — {APP_SUBTITLE} | {version}")
        if _ICON_PATH.is_file():
            self.setWindowIcon(QIcon(str(_ICON_PATH)))
        self.resize(1280, 720)
        self.setMinimumSize(1100, 650)

        self.startup_page = StartupPage(version, self)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.startup_page)

        # Keep branding visible even when the desktop hides native decorations.
        # Window controls remain owned by the OS/window manager.
        self.title_bar = TitleBar(APP_NAME, APP_SUBTITLE, show_controls=False)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.title_bar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(content)

        self.startup_controller = StartupController(self.startup_page, self)
        self.startup_controller.navigation_requested.connect(self._route_requested)

    def _route_requested(self, destination: str) -> None:
        self.navigation_requested.emit(destination)
        if destination == "login" and hasattr(self, "login_page"):
            self.stack.setCurrentWidget(self.login_page)
            self.login_page.identifier.setFocus()
            return
        if destination == "activation" and hasattr(self, "activation_page"):
            self.stack.setCurrentWidget(self.activation_page)
            return
        # Other pages are reserved for their own stages.
        names = {"login": "Đăng nhập", "activation": "Kích hoạt"}
        self.statusBar().showMessage(
            f"{names[destination]} sẽ khả dụng trong giai đoạn tiếp theo.",
            4000,
        )

    def attach_login(self, page: "LoginPage", controller: "LoginController") -> None:
        self.login_page = page
        self.login_controller = controller
        self.stack.addWidget(page)
        controller.back_requested.connect(self.show_startup)
        controller.authentication_successful.connect(self.authentication_successful.emit)

    def show_startup(self) -> None:
        self.login_page.password.clear()
        self.login_page.password.visibility_action.setChecked(False)
        self.login_page.toast.hide()
        self.stack.setCurrentWidget(self.startup_page)

    def closeEvent(self, event) -> None:
        if hasattr(self, "can_close") and not self.can_close():
            self.statusBar().showMessage("Tác vụ đang chạy. Hủy hoặc chờ hoàn tất trước khi đóng.", 5000)
            event.ignore()
            return
        if hasattr(self, "on_close"):
            self.on_close()
        super().closeEvent(event)
