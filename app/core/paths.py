"""Separate read-only application files from writable user data."""

import sys
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_data_path

from app.core.constants import APP_NAME


def bundle_root() -> Path:
    """Support source execution and a future PyInstaller bundle."""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))


@dataclass(frozen=True)
class AppPaths:
    root: Path

    @classmethod
    def default(cls) -> "AppPaths":
        return cls(user_data_path(APP_NAME, appauthor=False, roaming=False))

    @property
    def config_file(self) -> Path:
        return self.root / "config" / "app.json"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def database(self) -> Path:
        return self.root / "data" / "melody.db"

    def ensure_directories(self) -> None:
        for name in (
            "config",
            "data",
            "projects",
            "music",
            "lyrics",
            "audio",
            "images",
            "thumbnails",
            "downloads",
            "resources",
            "models",
            "cache",
            "logs",
        ):
            (self.root / name).mkdir(parents=True, exist_ok=True)
