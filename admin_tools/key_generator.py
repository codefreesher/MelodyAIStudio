"""Admin-only Ed25519 key generation and license signing."""

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.models.license import License
from app.security.machine_id import normalize_machine_id


def generate_keypair(private_path: Path, public_path: Path) -> None:
    if private_path.exists() or public_path.exists():
        raise ValueError("Key đã tồn tại. Không ghi đè keypair đang sử dụng.")
    key = Ed25519PrivateKey.generate()
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    private = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    public = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    descriptor = os.open(private_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(private)
    with public_path.open("xb") as stream:
        stream.write(public)


def generate_license(
    private_path: Path,
    machine_id: str,
    plan: str,
    expires_at: datetime | None,
    features: list[str],
    issued_at: datetime | None = None,
) -> str:
    issued = issued_at or datetime.now(timezone.utc)
    payload = {
        "license_id": str(uuid4()),
        "machine_id": normalize_machine_id(machine_id),
        "plan": plan,
        "issued_at": issued.isoformat(),
        "expires_at": expires_at.isoformat() if expires_at else None,
        "features": features,
    }
    License.from_payload(payload)
    key = serialization.load_pem_private_key(private_path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("Private key phải là Ed25519.")
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = key.sign(b"MLAI1." + data)

    def encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    return f"MLAI1.{encode(data)}.{encode(signature)}"
