"""Registered-device endpoints."""

from typing import Any

from app.api.api_client import ApiClient, ApiError


class DeviceApi:
    def __init__(self, client: ApiClient) -> None:
        self.client = client

    def heartbeat(self, token: str, app_version: str, os_version: str, integrity_status: str) -> dict[str, Any]:
        try:
            return self.client.request("POST", "/device/heartbeat", token=token, payload={
                "app_version": app_version, "os_version": os_version, "integrity_status": integrity_status
            })
        except ApiError as error:
            # Sanctum rejects a removed/revoked device token before the controller
            # can return its domain-specific DEVICE_REVOKED code.
            if error.status_code == 401:
                raise ApiError("DEVICE_REVOKED", status_code=401) from error
            raise
