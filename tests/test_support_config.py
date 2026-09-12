"""Public backend support-link contract."""

import unittest
from unittest.mock import Mock, patch

from app.services.support_config_service import SupportConfigService, SupportLinks


class SupportConfigTests(unittest.TestCase):
    def test_empty_backend_disables_links_without_request(self) -> None:
        with patch("app.services.support_config_service.httpx.get") as get:
            self.assertEqual(SupportConfigService("").fetch(), SupportLinks())
            get.assert_not_called()

    def test_reads_https_support_links(self) -> None:
        response = Mock()
        response.json.return_value = {
            "support": {
                "telegram_url": "https://t.me/melodyai_support",
                "zalo_url": "https://zalo.me/0123456789",
            }
        }
        with patch("app.services.support_config_service.httpx.get", return_value=response):
            links = SupportConfigService("https://api.melodyai.local/").fetch()
        self.assertEqual(links.telegram_url, "https://t.me/melodyai_support")
        self.assertEqual(links.zalo_url, "https://zalo.me/0123456789")
        response.raise_for_status.assert_called_once_with()

    def test_rejects_non_https_and_credential_urls(self) -> None:
        response = Mock()
        response.json.return_value = {
            "support": {
                "telegram_url": "http://t.me/unsafe",
                "zalo_url": "https://user:password@zalo.me/unsafe",
            }
        }
        with patch("app.services.support_config_service.httpx.get", return_value=response):
            self.assertEqual(SupportConfigService("https://api.example.com").fetch(), SupportLinks())


if __name__ == "__main__":
    unittest.main()
