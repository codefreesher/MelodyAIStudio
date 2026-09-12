"""Validated, immutable license claims shared by issuer and verifier."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.security.machine_id import normalize_machine_id

PLANS = ("TRIAL", "STANDARD", "PRO", "LIFETIME")
FEATURES = ("music", "lyric", "audio", "image", "offline")


def parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Timestamp must be text")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timezone is required")
    return result.astimezone(timezone.utc)


@dataclass(frozen=True)
class License:
    license_id: str
    machine_id: str
    plan: str
    issued_at: str
    expires_at: str | None
    features: tuple[str, ...]

    @classmethod
    def from_payload(cls, data: dict[str, Any]) -> "License":
        required = {"license_id", "machine_id", "plan", "issued_at", "expires_at", "features"}
        if not isinstance(data, dict) or set(data) != required:
            raise ValueError("Invalid license fields")
        UUID(data["license_id"])
        machine = normalize_machine_id(data["machine_id"])
        if machine != data["machine_id"] or data["plan"] not in PLANS:
            raise ValueError("Invalid machine or plan")
        issued = parse_timestamp(data["issued_at"])
        if data["plan"] == "LIFETIME":
            if data["expires_at"] is not None:
                raise ValueError("Lifetime must not expire")
        elif data["expires_at"] is None or parse_timestamp(data["expires_at"]) <= issued:
            raise ValueError("Expiry must follow issue date")
        features = data["features"]
        if not isinstance(features, list) or any(
            not isinstance(item, str) or item not in FEATURES for item in features
        ):
            raise ValueError("Invalid features")
        if len(set(features)) != len(features):
            raise ValueError("Duplicate features")
        return cls(
            data["license_id"], machine, data["plan"], data["issued_at"], data["expires_at"], tuple(features)
        )
