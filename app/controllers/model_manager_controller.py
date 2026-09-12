"""Opens the Ollama model manager dialog; the dialog owns its own worker
jobs against OfflineConfigService (list/pull/delete/cancel) — kept out of
the shared ConfigController, which has no notion of a per-row model list."""

from PySide6.QtCore import QObject

from app.ui.pages.offline_config.model_manager_dialog import ModelManagerDialog


class ModelManagerController(QObject):
    def __init__(self, page, service) -> None:
        super().__init__(page)
        self.page, self.service = page, service
        self.dialog = None
        page.manage_models_requested.connect(self.open_manager)

    def open_manager(self, provider_name: str, provider_data: dict) -> None:
        self.dialog = ModelManagerDialog(self.service, provider_name, provider_data, self.page)
        self.dialog.open()
