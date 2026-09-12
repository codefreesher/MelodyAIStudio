"""Resource jobs with inline (per-row) progress/cancel and scoped file actions."""

import shutil
from pathlib import Path

from PySide6.QtCore import QObject, QThreadPool, QUrl, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog

from app.resources_manager.resource_manifest import load_manifest
from app.ui.widgets.dialog import ConfirmDialog
from app.utils.async_utils import Worker

_DOWNLOAD_ACTIONS = ("install", "download", "repair")


class ResourceController(QObject):
    def __init__(self, page, service) -> None:
        super().__init__(page)
        self.page, self.service, self.worker = page, service, None
        self.active_id: str | None = None
        page.action.connect(self.action)
        page.import_requested.connect(self.import_manifest)
        page.reload_requested.connect(self.refresh)
        page.cancel_requested.connect(self.service.cancel_event.set)

    def refresh(self) -> None:
        self.page.show_resources(self.service.list())

    def import_manifest(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self.page, "Resource manifest", "", "JSON (*.json)")
        if path:
            try:
                load_manifest(Path(path))
                self.service.manifest.parent.mkdir(parents=True, exist_ok=True)
                if Path(path).resolve() != self.service.manifest.resolve():
                    shutil.copy2(path, self.service.manifest)
                self.refresh()
            except (OSError, ValueError, KeyError):
                self.page.toast.show_message("Manifest không hợp lệ.", "error")

    def action(self, item: dict, action: str) -> None:
        if self.worker:
            return
        if action in _DOWNLOAD_ACTIONS and not (item.get("url") and item.get("sha256")):
            self.page.toast.show_message(
                "Admin chưa cấu hình file tải và mã SHA-256 cho tài nguyên này.",
                "error",
                duration_ms=0,
            )
            return
        if action == "open":
            folder = self.service.root / item["id"]
            if folder.is_dir():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
            else:
                self.page.toast.show_message("Chưa có thư mục tài nguyên.")
            return
        if action == "remove":
            self.confirm = ConfirmDialog("Gỡ tài nguyên", f"Gỡ {item['name']}?", self.page, True)
            self.confirm.accepted.connect(lambda: self.start(item, action))
            self.confirm.open()
            return
        self.start(item, action)

    def start(self, item: dict, action: str) -> None:
        self.service.cancel_event.clear()
        self.active_id = item["id"]
        row = self.page.get_item(self.active_id)
        if row and action in _DOWNLOAD_ACTIONS:
            row.set_downloading(True)
        self.page.set_busy(True)
        self.worker = Worker(lambda: self.service.perform(item, action, self.worker.signals.progress.emit))
        self.worker.signals.progress.connect(self._progress)
        self.worker.signals.result.connect(self.result)
        self.worker.signals.error.connect(self.error)
        self.worker.signals.finished.connect(self.finished)
        QThreadPool.globalInstance().start(self.worker)

    def _progress(self, value: object) -> None:
        row = self.page.get_item(self.active_id)
        if row:
            row.set_progress(value)

    @Slot(object)
    def result(self, value):
        self.page.toast.show_message(str(value), "success")

    @Slot(object)
    def error(self, error):
        self.page.toast.show_message(
            str(error) if isinstance(error, ValueError) else "Không thể xử lý tài nguyên.", "error"
        )

    @Slot()
    def finished(self):
        self.page.set_busy(False)
        self.worker = None
        self.active_id = None
        self.refresh()
