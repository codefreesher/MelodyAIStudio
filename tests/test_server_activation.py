"""Admin-server activation and heartbeat contract tests."""

import json
import platform
import tempfile
import unittest
from pathlib import Path

import httpx
from PySide6.QtCore import QThreadPool
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.api.api_client import ApiClient, ApiError
from app.api.device_api import DeviceApi
from app.api.license_api import LicenseApi
from app.core.config import AppConfig
from app.security.credential_vault import CredentialVault
from app.security.device_session import DeviceSessionStore
from app.services.activation_service import DEVICE_TOKEN_KEY, ActivationService
from app.services.device_info_service import DeviceInfoService
from app.services.heartbeat_service import HeartbeatService


class StubDeviceInfo:
    def activation_payload(self) -> dict[str, str]:
        return {
            "device_name": "Test PC", "hostname": "test-pc", "os_name": "TestOS",
            "os_version": "1", "architecture": "x64", "app_version": "1.2.3",
        }


class ServerActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.vault = CredentialVault(root / "vault")
        self.store = DeviceSessionStore(root / "activation.json")

    def tearDown(self) -> None:
        QThreadPool.globalInstance().waitForDone(3000)
        self.temp.cleanup()

    def test_production_server_is_the_default(self) -> None:
        self.assertEqual(AppConfig().api_base_url, "https://agri.tainguyenso.vn/api/v1")

    def test_device_fields_respect_server_limits(self) -> None:
        info = DeviceInfoService("1.2.3").collect()
        for field in ("os_name", "os_version", "architecture", "app_version"):
            self.assertLessEqual(len(info[field]), 50)
        self.assertEqual(info["os_version"], platform.version().strip()[:50])

    def test_activate_persists_metadata_but_not_plaintext_token(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            self.assertEqual(request.url.path, "/api/v1/license/activate")
            self.assertEqual(payload["machine_id"], "AAAA-BBBB-CCCC-DDDD-EEEE-FFFF-0000-1111")
            return httpx.Response(200, json={"data": {
                "device_token": "secret-device-token", "device_uuid": "device-1",
                "license_id": "license-1", "plan": "CREATOR",
                "features": {"music": True, "lyrics": False, "audio": True, "image": False,
                             "online_ai": True, "offline_ai": False},
                "expires_at": None, "heartbeat_interval": 10,
            }})

        http = httpx.Client(transport=httpx.MockTransport(handler))
        service = ActivationService(
            LicenseApi(ApiClient("https://server.test/api/v1", client=http)),
            "AAAA-BBBB-CCCC-DDDD-EEEE-FFFF-0000-1111", StubDeviceInfo(), self.vault, self.store,
        )
        session = service.activate("KEY-123")
        self.assertEqual(session.heartbeat_interval, 30)
        self.assertEqual(self.vault.get(DEVICE_TOKEN_KEY), "secret-device-token")
        self.assertNotIn("secret-device-token", self.store.path.read_text(encoding="utf-8"))
        self.assertTrue(self.store.load().has_feature("music"))
        http.close()

    def test_activate_accepts_nested_laravel_response(self) -> None:
        http = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"data": {
            "device_token": "nested-secret", "device": {"uuid": "device-nested"},
            "license": {"id": 42, "expires_at": "2026-12-10T00:00:00Z",
                        "plan": {"code": "PRO", "features": ["music", "online_ai"]}},
            "heartbeat_interval": 60,
        }})))
        result = ActivationService(
            LicenseApi(ApiClient("https://server.test/api/v1", client=http)), "machine",
            StubDeviceInfo(), self.vault, self.store,
        ).activate("KEY")
        self.assertEqual(result.device_uuid, "device-nested")
        self.assertEqual(result.license_id, "42")
        self.assertEqual(result.plan, "PRO")
        self.assertTrue(result.has_feature("music"))
        http.close()

    def test_session_accepts_scalar_ids_and_entitlement(self) -> None:
        from app.security.device_session import DeviceSession

        result = DeviceSession.from_response({
            "device_id": 8, "license": 19,
            "entitlement": {"plan": "STANDARD", "features": ["audio"], "expires_at": None},
        })
        self.assertEqual((result.device_uuid, result.license_id), ("8", "19"))
        self.assertTrue(result.has_feature("audio"))

    def test_error_mapping_hides_raw_json(self) -> None:
        http = httpx.Client(transport=httpx.MockTransport(
            lambda request: httpx.Response(403, json={"error": {"code": "DEVICE_BLOCKED", "debug": "raw"}})
        ))
        with self.assertRaisesRegex(ApiError, "Thiết bị đã bị chặn"):
            ApiClient("https://server.test", client=http).request("POST", "/x")
        http.close()

    def test_unauthenticated_heartbeat_is_a_revoked_device(self) -> None:
        http = httpx.Client(transport=httpx.MockTransport(
            lambda request: httpx.Response(401, json={"message": "Unauthenticated."})
        ))
        with self.assertRaisesRegex(ApiError, "Thiết bị đã bị thu hồi") as raised:
            DeviceApi(ApiClient("https://server.test", client=http)).heartbeat("old-token", "1", "os", "ok")
        self.assertEqual(raised.exception.code, "DEVICE_REVOKED")
        http.close()

    def test_heartbeat_revoke_clears_token_and_returns_activation_signal(self) -> None:
        http = httpx.Client(transport=httpx.MockTransport(
            lambda request: httpx.Response(403, json={"code": "DEVICE_REVOKED"})
        ))
        self.vault.set(DEVICE_TOKEN_KEY, "secret")
        session = ActivationService(
            LicenseApi(ApiClient("https://unused", client=http)), "machine", StubDeviceInfo(),
            self.vault, self.store,
        )
        # Seed metadata directly; activation itself is covered above.
        from app.security.device_session import DeviceSession

        metadata = DeviceSession("device-1", "license-1", "CREATOR", {"music": True})
        self.store.save(metadata)
        heartbeat = HeartbeatService(DeviceApi(ApiClient("https://server.test", client=http)), self.vault,
                                     self.store, "1.2.3")
        changes = []
        heartbeat.access_changed.connect(lambda code, message: changes.append(code))
        heartbeat.start(metadata, immediate=True)
        for _ in range(100):
            QTest.qWait(10)
            if heartbeat.worker is None:
                break
        self.assertEqual(changes, ["DEVICE_REVOKED"])
        self.assertEqual(self.vault.get(DEVICE_TOKEN_KEY), "")
        self.assertIsNone(self.store.load())
        self.assertIsNotNone(session)
        http.close()
