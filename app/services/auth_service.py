"""Authentication orchestration independent of Qt and provider details."""

from datetime import datetime, timezone
from typing import Protocol

from app.core.exceptions import AuthenticationError
from app.models.user import User
from app.security.session_manager import SessionManager


class AuthProvider(Protocol):
    def authenticate(self, identifier: str, password: str) -> User: ...
    def restore_session(self, identifier: str) -> User: ...


class AuthService:
    def __init__(self, provider: AuthProvider, sessions: SessionManager) -> None:
        self.provider = provider
        self.sessions = sessions

    def login(self, identifier: str, password: str, remember: bool = False) -> User:
        identifier = identifier.strip()
        if not identifier or not password:
            raise AuthenticationError("Vui lòng nhập tài khoản và mật khẩu.")
        user = self.provider.authenticate(identifier, password)
        self._ensure_active(user)
        try:
            self.sessions.start(user, remember)
        except OSError as exc:
            raise AuthenticationError("Không thể lưu phiên đăng nhập. Vui lòng thử lại.") from exc
        return user

    def restore_session(self) -> User | None:
        identifier = self.sessions.remembered_identifier()
        if not identifier:
            return None
        try:
            user = self.provider.restore_session(identifier)
            self._ensure_active(user)
        except Exception:
            self.sessions.clear()
            raise
        self.sessions.current_user = user
        return user

    def current_session_is_active(self) -> bool:
        user = self.sessions.current_user
        if user is None:
            return False
        try:
            self._ensure_active(user)
        except AuthenticationError:
            self.sessions.clear()
            return False
        return True

    @staticmethod
    def _ensure_active(user: User) -> None:
        if user.expires_at is None:
            return
        try:
            expiry = datetime.fromisoformat(user.expires_at.replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise AuthenticationError("Thời hạn tài khoản không hợp lệ.") from exc
        if expiry.tzinfo is None:
            raise AuthenticationError("Thời hạn tài khoản không hợp lệ.")
        if expiry.astimezone(timezone.utc) <= datetime.now(timezone.utc):
            raise AuthenticationError("Gói tài khoản đã hết hạn.")
