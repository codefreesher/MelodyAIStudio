"""Dashboard refresh orchestration."""

from app.services.history_service import HistoryService
from app.ui.pages.dashboard.dashboard_page import DashboardPage


class DashboardController:
    def __init__(self, page: DashboardPage, history: HistoryService) -> None:
        self.page, self.history = page, history

    def refresh(self) -> None:
        self.page.set_projects(self.history.list(size=4)[0])
