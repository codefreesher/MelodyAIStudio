"""Account profile orchestration independent of Qt widgets."""

from typing import Protocol

from app.core.exceptions import AuthenticationError
from app.models.user import User


class AccountProvider(Protocol):
    def update_profile(self, user: User, username: str, current_password: str, new_password: str) -> User: ...


class AccountService:
    def __init__(self, provider: AccountProvider) -> None:
        self.provider = provider

    def update(self, user: User, values: dict) -> User:
        username = str(values.get("username", "")).strip()
        current_password = str(values.get("current_password", ""))
        new_password = str(values.get("new_password", ""))
        confirmation = str(values.get("confirm_password", ""))
        if len(username) < 2 or len(username) > 40:
            raise AuthenticationError("Tên tài khoản phải có từ 2 đến 40 ký tự.")
        if not current_password:
            raise AuthenticationError("Vui lòng nhập mật khẩu hiện tại.")
        if new_password and len(new_password) < 6:
            raise AuthenticationError("Mật khẩu mới phải có ít nhất 6 ký tự.")
        if new_password != confirmation:
            raise AuthenticationError("Mật khẩu xác nhận không khớp.")
        return self.provider.update_profile(user, username, current_password, new_password)
