"""Login intent, validation feedback and asynchronous service execution."""

import logging

from PySide6.QtCore import QObject, QThreadPool, Signal, Slot

from app.core.exceptions import AuthenticationError
from app.services.auth_service import AuthService
from app.ui.pages.login.login_page import LoginPage
from app.utils.async_utils import Worker


class LoginController(QObject):
    authentication_successful = Signal(object)
    back_requested = Signal()

    def __init__(self, page: LoginPage, service: AuthService, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.page = page
        self.service = service
        self.worker: Worker | None = None
        page.login_requested.connect(self.login)
        page.back_requested.connect(self.back_requested.emit)
        page.forgot_requested.connect(
            lambda: page.toast.show_message("Vui lòng liên hệ Admin để được hỗ trợ đặt lại mật khẩu.")
        )
        page.google_requested.connect(lambda: page.toast.show_message("Đăng nhập Google chưa khả dụng."))
        page.admin_requested.connect(
            lambda: page.toast.show_message("Vui lòng liên hệ người cung cấp MelodyAI để tạo tài khoản.")
        )
        remembered = service.sessions.remembered_identifier()
        if remembered:
            page.identifier.setText(remembered)
            page.remember.setChecked(True)

    @Slot(str, str, bool)
    def login(self, identifier: str, password: str, remember: bool) -> None:
        if self.worker is not None:
            return
        if not identifier.strip() or not password:
            self.page.toast.show_message("Vui lòng nhập tài khoản và mật khẩu.", "error")
            return
        self.page.set_loading(True)
        self.page.toast.hide()
        self.worker = Worker(lambda: self.service.login(identifier, password, remember))
        self.worker.signals.result.connect(self._success)
        self.worker.signals.error.connect(self._error)
        self.worker.signals.finished.connect(self._finished)
        QThreadPool.globalInstance().start(self.worker)

    @Slot(object)
    def _success(self, user: object) -> None:
        self.page.password.clear()
        self.page.password.visibility_action.setChecked(False)
        self.page.toast.show_message("Đăng nhập thành công!", "success")
        self.authentication_successful.emit(user)

    @Slot(object)
    def _error(self, error: Exception) -> None:
        if isinstance(error, AuthenticationError):
            message = str(error)
        else:
            logging.getLogger("melodyai").error("Unexpected authentication failure: %s", type(error).__name__)
            message = "Không thể đăng nhập lúc này. Vui lòng thử lại."
        self.page.toast.show_message(message, "error")

    @Slot()
    def _finished(self) -> None:
        self.page.set_loading(False)
        self.worker = None
