"""User preferences, storage locations and maintenance operations."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from app.database.repositories.settings_repository import SettingsRepository
from app.security.credential_vault import CredentialVault
from app.security.session_manager import SessionManager
from app.services.provider_config_service import PROVIDERS


class SettingsService:
    def __init__(
        self, settings: SettingsRepository, root: Path, sessions: SessionManager, vault: CredentialVault
    ) -> None:
        self.settings, self.root, self.sessions, self.vault = settings, root, sessions, vault

    def load(self, name: str = "") -> dict:
        return self.settings.get(
            "preferences",
            {
                "theme": "pink_light",
                "accent": "#FF4F9A",
                "language": "vi",
                "auto_update": True,
                "start_windows": False,
            },
        )

    def save(self, name: str, data: dict) -> str:
        if data.get("theme") not in ("pink_light", "pink_dark", "system"):
            raise ValueError("Theme không hợp lệ.")
        if data.get("language") not in ("vi", "en"):
            raise ValueError("Ngôn ngữ không hợp lệ.")
        if data.get("start_windows"):
            if sys.platform != "win32" or not getattr(sys, "frozen", False):
                raise ValueError("Start with Windows cần bản EXE đã cài trên Windows.")
        if sys.platform == "win32":
            import winreg

            with winreg.CreateKey(
                winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"
            ) as key:
                if data.get("start_windows"):
                    winreg.SetValueEx(
                        key, "MelodyAI", 0, winreg.REG_SZ, subprocess.list2cmdline([sys.executable])
                    )
                else:
                    try:
                        winreg.DeleteValue(key, "MelodyAI")
                    except FileNotFoundError:
                        pass
        self.settings.set("preferences", data)
        return "Đã lưu cài đặt."

    def folder(self, name: str) -> Path:
        return Path(self.settings.get("path:" + name, str(self.root / name)))

    def set_folder(self, name: str, path: Path) -> None:
        if name not in ("projects", "downloads", "models", "cache"):
            raise ValueError("Loại thư mục không hợp lệ.")
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=path):
            pass
        self.settings.set("path:" + name, str(path.resolve()))

    def clear_cache(self) -> str:
        # Never recursively delete a user-selected arbitrary directory.
        cache = self.folder("cache") / "MelodyAI-cache"
        if cache.exists():
            shutil.rmtree(cache)
        return "Đã xóa cache do MelodyAI quản lý."

    def clear_credentials(self) -> str:
        for provider in PROVIDERS:
            self.vault.delete(provider)
        return "Đã xóa credentials."

    def clear_session(self) -> str:
        self.sessions.clear()
        return "Đã xóa session."
