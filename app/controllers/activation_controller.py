"""Activation controller handles clipboard, worker and user-safe feedback."""

from PySide6.QtCore import QObject, QThreadPool, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication

from app.api.api_client import ApiError
from app.core.exceptions import LicenseError
from app.services.activation_service import ActivationService
from app.services.support_config_service import SupportConfigService, SupportLinks
from app.ui.pages.activation.activation_page import ActivationPage
from app.utils.async_utils import Worker


class ActivationController(QObject):
    activation_successful = Signal(object)
    back_requested = Signal()

    def __init__(
        self,
        page: ActivationPage,
        service: ActivationService,
        parent: QObject | None = None,
        support_service: SupportConfigService | None = None,
    ) -> None:
        super().__init__(parent)
        self.page, self.service = page, service
        self.worker: Worker | None = None
        self.support_worker: Worker | None = None
        self.support_links = SupportLinks()
        page.machine.setText(service.machine_id)
        page.activation_requested.connect(self.activate)
        page.back_requested.connect(self.back_requested.emit)
        page.copy_requested.connect(self.copy_machine_id)
        page.support_requested.connect(
            lambda: page.toast.show_message("Gửi Machine ID cho người cung cấp MelodyAI để được hỗ trợ.")
        )
        page.telegram_requested.connect(lambda: self._open_support_url(self.support_links.telegram_url))
        page.zalo_requested.connect(lambda: self._open_support_url(self.support_links.zalo_url))
        if support_service is not None:
            self.support_worker = Worker(support_service.fetch)
            self.support_worker.signals.result.connect(self._support_loaded)
            self.support_worker.signals.error.connect(self._support_failed)
            self.support_worker.signals.finished.connect(self._support_finished)
            QThreadPool.globalInstance().start(self.support_worker)

    def copy_machine_id(self) -> None:
        QApplication.clipboard().setText(self.service.machine_id)
        self.page.toast.show_message("Đã sao chép Machine ID.", "success")

    @Slot(object)
    def _support_loaded(self, links: SupportLinks) -> None:
        self.support_links = links
        self.page.set_support_links(bool(links.telegram_url), bool(links.zalo_url))

    @Slot(object)
    def _support_failed(self, error: Exception) -> None:
        self.page.set_support_links(False, False)

    @Slot()
    def _support_finished(self) -> None:
        self.support_worker = None

    def _open_support_url(self, url: str) -> None:
        if url:
            QDesktopServices.openUrl(QUrl(url))

    @Slot(str)
    def activate(self, token: str) -> None:
        if self.worker is not None:
            return
        if not token.strip():
            self.page.toast.show_message("Vui lòng nhập license key.", "error")
            return
        self.page.set_loading(True)
        self.worker = Worker(lambda: self.service.activate(token))
        self.worker.signals.result.connect(self._success)
        self.worker.signals.error.connect(self._error)
        self.worker.signals.finished.connect(self._finished)
        QThreadPool.globalInstance().start(self.worker)

    @Slot(object)
    def _success(self, license: object) -> None:
        self.page.license_input.clear()
        self.page.toast.show_message("Kích hoạt thành công!", "success")
        self.activation_successful.emit(license)

    @Slot(object)
    def _error(self, error: Exception) -> None:
        self.page.toast.show_message(
            str(error) if isinstance(error, (LicenseError, ApiError)) else "Không thể kích hoạt. Vui lòng thử lại.",
            "error",
        )

    @Slot()
    def _finished(self) -> None:
        self.page.set_loading(False)
        self.worker = None
