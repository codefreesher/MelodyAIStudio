"""User-controlled download/install and automatic metadata checking."""

import threading
from pathlib import Path

from app.services.download_service import DownloadService
from app.updater.github_client import GitHubClient
from app.updater.installer import launch_installer
from app.updater.update_checker import Release, select_release


class UpdateService:
    def __init__(self, version: str, folder: Path, settings) -> None:
        self.version, self.folder, self.settings = version, folder, settings
        self.cancel_event = threading.Event()

    def check(self, owner: str, repository: str) -> Release | None:
        self.settings.set("github", {"owner": owner, "repository": repository})
        return select_release(GitHubClient().latest(owner, repository), self.version)

    def download(self, release: Release, progress=lambda value: None) -> Path:
        return DownloadService().download(
            release.url, self.folder / release.name, release.sha256, progress, self.cancel_event
        )

    def install(self, release: Release) -> None:
        launch_installer(self.folder / release.name, release.sha256)
