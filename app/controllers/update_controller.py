"""Update lifecycle driving UpdateCard's state machine; explicit install
confirmation, stale-result reset. Owner/repository are fixed configuration
(app.core.constants / AppConfig override) rather than free-typed UI fields —
see app/studio.py for how they're resolved.
"""

import time
from datetime import datetime

from PySide6.QtCore import QObject, QThreadPool, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from app.ui.widgets.dialog import ConfirmDialog
from app.utils.async_utils import Worker


def _now_text() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


class UpdateController(QObject):
    installer_started = Signal()

    def __init__(self, page, service, owner: str, repository: str) -> None:
        super().__init__(page)
        self.page, self.service = page, service
        self.owner, self.repository = owner, repository
        self.worker = None
        self.release = None
        self.downloaded = False
        self.operation: str | None = None
        self.install_succeeded = False
        self.can_install = lambda: True
        self._download_started_at = 0.0
        self._download_total = 0

        card = page.card
        card.check_requested.connect(self.check)
        card.download_requested.connect(self.download)
        card.cancel_requested.connect(self.cancel)
        card.install_requested.connect(self.confirm_install)
        card.dismiss_requested.connect(self.dismiss)
        card.view_release_requested.connect(self.view_release)

    def _release_context(self) -> dict:
        if not self.release:
            return {}
        return {
            "latest_version": self.release.version,
            "notes": self.release.notes,
            "size": self.release.size,
            "html_url": self.release.html_url,
        }

    def check(self) -> None:
        if self.worker:
            return
        if not (self.owner and self.repository):
            self.page.toast.show_message("Chưa cấu hình nguồn cập nhật.", "error")
            return
        self.release = None
        self.downloaded = False
        self.page.card.set_state("CHECKING")
        self._run("check", lambda: self.service.check(self.owner, self.repository))

    def download(self) -> None:
        if self.worker or not self.release:
            return
        self.service.cancel_event.clear()
        self._download_started_at = time.monotonic()
        self._download_total = self.release.size
        self.page.card.set_state("DOWNLOADING", **self._release_context())
        self.page.card.progress.set_progress(0, 0, self._download_total, 0)
        self._run("download", lambda: self.service.download(self.release, self.worker.signals.progress.emit))

    def cancel(self) -> None:
        self.service.cancel_event.set()

    def dismiss(self) -> None:
        self.page.card.set_state("UPDATE_AVAILABLE", **self._release_context())

    def view_release(self) -> None:
        if self.release and self.release.html_url:
            QDesktopServices.openUrl(QUrl(self.release.html_url))

    def confirm_install(self) -> None:
        if not self.release or not self.downloaded:
            return
        if not self.can_install():
            self.page.toast.show_message("Hoàn tất các tác vụ đang chạy trước khi cài update.")
            return
        self.dialog = ConfirmDialog("Cài cập nhật", "Đóng MelodyAI và mở trình cài đặt?", self.page)
        self.dialog.accepted.connect(self.install)
        self.dialog.open()

    def install(self) -> None:
        self.page.card.set_state("INSTALLING", **self._release_context())
        self.install_succeeded = False
        self._run("install", lambda: self.service.install(self.release))

    def _run(self, operation: str, function) -> None:
        self.operation = operation
        self.worker = Worker(function)
        self.worker.signals.result.connect(self.result)
        self.worker.signals.error.connect(self.error)
        self.worker.signals.finished.connect(self.finished)
        if operation == "download":
            self.worker.signals.progress.connect(self._on_download_progress)
        QThreadPool.globalInstance().start(self.worker)

    def _on_download_progress(self, percent: int) -> None:
        elapsed = max(0.001, time.monotonic() - self._download_started_at)
        downloaded = int(self._download_total * percent / 100) if self._download_total else 0
        state = "VERIFYING" if percent >= 100 else "DOWNLOADING"
        self.page.card.set_state(state, **self._release_context())
        self.page.card.progress.set_progress(percent, downloaded, self._download_total, downloaded / elapsed)

    @Slot(object)
    def result(self, value: object) -> None:
        if self.operation == "check":
            self.release = value
            if value is None:
                self.page.card.set_state("UP_TO_DATE", checked_at=_now_text())
            else:
                self.page.card.set_state("UPDATE_AVAILABLE", **self._release_context())
        elif self.operation == "download":
            self.downloaded = True
            self.page.card.set_state("READY_TO_INSTALL", **self._release_context())
        elif self.operation == "install":
            self.install_succeeded = True

    @Slot(object)
    def error(self, error: object) -> None:
        message = str(error) if isinstance(error, ValueError) else "Không thể truy cập GitHub/tải update."
        if self.operation == "download" and isinstance(error, ValueError) and "hủy" in message.lower():
            # User-initiated cancel — quietly back to "update available",
            # not a scary error box.
            self.page.card.set_state("UPDATE_AVAILABLE", **self._release_context())
            return
        self.page.card.set_state("ERROR", error_summary=message, error_detail=type(error).__name__)

    @Slot()
    def finished(self) -> None:
        self.worker = None
        if self.operation == "install" and self.install_succeeded:
            self.installer_started.emit()
