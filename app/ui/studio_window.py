"""Authenticated workspace, independently registers feature pages."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QStackedWidget, QWidget

from app.ui.navigation import ROUTES
from app.ui.widgets.sidebar import Sidebar


class StudioWindow(QWidget):
    route_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        self.sidebar = Sidebar()
        self.stack = QStackedWidget()
        row.addWidget(self.sidebar)
        row.addWidget(self.stack, 1)
        self.pages: dict[str, QWidget] = {}
        for route, caption in ROUTES.items():
            self.sidebar.add_item(route, caption)
        self.sidebar.page_requested.connect(self.navigate)

    def register(self, route: str, page: QWidget) -> None:
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setWidget(page)
        self.pages[route] = area
        self.stack.addWidget(area)

    def navigate(self, route: str) -> None:
        if route in self.pages:
            self.stack.setCurrentWidget(self.pages[route])
            self.sidebar.set_current(route)
            self.route_changed.emit(route)
