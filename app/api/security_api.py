"""Reserved API boundary for security-event reporting in a later stage."""

from app.api.api_client import ApiClient


class SecurityApi:
    def __init__(self, client: ApiClient) -> None:
        self.client = client
