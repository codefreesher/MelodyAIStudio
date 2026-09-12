"""Persist provider metadata separately from secrets; explicit connection probes."""

from urllib.parse import urlparse

import httpx

from app.database.repositories.settings_repository import SettingsRepository
from app.security.credential_vault import CredentialVault

PROVIDERS = ["OpenAI", "Claude", "Gemini", "Suno", "Stability", "Khác"]


class ProviderConfigService:
    def __init__(self, settings: SettingsRepository, vault: CredentialVault) -> None:
        self.settings, self.vault = settings, vault

    def load(self, provider: str) -> dict:
        data = dict(self.settings.get("provider:" + provider, {}))
        data["api_key"] = self.vault.get(provider)
        return data

    def save(self, provider: str, data: dict) -> str:
        metadata = dict(data)
        secret = metadata.pop("api_key", "")
        url = metadata.get("base_url", "")
        if url and urlparse(url).scheme != "https":
            raise ValueError("Online provider phải dùng HTTPS.")
        if secret:
            self.vault.set(provider, secret)
        else:
            self.vault.delete(provider)
        self.settings.set("provider:" + provider, metadata)
        return "Đã lưu cấu hình provider."

    def test(self, provider: str, data: dict) -> str:
        url = data.get("base_url", "").strip().rstrip("/")
        if urlparse(url).scheme != "https":
            raise ValueError("Nhập Base URL HTTPS để kiểm tra.")
        # Probe base URL without sending credentials to an arbitrary configurable host.
        with httpx.Client(timeout=10, follow_redirects=False) as client:
            response = client.get(url)
        return f"Máy chủ phản hồi HTTP {response.status_code}. Đây là kiểm tra kết nối, chưa xác minh API key/model."
