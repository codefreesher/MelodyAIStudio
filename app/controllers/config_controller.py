"""Common worker lifecycle for configuration services."""

from PySide6.QtCore import QObject, QThreadPool, Slot

from app.ui.widgets.dialog import ConfirmDialog
from app.utils.async_utils import Worker


class ConfigController(QObject):
    def __init__(self, page, service) -> None:
        super().__init__(page)
        self.page, self.service, self.worker = page, service, None
        page.selected.connect(self.load)
        page.action.connect(self.action)

    def load(self, name: str) -> None:
        self.run(lambda: self.service.load(name), load=True)

    def action(self, action: str, name: str, data: dict) -> None:
        if action == "cancel":
            self.service.cancel_event.set()
            return
        if action == "delete":
            self.dialog = ConfirmDialog(
                "Xóa model", f"Xóa model {data.get('model', '')} khỏi local engine?", self.page, True
            )
            self.dialog.accepted.connect(lambda: self.run(lambda: self.service.delete(name, data)))
            self.dialog.open()
            return
        self.run(lambda: getattr(self.service, action)(name, data))

    def run(self, function, load: bool = False) -> None:
        if self.worker:
            return
        if hasattr(self.service, "cancel_event"):
            self.service.cancel_event.clear()
        self.loading_data = load
        self.page.set_loading(True)
        if "cancel" in self.page.buttons:
            self.page.buttons["cancel"].setEnabled(True)
        self.worker = Worker(function)
        self.worker.signals.result.connect(self.result)
        self.worker.signals.error.connect(self.error)
        self.worker.signals.finished.connect(self.finished)
        QThreadPool.globalInstance().start(self.worker)

    @Slot(object)
    def result(self, value: object) -> None:
        if self.loading_data:
            self.page.set_values(value)
        else:
            self.page.status.setText(str(value))

    @Slot(object)
    def error(self, error: Exception) -> None:
        self.page.toast.show_message(
            str(error)
            if isinstance(error, ValueError)
            else "Không thể thực hiện. Kiểm tra cấu hình/kết nối.",
            "error",
        )

    @Slot()
    def finished(self) -> None:
        self.page.set_loading(False)
        self.worker = None
