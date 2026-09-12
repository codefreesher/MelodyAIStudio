"""Composition root for stages 07–18. UI receives controllers, never providers."""

from PySide6.QtCore import QTimer, QUrl

from app.controllers.config_controller import ConfigController
from app.controllers.dashboard_controller import DashboardController
from app.controllers.generation_controller import GenerationController
from app.controllers.history_controller import HistoryController
from app.controllers.model_manager_controller import ModelManagerController
from app.controllers.profile_controller import ProfileController
from app.controllers.resource_controller import ResourceController
from app.controllers.settings_controller import SettingsController
from app.controllers.update_controller import UpdateController
from app.core.constants import UPDATE_OWNER, UPDATE_REPOSITORY
from app.database.database import Database
from app.database.repositories.history_repository import HistoryRepository
from app.database.repositories.settings_repository import SettingsRepository
from app.models.license import License
from app.models.user import User
from app.providers.online.provider_manager import ProviderManager
from app.resources_manager.process_manager import ProcessManager
from app.security.credential_vault import CredentialVault
from app.services.account_service import AccountService
from app.services.ai_service import AIService
from app.services.history_service import HistoryService
from app.services.offline_config_service import OfflineConfigService
from app.services.provider_config_service import ProviderConfigService
from app.services.resource_service import ResourceService
from app.services.settings_service import SettingsService
from app.services.update_service import UpdateService
from app.ui.pages.audio.audio_page import AudioPage
from app.ui.pages.dashboard.dashboard_page import DashboardPage
from app.ui.pages.generation_page import GenerationPage
from app.ui.pages.history.history_page import HistoryPage
from app.ui.pages.image.image_page import ImagePage
from app.ui.pages.lyric.lyric_page import LyricPage
from app.ui.pages.music.music_page import MusicPage
from app.ui.pages.offline_config.offline_config_page import OfflineConfigPage
from app.ui.pages.online_config.online_config_page import OnlineConfigPage
from app.ui.pages.resources.resource_page import ResourcePage
from app.ui.pages.settings.settings_page import SettingsPage
from app.ui.pages.updates.update_page import UpdatePage
from app.ui.studio_window import StudioWindow


class StudioRuntime:
    def __init__(self, application) -> None:
        self.application = application
        paths = application.paths
        database = Database(paths.database)
        self.settings = SettingsRepository(database)
        if self.settings.get("github") is None:
            self.settings.set(
                "github",
                {
                    "owner": application.config.github_owner,
                    "repository": application.config.github_repository,
                },
            )
        if self.settings.get("preferences") is None:
            self.settings.set(
                "preferences",
                {
                    "theme": application.config.theme,
                    "language": application.config.language,
                    "auto_update": application.config.check_updates_automatically,
                    "accent": "#FF4F9A",
                    "start_windows": False,
                },
            )
        self.history = HistoryService(HistoryRepository(database))
        vault = CredentialVault(paths.root / "config" / "vault")
        self.settings_service = SettingsService(self.settings, paths.root, application.sessions, vault)
        self.view = StudioWindow()
        self.profile_controller = ProfileController(
            self.view, self.view.sidebar, AccountService(application.auth_service.provider)
        )
        self.profile_controller.updated.connect(self.profile_updated)
        self.controllers = []
        self.generators = []
        self.identity = None
        from app.ui.translation import TranslationManager

        self.translation = TranslationManager(application.qt)
        self.dashboard = DashboardPage()
        self.dashboard_controller = DashboardController(self.dashboard, self.history)
        self.view.register("dashboard", self.dashboard)
        self.dashboard.navigate.connect(self.view.navigate)
        self.dashboard.search_requested.connect(self.search)
        providers = ProviderManager()
        for kind in ("music", "lyric", "audio", "image"):
            if kind == "music":
                page = MusicPage()
            elif kind == "lyric":
                page = LyricPage()
            elif kind == "audio":
                page = AudioPage()
            elif kind == "image":
                page = ImagePage()
            else:
                page = GenerationPage(kind)
            service = AIService(
                kind, self.settings_service.folder("projects"), providers, self.history.repository
            )
            service.authorize = lambda feature=kind: self.authorize(feature)
            controller = GenerationController(page, service)
            controller.saved.connect(self.dashboard_controller.refresh)
            self.controllers.append(controller)
            self.generators.append(controller)
            self.view.register(kind, page)
        self.history_page = HistoryPage()
        self.history_controller = HistoryController(self.history_page, self.history)
        self.controllers.append(self.history_controller)
        self.view.register("history", self.history_page)
        online = OnlineConfigPage()
        self.online_controller = ConfigController(online, ProviderConfigService(self.settings, vault))
        self.controllers.append(self.online_controller)
        self.view.register("online_config", online)
        offline = OfflineConfigPage()
        self.processes = ProcessManager()
        offline_service = OfflineConfigService(self.settings, self.processes)
        self.offline_controller = ConfigController(offline, offline_service)
        self.controllers.append(self.offline_controller)
        self.model_manager_controller = ModelManagerController(offline, offline_service)
        self.controllers.append(self.model_manager_controller)
        self.view.register("offline_config", offline)
        resources = ResourcePage()
        self.resource_controller = ResourceController(
            resources,
            ResourceService(
                paths.root / "resources",
                self.settings_service.folder("downloads"),
                paths.root / "config/resources.json",
            ),
        )
        self.controllers.append(self.resource_controller)
        self.view.register("resources", resources)
        settings_page = SettingsPage()
        self.settings_controller = SettingsController(
            settings_page, self.settings_service, application.theme_manager
        )
        self.settings_controller.can_logout = lambda: not self.busy()
        self.settings_controller.logged_out.connect(self.logout)
        self.settings_controller.changed.connect(self.preferences_changed)
        self.controllers.append(self.settings_controller)
        self.view.register("settings", settings_page)
        updates = UpdatePage(application.qt.applicationVersion())
        # A developer override (config/app.json) still wins over the
        # built-in default — see app/core/constants.py.
        update_owner = application.config.github_owner or UPDATE_OWNER
        update_repository = application.config.github_repository or UPDATE_REPOSITORY
        self.update_controller = UpdateController(
            updates,
            UpdateService(
                application.qt.applicationVersion(), self.settings_service.folder("downloads"), self.settings
            ),
            update_owner,
            update_repository,
        )
        self.update_controller.can_install = lambda: not self.busy()
        self.update_controller.installer_started.connect(application.window.close)
        self.controllers.append(self.update_controller)
        self.view.register("updates", updates)
        self.view.route_changed.connect(self.refresh)
        self.preferences_changed()

    def enter(self, identity) -> None:
        self.identity = identity
        username = getattr(identity, "username", "Bạn")
        self.view.sidebar.set_profile(username, identity.plan, isinstance(identity, User))
        self.profile_controller.set_user(identity if isinstance(identity, User) else None)
        self.dashboard.greeting.setText(f"Xin chào, {username}!")
        self.view.navigate("dashboard")
        preferences = self.settings_service.load()
        if preferences.get("auto_update") and self.update_controller.owner and self.update_controller.repository:
            QTimer.singleShot(1000, self.update_controller.check)

    def profile_updated(self, user: User) -> None:
        self.identity = user
        self.application.sessions.current_user = user
        self.view.sidebar.set_profile(user.username, user.plan, True)
        self.dashboard.greeting.setText(f"Xin chào, {user.username}!")

    def authorize(self, feature: str) -> None:
        if isinstance(self.identity, License):
            license = self.application.license_manager.load()
            if license is None or feature not in license.features:
                raise ValueError("License không bao gồm tính năng này hoặc đã hết hiệu lực.")
        elif self.identity is None:
            raise ValueError("Vui lòng đăng nhập trước.")

    def refresh(self, route: str) -> None:
        self.translation.apply(self.settings_service.load().get("language", "vi"))
        if route == "dashboard":
            self.dashboard_controller.refresh()
        elif route == "history":
            self.history_controller.refresh()
        elif route == "resources":
            self.resource_controller.refresh()
        elif route == "online_config":
            self.online_controller.load(self.online_controller.page.current())
        elif route == "offline_config":
            self.offline_controller.load(self.offline_controller.page.current())

    def search(self, text: str) -> None:
        self.history_page.search.setText(text)
        self.history_controller.reset()
        self.view.navigate("history")

    def preferences_changed(self) -> None:
        preferences = self.settings_service.load()
        self.translation.apply(preferences.get("language", "vi"))
        self.application.theme_manager.apply(
            preferences.get("theme", "pink_light"), preferences.get("accent")
        )
        for controller in self.generators:
            controller.service.root = self.settings_service.folder("projects")
        self.resource_controller.service.downloads = self.settings_service.folder("downloads")
        self.update_controller.service.folder = self.settings_service.folder("downloads")

    def busy(self) -> bool:
        return any(getattr(controller, "worker", None) is not None for controller in self.controllers)

    def logout(self) -> None:
        if self.busy():
            self.settings_controller.page.toast.show_message("Chờ tác vụ kết thúc trước khi đăng xuất.")
            return
        if not isinstance(self.identity, License):
            self.application.sessions.clear()
        self.identity = None
        for controller in self.generators:
            if controller.page.player:
                controller.page.player.media.stop()
                controller.page.player.media.setSource(QUrl())
        self.application.window.show_startup()

    def release_media(self) -> None:
        for controller in self.generators:
            if controller.page.player:
                controller.page.player.media.stop()
                controller.page.player.media.setSource(QUrl())
