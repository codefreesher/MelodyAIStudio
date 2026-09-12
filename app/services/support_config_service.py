"""Load public support links from the MelodyAI web backend."""

from dataclasses import dataclass
from urllib.parse import urlparse

import httpx


@dataclass(frozen=True)
class SupportLinks:
    telegram_url: str = ""
    zalo_url: str = ""


class SupportConfigService:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.strip().rstrip("/")

    def fetch(self) -> SupportLinks:
        if not self.base_url:
            return SupportLinks()
        response = httpx.get(
            f"{self.base_url}/api/v1/public/app-config",
            timeout=10,
            follow_redirects=False,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Invalid backend configuration")
        support = payload.get("support", {})
        if not isinstance(support, dict):
            raise ValueError("Invalid support configuration")
        return SupportLinks(
            telegram_url=self._public_url(support.get("telegram_url")),
            zalo_url=self._public_url(support.get("zalo_url")),
        )

    @staticmethod
    def _public_url(value: object) -> str:
        if not isinstance(value, str):
            return ""
        url = value.strip()
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            return ""
        return url
