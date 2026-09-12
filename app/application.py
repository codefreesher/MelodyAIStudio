"""Own the Qt application and its top-level window."""

from PySide6.QtCore import QThreadPool, QTimer
from PySide6.QtWidgets import QApplication

from app.core.config import AppConfig
from app.core.constants import APP_NAME
from app.core.paths import AppPaths
from app.ui.main_window import MainWindow
from app.ui.themes.theme_manager import ThemeManager
from app.utils.async_utils import Worker


class Application:
    def __init__(
        self,
        argv: list[str],
        config: AppConfig,
        paths: AppPaths,
        version: str,
    ) -> None:
        self.config = config
        self.paths = paths
        self.qt = QApplication(argv)
        self.qt.setApplicationName(APP_NAME)
        self.qt.setApplicationVersion(version)
        self.theme_manager = ThemeManager(self.qt)
        self.theme_manager.apply()
        self.window = MainWindow(version)
        from app.controllers.login_controller import LoginController
        from app.providers.mock.auth_provider import MockAuthProvider
        from app.security.session_manager import JsonSessionStore, SessionManager
        from app.services.auth_service import AuthService
        from app.ui.pages.login.login_page import LoginPage

        self.sessions = SessionManager(JsonSessionStore(paths.root / "config" / "session.json"))
        self.auth_service = AuthService(MockAuthProvider(), self.sessions)
        login_page = LoginPage(self.window)
        self.login_controller = LoginController(login_page, self.auth_service, self.window)
        self.window.attach_login(login_page, self.login_controller)
        from app.controllers.activation_controller import ActivationController
        from app.core.paths import bundle_root
        from app.security.license_manager import LicenseManager
        from app.security.license_verifier import LicenseVerifier
        from app.security.machine_id import get_machine_id
        from app.services.activation_service import ActivationService
        from app.services.support_config_service import SupportConfigService
        from app.ui.pages.activation.activation_page import ActivationPage

        machine_id = get_machine_id()
        verifier = LicenseVerifier(bundle_root() / "app/assets/keys/license_public.pem")
        self.license_manager = LicenseManager(verifier, machine_id, paths.root / "config/license.token")
        activation_page = ActivationPage(self.window)
        self.activation_controller = ActivationController(
            activation_page,
            ActivationService(self.license_manager, machine_id),
            self.window,
            SupportConfigService(config.backend_base_url),
        )
        self.window.activation_page = activation_page
        self.window.stack.addWidget(activation_page)
        self.activation_controller.back_requested.connect(self.window.show_startup)
        self.studio = None
        self.window.authentication_successful.connect(self.open_studio)
        self.activation_controller.activation_successful.connect(self.open_studio)
        self.restore_worker: Worker | None = None
        self.access_timer = QTimer(self.window)
        self.access_timer.setInterval(60_000)
        self.access_timer.timeout.connect(self._validate_current_access)
        self.access_timer.start()
        QTimer.singleShot(0, self._restore_access)
        self.window.can_close = self.can_close
        self.window.on_close = self.release_media

    def open_studio(self, identity: object) -> None:
        if self.studio is None:
            from app.studio import StudioRuntime

            self.studio = StudioRuntime(self)
            self.window.stack.addWidget(self.studio.view)
        self.studio.enter(identity)
        self.window.stack.setCurrentWidget(self.studio.view)

    def release_media(self) -> None:
        if self.studio:
            self.studio.release_media()

    def _restore_access(self) -> None:
        if self.sessions.remembered_identifier():
            self.restore_worker = Worker(self.auth_service.restore_session)
            self.restore_worker.signals.result.connect(self._account_restored)
            self.restore_worker.signals.error.connect(lambda error: self._restore_license())
            self.restore_worker.signals.finished.connect(self._restore_finished)
            QThreadPool.globalInstance().start(self.restore_worker)
            return
        self._restore_license()

    def _account_restored(self, user: object) -> None:
        if user is not None:
            self.open_studio(user)
        else:
            self._restore_license()

    def _restore_finished(self) -> None:
        self.restore_worker = None

    def _restore_license(self) -> None:
        from app.core.exceptions import LicenseError

        try:
            license = self.license_manager.load()
        except LicenseError:
            return
        if license is not None:
            self.open_studio(license)

    def _validate_current_access(self) -> None:
        if self.studio is None or self.window.stack.currentWidget() is not self.studio.view:
            return
        from app.core.exceptions import LicenseError
        from app.models.license import License
        from app.models.user import User

        identity = self.studio.identity
        valid = True
        message = ""
        if isinstance(identity, License):
            try:
                valid = self.license_manager.load() is not None
            except LicenseError as error:
                valid = False
                message = str(error)
        elif isinstance(identity, User):
            valid = self.auth_service.current_session_is_active()
            message = "Gói tài khoản đã hết hạn. Vui lòng đăng nhập lại."
        if not valid:
            self.studio.identity = None
            if isinstance(identity, License):
                self.window.stack.setCurrentWidget(self.window.activation_page)
                self.window.activation_page.toast.show_message(message, "error", duration_ms=0)
            else:
                self.window.stack.setCurrentWidget(self.window.login_page)
                self.window.login_page.toast.show_message(message, "error", duration_ms=0)

    def can_close(self) -> bool:
        return not (
            self.login_controller.worker
            or self.restore_worker
            or self.activation_controller.worker
            or (self.studio and self.studio.busy())
        )

    def run(self, smoke_test: bool = False, showcase: bool = False) -> int:
        if showcase:
            from app.ui.pages.component_showcase import ComponentShowcase

            self.window.setCentralWidget(ComponentShowcase(self.window))
        self.window.show()
        if smoke_test:
            QTimer.singleShot(250, self.window.close)
        return self.qt.exec()
