"""Run only the downloaded installer after verifying it again."""

import subprocess
import sys
from pathlib import Path

from app.services.download_service import verify_sha256


def launch_installer(path: Path, sha256: str) -> None:
    verify_sha256(path, sha256)
    if sys.platform != "win32":
        raise ValueError("Cài update EXE chỉ thực hiện trên Windows.")
    if path.suffix.lower() != ".exe":
        raise ValueError("Installer phải là EXE.")
    subprocess.Popen([str(path.resolve()), "/NORESTART"], shell=False)
