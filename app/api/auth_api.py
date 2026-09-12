"""Account authentication endpoint boundary (kept separate from activation)."""

from typing import Any

from app.api.api_client import ApiClient


class AuthApi:
    def __init__(self, client: ApiClient) -> None:
        self.client = client

    def login(self, identifier: str, password: str) -> dict[str, Any]:
        return self.client.request("POST", "/auth/login", payload={"identifier": identifier, "password": password})
