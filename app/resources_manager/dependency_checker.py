"""Detect local engines without collecting unnecessary hardware data."""

import shutil
import sys
from pathlib import Path


class DependencyChecker:
    def __init__(self, resources_root: Path, downloads: Path) -> None:
        self.resources_root, self.downloads = resources_root, downloads

    def status(self, resource_id: str) -> str:
        installed = self.resources_root / resource_id / ".installed"
        if installed.exists():
            return "installed"
        checks = {
            "ollama": lambda: bool(shutil.which("ollama")),
            "ffmpeg": lambda: bool(shutil.which("ffmpeg")),
            "python": lambda: bool(sys.executable),
            "stable-diffusion": lambda: any(
                (self.resources_root / "stable-diffusion").glob("**/webui-user.bat")
            ),
            "tts-models": lambda: any((self.resources_root / "tts-models").glob("**/*.onnx")),
        }
        return "installed" if checks.get(resource_id, lambda: False)() else "missing"
