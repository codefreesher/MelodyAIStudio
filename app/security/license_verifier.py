"""Ed25519 verification only. No private key operations exist in desktop."""

import base64
import binascii
import json
from datetime import datetime, timezone
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.core.exceptions import LicenseError
from app.models.license import License, parse_timestamp
from app.security.machine_id import normalize_machine_id


def decode_part(value: str) -> bytes:
    return base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)


class LicenseVerifier:
    def __init__(self, public_key_path: Path) -> None:
        self.public_key_path = public_key_path

    def verify(self, token: str, machine_id: str, now: datetime | None = None) -> License:
        try:
            public_key = serialization.load_pem_public_key(self.public_key_path.read_bytes())
            if not isinstance(public_key, Ed25519PublicKey):
                raise ValueError("Wrong key type")
        except (OSError, ValueError) as exc:
            raise LicenseError("Chưa có public key hợp lệ. Vui lòng liên hệ Admin.") from exc
        try:
            if not isinstance(token, str) or len(token) > 16384:
                raise ValueError("Invalid token size")
            prefix, payload_part, signature_part = token.strip().split(".")
            if prefix != "MLAI1":
                raise ValueError("Unsupported license format")
            payload = decode_part(payload_part)
            signature = decode_part(signature_part)
            public_key.verify(signature, b"MLAI1." + payload)
            license = License.from_payload(json.loads(payload))
        except InvalidSignature as exc:
            raise LicenseError("Chữ ký license không hợp lệ.") from exc
        except (ValueError, TypeError, KeyError, AttributeError, binascii.Error, UnicodeError) as exc:
            raise LicenseError("License không đúng định dạng.") from exc
        try:
            expected = normalize_machine_id(machine_id)
        except ValueError as exc:
            raise LicenseError("Machine ID không hợp lệ.") from exc
        if license.machine_id != expected:
            raise LicenseError("License không dành cho máy này.")
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError("Verification clock must include timezone")
        if parse_timestamp(license.issued_at) > current:
            raise LicenseError("License chưa có hiệu lực. Kiểm tra ngày giờ hệ thống.")
        if license.expires_at is not None and parse_timestamp(license.expires_at) <= current:
            raise LicenseError("License đã hết hạn.")
        return license
