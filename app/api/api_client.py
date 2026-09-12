"""Shared HTTP client with safe, localized server-error mapping."""

from __future__ import annotations

from typing import Any

import httpx

ERROR_MESSAGES = {
    "LICENSE_INVALID": "License không hợp lệ",
    "LICENSE_REVOKED": "License đã bị thu hồi",
    "LICENSE_EXPIRED": "License đã hết hạn",
    "MACHINE_MISMATCH": "License không thuộc thiết bị này",
    "USER_LOCKED": "Tài khoản đã bị khóa",
    "DEVICE_LIMIT_REACHED": "Đã vượt số lượng thiết bị",
    "DEVICE_BLOCKED": "Thiết bị đã bị chặn",
    "DEVICE_REVOKED": "Thiết bị đã bị thu hồi",
    "PLAN_DISABLED": "Gói sử dụng không còn hiệu lực",
}


class ApiError(Exception):
    def __init__(self, code: str, message: str | None = None, status_code: int | None = None) -> None:
        self.code = code
        self.status_code = status_code
        super().__init__(ERROR_MESSAGES.get(code, message or "Máy chủ không thể xử lý yêu cầu."))


class ApiClient:
    def __init__(self, base_url: str, timeout: float = 15.0, client: httpx.Client | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = client

    def request(
        self, method: str, path: str, *, payload: dict[str, Any] | None = None, token: str = ""
    ) -> dict[str, Any]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            client = self._client or httpx.Client(timeout=self.timeout)
            response = client.request(method, f"{self.base_url}/{path.lstrip('/')}", json=payload, headers=headers)
        except httpx.RequestError as exc:
            raise ApiError("NETWORK_ERROR", "Không thể kết nối máy chủ.") from exc
        finally:
            if self._client is None and "client" in locals():
                client.close()
        try:
            body = response.json()
        except ValueError as exc:
            raise ApiError("INVALID_RESPONSE", "Phản hồi máy chủ không hợp lệ.", response.status_code) from exc
        if not isinstance(body, dict):
            raise ApiError("INVALID_RESPONSE", "Phản hồi máy chủ không hợp lệ.", response.status_code)
        if response.is_error or body.get("success") is False:
            error = body.get("error")
            if isinstance(error, dict):
                code, message = error.get("code"), error.get("message")
            else:
                code, message = body.get("code"), body.get("message")
            raise ApiError(
                code if isinstance(code, str) else f"HTTP_{response.status_code}",
                message if isinstance(message, str) else None,
                response.status_code,
            )
        data = body.get("data", body)
        if not isinstance(data, dict):
            raise ApiError("INVALID_RESPONSE", "Phản hồi máy chủ không hợp lệ.", response.status_code)
        return data
