"""Ed25519 end-to-end verification using disposable admin keypairs."""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from admin_tools.key_generator import generate_keypair, generate_license
from app.core.exceptions import LicenseError
from app.security.license_manager import LicenseManager
from app.security.license_verifier import LicenseVerifier
from app.security.machine_id import normalize_machine_id


class LicenseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.private = self.root / "private/key.pem"
        self.public = self.root / "public/key.pem"
        generate_keypair(self.private, self.public)
        self.verifier = LicenseVerifier(self.public)
        self.machine = normalize_machine_id("a" * 32)
        self.now = datetime.now(timezone.utc)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def token(self, plan: str = "PRO", expired: bool = False) -> str:
        return generate_license(
            self.private,
            self.machine,
            plan,
            None if plan == "LIFETIME" else self.now + timedelta(days=-1 if expired else 30),
            ["music", "lyric"],
            self.now - timedelta(days=2),
        )

    def test_valid(self) -> None:
        self.assertEqual(self.verifier.verify(self.token(), self.machine).plan, "PRO")

    def test_machine_mismatch(self) -> None:
        with self.assertRaisesRegex(LicenseError, "máy này"):
            self.verifier.verify(self.token(), normalize_machine_id("b" * 32))

    def test_invalid_signature(self) -> None:
        parts = self.token().split(".")
        parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
        with self.assertRaisesRegex(LicenseError, "Chữ ký"):
            self.verifier.verify(".".join(parts), self.machine)

    def test_expired(self) -> None:
        with self.assertRaisesRegex(LicenseError, "hết hạn"):
            self.verifier.verify(self.token(expired=True), self.machine)

    def test_lifetime(self) -> None:
        license = self.verifier.verify(self.token("LIFETIME"), self.machine, self.now + timedelta(days=36500))
        self.assertIsNone(license.expires_at)

    def test_persistence_and_invalid_does_not_replace(self) -> None:
        manager = LicenseManager(self.verifier, self.machine, self.root / "license.token")
        original = manager.activate(self.token())
        with self.assertRaises(LicenseError):
            manager.activate("invalid")
        self.assertEqual(manager.load(), original)
        self.assertFalse((self.root / "license.tmp").exists())

    def test_no_overwrite_keypair(self) -> None:
        original = self.private.read_bytes()
        with self.assertRaises(ValueError):
            generate_keypair(self.private, self.public)
        self.assertEqual(original, self.private.read_bytes())

    def test_missing_public_key(self) -> None:
        with self.assertRaisesRegex(LicenseError, "public key"):
            LicenseVerifier(self.root / "missing.pem").verify(self.token(), self.machine)
