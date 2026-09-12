"""Translate startup intent into navigation requests for the application router."""

from PySide6.QtCore import QObject, Signal

from app.ui.pages.startup.startup_page import StartupPage


class StartupController(QObject):
    navigation_requested = Signal(str)

    def __init__(self, page: StartupPage, parent: QObject | None = None) -> None:
        super().__init__(parent)
        page.request_login.connect(self.open_login)
        page.request_activation.connect(self.open_activation)

    def open_login(self) -> None:
        self.navigation_requested.emit("login")

    def open_activation(self) -> None:
        self.navigation_requested.emit("activation")
