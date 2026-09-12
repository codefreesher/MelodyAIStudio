"""Update lifecycle with stale-result reset and explicit install confirmation."""

from PySide6.QtCore import QObject, QThreadPool, Signal, Slot

from app.ui.widgets.dialog import ConfirmDialog
from app.utils.async_utils import Worker


class UpdateController(QObject):
    installer_started = Signal()

    def __init__(self, page, service) -> None:
        super().__init__(page)
        self.page, self.service, self.worker, self.release = page, service, None, None
        self.downloaded = False
        self.can_install = lambda: True
        page.action.connect(self.action)
        config = service.settings.get("github", {})
        page.owner.setText(config.get("owner", ""))
        page.repository.setText(config.get("repository", ""))

    def action(self, action: str) -> None:
        if action == "cancel":
            self.service.cancel_event.set()
            return
        if self.worker:
            return
        if action == "install":
            if not self.release or not self.downloaded:
                return
            self.dialog = ConfirmDialog("Cài cập nhật", "Đóng MelodyAI và mở trình cài đặt?", self.page)
            self.dialog.accepted.connect(self.install)
            self.dialog.open()
            return
        if action == "check":
            self.release = None
            self.downloaded = False
            self.page.notes.clear()
            self.page.latest.setText("Đang kiểm tra…")
            owner, repository = self.page.owner.text().strip(), self.page.repository.text().strip()

            def function():
                return self.service.check(owner, repository)
        elif action == "download" and self.release:
            self.service.cancel_event.clear()

            def function():
                return self.service.download(self.release, self.worker.signals.progress.emit)
        else:
            return
        self.operation = action
        self.page.progress.setValue(0)
        self.page.owner.setEnabled(False)
        self.page.repository.setEnabled(False)
        self.worker = Worker(function)
        self.worker.signals.result.connect(self.result)
        self.worker.signals.error.connect(self.error)
        self.worker.signals.finished.connect(self.finished)
        self.worker.signals.progress.connect(self.page.progress.setValue)
        for button in self.page.buttons.values():
            button.setEnabled(False)
        self.page.buttons["cancel"].setEnabled(action == "download")
        QThreadPool.globalInstance().start(self.worker)

    @Slot(object)
    def result(self, value):
        if self.operation == "check":
            self.release = value
            self.page.latest.setText("Đã là bản mới nhất." if not value else f"Bản mới: {value.version}")
            if value:
                self.page.notes.setPlainText(value.notes)
        elif self.operation == "install":
            self.install_succeeded = True
        else:
            self.downloaded = True
            self.page.toast.show_message("Đã tải và xác minh SHA256.", "success")

    @Slot(object)
    def error(self, error):
        self.page.toast.show_message(
            str(error) if isinstance(error, ValueError) else "Không thể truy cập GitHub/tải update.", "error"
        )

    @Slot()
    def finished(self):
        self.worker = None
        self.page.owner.setEnabled(True)
        self.page.repository.setEnabled(True)
        self.page.buttons["check"].setEnabled(True)
        self.page.buttons["cancel"].setEnabled(False)
        self.page.buttons["download"].setEnabled(self.release is not None)
        self.page.buttons["install"].setEnabled(self.downloaded)
        if self.operation == "install" and self.install_succeeded:
            self.installer_started.emit()

    def install(self) -> None:
        if not self.can_install():
            self.page.toast.show_message("Hoàn tất các tác vụ đang chạy trước khi cài update.")
            return
        self.operation = "install"
        self.install_succeeded = False
        self.worker = Worker(lambda: self.service.install(self.release))
        self.worker.signals.result.connect(self.result)
        self.worker.signals.error.connect(self.error)
        self.worker.signals.finished.connect(self.finished)
        for button in self.page.buttons.values():
            button.setEnabled(False)
        QThreadPool.globalInstance().start(self.worker)
