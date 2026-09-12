"""Explicit development authentication, replaceable by a backend adapter."""

import hmac
from dataclasses import replace

from app.core.exceptions import AuthenticationError
from app.models.user import User


class MockAuthProvider:
    def __init__(self) -> None:
        self._password = b"123456"
        self._username = "demo"

    def authenticate(self, identifier: str, password: str) -> User:
        valid_user = identifier.casefold() in ("demo@melodyai.local", "demo")
        valid_password = hmac.compare_digest(password.encode(), self._password)
        if not (valid_user and valid_password):
            raise AuthenticationError("Tài khoản hoặc mật khẩu không đúng.")
        return User("mock-demo", self._username, "demo@melodyai.local")

    def restore_session(self, identifier: str) -> User:
        """Development equivalent of validating a backend refresh session."""
        if identifier.casefold() not in ("demo@melodyai.local", "demo"):
            raise AuthenticationError("Phiên đăng nhập không còn hợp lệ.")
        return User("mock-demo", self._username, "demo@melodyai.local")

    def update_profile(self, user: User, username: str, current_password: str, new_password: str) -> User:
        if not hmac.compare_digest(current_password.encode(), self._password):
            raise AuthenticationError("Mật khẩu hiện tại không đúng.")
        self._username = username
        if new_password:
            self._password = new_password.encode()
        return replace(user, username=username)
