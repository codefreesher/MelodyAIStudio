"""Development session abstraction; persisted data is not an auth token.

Only a non-secret mock account identifier is remembered. Real backend tokens
must use the credential vault when backend authentication is introduced.
"""

import json
from pathlib import Path
from typing import Protocol

from app.models.user import User


class SessionStore(Protocol):
    def save(self, identifier: str) -> None: ...
    def load(self) -> str | None: ...
    def clear(self) -> None: ...


class JsonSessionStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def save(self, identifier: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        try:
            temporary.write_text(json.dumps({"mock_identifier": identifier}), encoding="utf-8")
            temporary.replace(self.path)
        finally:
            temporary.unlink(missing_ok=True)

    def load(self) -> str | None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeError):
            return None
        if not isinstance(data, dict):
            return None
        value = data.get("mock_identifier")
        return value if isinstance(value, str) else None

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)


class SessionManager:
    def __init__(self, store: SessionStore | None = None) -> None:
        self.store = store
        self.current_user: User | None = None

    def start(self, user: User, remember: bool) -> None:
        if self.store:
            if remember:
                self.store.save(user.email)
            else:
                self.store.clear()
        self.current_user = user

    def remembered_identifier(self) -> str | None:
        return self.store.load() if self.store else None

    def clear(self) -> None:
        if self.store:
            self.store.clear()
        self.current_user = None
