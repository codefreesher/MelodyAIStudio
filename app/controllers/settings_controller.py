"""Apply theme preferences and request maintenance through the service."""

from pathlib import Path

from PySide6.QtCore import QObject, QThreadPool, QUrl, Signal, Slot
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import QFileDialog

from app.ui.widgets.dialog import ConfirmDialog
from app.utils.async_utils import Worker


class SettingsController(QObject):
    logged_out = Signal()
    changed = Signal()

    def __init__(self, page, service, theme) -> None:
        super().__init__(page)
        self.page, self.service, self.theme = page, service, theme
        self.worker = None
        self.can_logout = lambda: True
        page.save_requested.connect(self.save)
        page.action.connect(self.action)
        page.folder_action.connect(self.folder)
        page.set_values(service.load())
        self._refresh_paths()

    def _refresh_paths(self) -> None:
        for name in ("projects", "downloads", "models", "cache"):
            self.page.storage.set_path(name, str(self.service.folder(name)))

    def save(self, data: dict) -> None:
        try:
            if not QColor.isValidColorName(data["accent"]):
                raise ValueError("Mã màu không hợp lệ.")
            message = self.service.save("", data)
            self.theme.apply(data["theme"], data["accent"])
            self.changed.emit()
            self.page.toast.show_message(message, "success")
        except (OSError, ValueError) as error:
            self.page.toast.show_message(str(error), "error")

    def folder(self, name: str, action: str) -> None:
        if action == "change":
            path = QFileDialog.getExistingDirectory(self.page, "Chọn thư mục")
            if path:
                try:
                    self.service.set_folder(name, Path(path))
                    self._refresh_paths()
                    self.changed.emit()
                except OSError:
                    self.page.toast.show_message("Không thể ghi thư mục.", "error")
        else:
            path = self.service.folder(name)
            path.mkdir(parents=True, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def action(self, action: str) -> None:
        if action == "logs":
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.service.root / "logs")))
            return
        self.dialog = ConfirmDialog("Xác nhận", "Thực hiện thao tác này?", self.page, True)
        self.dialog.accepted.connect(lambda: self.perform(action))
        self.dialog.open()

    def perform(self, action: str) -> None:
        if self.worker:
            return
        if action == "clear_session" and not self.can_logout():
            self.page.toast.show_message("Chờ tác vụ hoàn tất trước khi đăng xuất.")
            return
        self.operation = action
        self.worker = Worker(getattr(self.service, action))
        self.worker.signals.result.connect(self.completed)
        self.worker.signals.error.connect(self.failed)
        self.worker.signals.finished.connect(self.finished)
        QThreadPool.globalInstance().start(self.worker)

    @Slot(object)
    def completed(self, message):
        self.page.toast.show_message(str(message), "success")

    @Slot(object)
    def failed(self, error):
        self.operation = ""
        self.page.toast.show_message("Không thể hoàn tất thao tác.", "error")

    @Slot()
    def finished(self):
        self.worker = None
        if self.operation == "clear_session":
            self.logged_out.emit()
