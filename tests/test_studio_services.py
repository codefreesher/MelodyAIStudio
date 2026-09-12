"""Functional checks for creative outputs, SQLite, vault and update safety."""

import hashlib
import json
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import httpx

from app.database.database import Database
from app.database.repositories.history_repository import HistoryRepository
from app.database.repositories.settings_repository import SettingsRepository
from app.providers.online.provider_manager import ProviderManager
from app.resources_manager.extractor import extract_zip
from app.security.credential_vault import CredentialVault
from app.services.ai_service import AIService
from app.services.download_service import DownloadService
from app.services.provider_config_service import ProviderConfigService
from app.services.resource_service import ResourceService
from app.updater.installer import launch_installer
from app.updater.update_checker import select_release


class StudioServicesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = Database(self.root / "test.db")
        self.history = HistoryRepository(self.db)

    def tearDown(self):
        self.temp.cleanup()

    def test_creative_outputs_history_and_export(self):
        for kind in ("music", "lyric", "audio", "image"):
            service = AIService(kind, self.root, ProviderManager(), self.history)
            service.prepare()
            result = service.generate("Test melody", {"count": "2"})
            self.assertTrue(all(path.is_file() for path in result.paths))
            if kind == "image":
                self.assertEqual(result.paths[0].read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            if kind == "music":
                self.assertTrue(result.metadata["waveform"])
            service.save(result)
            service.save(result)
            export = self.root / ("export-" + kind)
            service.download(result, export)
            self.assertTrue((export / result.paths[0].name).exists())
        self.assertEqual(self.history.list()[1], 4)
        self.assertEqual(self.history.list(kind="lyric")[1], 1)
        self.assertEqual(self.history.list(search="' OR 1=1 --")[1], 0)
        row = self.history.list()[0][0]
        self.history.delete(row["uuid"])
        self.assertTrue(Path(row["result_path"]).exists())
        self.assertEqual(self.history.list()[1], 3)

    def test_cancellation_and_permission(self):
        service = AIService("music", self.root, ProviderManager(), self.history)
        service.cancel()
        with self.assertRaisesRegex(ValueError, "hủy"):
            service.generate("x", {})
        self.assertEqual(self.history.list()[1], 0)
        service.authorize = lambda: (_ for _ in ()).throw(ValueError("denied"))
        with self.assertRaisesRegex(ValueError, "denied"):
            service.generate("x", {})

    def test_vault_no_plaintext_in_database_or_file(self):
        vault = CredentialVault(self.root / "vault")
        vault.backend = None
        service = ProviderConfigService(SettingsRepository(self.db), vault)
        secret = "secret-test-key-123"
        service.save(
            "OpenAI", {"api_key": secret, "base_url": "https://example.com", "model": "test", "enabled": True}
        )
        self.assertEqual(service.load("OpenAI")["api_key"], secret)
        self.assertNotIn(secret.encode(), self.db.path.read_bytes())
        for file in vault.root.iterdir():
            self.assertNotIn(secret.encode(), file.read_bytes())
        vault.delete("OpenAI")
        self.assertEqual(vault.get("OpenAI"), "")

    def test_download_integrity_and_cancellation(self):
        data = b"artifact-data"
        digest = hashlib.sha256(data).hexdigest()
        real_client = httpx.Client

        def factory(**kwargs):
            return real_client(
                transport=httpx.MockTransport(lambda request: httpx.Response(200, content=data)), **kwargs
            )

        target = self.root / "artifact.zip"
        with patch("app.services.download_service.httpx.Client", side_effect=factory):
            progress = []
            DownloadService().download("https://example.com/a", target, digest, progress.append)
            self.assertEqual(progress[-1], 100)
            target.write_bytes(b"old")
            with self.assertRaises(ValueError):
                DownloadService().download("https://example.com/a", target, "0" * 64)
            self.assertEqual(target.read_bytes(), b"old")
            cancel = threading.Event()
            cancel.set()
            with self.assertRaises(ValueError):
                DownloadService().download("https://example.com/a", target, digest, cancel=cancel)
        self.assertFalse(target.with_suffix(".zip.part").exists())

    def test_zip_traversal_and_install(self):
        archive = self.root / "bad.zip"
        with zipfile.ZipFile(archive, "w") as source:
            source.writestr("../escape", b"bad")
        with self.assertRaises(ValueError):
            extract_zip(archive, self.root / "out")
        self.assertFalse((self.root / "escape").exists())
        download = self.root / "downloads"
        download.mkdir()
        archive = download / "demo.zip"
        with zipfile.ZipFile(archive, "w") as source:
            source.writestr("bin/tool.exe", b"demo executable fixture")
        item = {
            "id": "demo",
            "name": "Demo",
            "url": "https://example.com/demo.zip",
            "archive_type": "zip",
            "version": "1",
            "executable": "bin/tool.exe",
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        }
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps([item]))
        service = ResourceService(self.root / "resources", download, manifest)
        service.perform(item, "install")
        self.assertTrue(service.list()[0]["installed"])
        service.perform(item, "remove")
        self.assertFalse(service.list()[0]["installed"])

    def test_release_validation(self):
        asset = {
            "name": "MelodyAI-Setup-0.2.0.exe",
            "digest": "sha256:" + "a" * 64,
            "browser_download_url": "https://github.com/a/b/releases/download/v0.2.0/MelodyAI-Setup-0.2.0.exe",
        }
        release = {"tag_name": "v0.2.0", "assets": [asset], "body": "Changes"}
        self.assertEqual(select_release(release, "0.1.0").version, "0.2.0")
        self.assertIsNone(select_release(release, "0.3.0"))
        self.assertIsNone(select_release(dict(release, prerelease=True), "0.1.0"))
        asset["digest"] = None
        with self.assertRaises(ValueError):
            select_release(release, "0.1.0")
        target = self.root / "installer.exe"
        target.write_bytes(b"wrong")
        with patch("app.updater.installer.subprocess.Popen") as execute:
            with self.assertRaises(ValueError):
                launch_installer(target, "0" * 64)
            execute.assert_not_called()
