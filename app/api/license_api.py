"""License activation endpoint."""

from typing import Any

from app.api.api_client import ApiClient


class LicenseApi:
    def __init__(self, client: ApiClient) -> None:
        self.client = client

    def activate(self, license_key: str, machine_id: str, device_info: dict[str, str]) -> dict[str, Any]:
        return self.client.request(
            "POST", "/license/activate", payload={"license_key": license_key, "machine_id": machine_id, **device_info}
        )
