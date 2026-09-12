"""Persist signed license tokens only after verification; reverify on load."""

from pathlib import Path

from app.core.exceptions import LicenseError
from app.models.license import License
from app.security.license_verifier import LicenseVerifier


class LicenseManager:
    def __init__(self, verifier: LicenseVerifier, machine_id: str, path: Path) -> None:
        self.verifier, self.machine_id, self.path = verifier, machine_id, path

    def activate(self, token: str) -> License:
        license = self.verifier.verify(token, self.machine_id)
        temporary = self.path.with_suffix(".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(token.strip(), encoding="utf-8")
            temporary.replace(self.path)
        except OSError as exc:
            raise LicenseError("Không thể lưu license trên máy này.") from exc
        finally:
            temporary.unlink(missing_ok=True)
        return license

    def load(self) -> License | None:
        try:
            token = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except (OSError, UnicodeError) as exc:
            raise LicenseError("Không thể đọc license đã lưu.") from exc
        return self.verifier.verify(token, self.machine_id)
