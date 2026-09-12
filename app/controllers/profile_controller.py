"""Open and submit the account profile dialog."""

from PySide6.QtCore import QObject, QThreadPool, Signal, Slot

from app.core.exceptions import AuthenticationError
from app.models.user import User
from app.services.account_service import AccountService
from app.ui.widgets.dialog import ProfileDialog
from app.utils.async_utils import Worker


class ProfileController(QObject):
    updated = Signal(object)

    def __init__(self, parent, sidebar, service: AccountService) -> None:
        super().__init__(parent)
        self.parent_widget = parent
        self.sidebar = sidebar
        self.service = service
        self.user: User | None = None
        self.dialog: ProfileDialog | None = None
        self.worker: Worker | None = None

    def set_user(self, user: User | None) -> None:
        self.user = user

    def open(self) -> None:
        if self.user is None or self.worker is not None:
            return
        self.dialog = ProfileDialog(self.user.username, self.user.email, self.parent_widget)
        self.dialog.save_requested.connect(self.save)
        self.dialog.open()

    @Slot(dict)
    def save(self, values: dict) -> None:
        if self.user is None or self.worker is not None or self.dialog is None:
            return
        self.dialog.set_loading(True)
        self.worker = Worker(lambda: self.service.update(self.user, values))
        self.worker.signals.result.connect(self._completed)
        self.worker.signals.error.connect(self._failed)
        self.worker.signals.finished.connect(self._finished)
        QThreadPool.globalInstance().start(self.worker)

    @Slot(object)
    def _completed(self, user: User) -> None:
        self.user = user
        if self.dialog is not None:
            self.dialog.accept()
        self.updated.emit(user)

    @Slot(object)
    def _failed(self, error: Exception) -> None:
        if self.dialog is not None:
            message = str(error) if isinstance(error, AuthenticationError) else "Không thể cập nhật tài khoản."
            self.dialog.toast.show_message(message, "error", duration_ms=0)

    @Slot()
    def _finished(self) -> None:
        if self.dialog is not None:
            self.dialog.set_loading(False)
        self.worker = None
