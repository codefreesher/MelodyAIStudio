"""Non-secret activation metadata; the device token lives only in CredentialVault."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

FEATURE_NAMES = ("music", "lyrics", "audio", "image", "online_ai", "offline_ai")


@dataclass
class DeviceSession:
    device_uuid: str
    license_id: str
    plan: str
    features: dict[str, bool] = field(default_factory=dict)
    expires_at: str | None = None
    last_seen: str | None = None
    last_server_check: str | None = None
    offline_grace_until: str | None = None
    heartbeat_interval: int = 60

    def has_feature(self, name: str) -> bool:
        aliases = {"lyric": "lyrics", "online": "online_ai", "offline": "offline_ai"}
        return bool(self.features.get(aliases.get(name, name), False))

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> "DeviceSession":
        activation = data.get("activation") if isinstance(data.get("activation"), dict) else {}
        device = data.get("device") if isinstance(data.get("device"), dict) else {}
        license_data = data.get("license") if isinstance(data.get("license"), dict) else {}
        entitlement = data.get("entitlement") if isinstance(data.get("entitlement"), dict) else {}
        plan_data = data.get(
            "plan", license_data.get("plan", entitlement.get("plan", activation.get("plan", "")))
        )
        plan = plan_data if isinstance(plan_data, str) else (
            plan_data.get("code", plan_data.get("name", plan_data.get("slug", "")))
            if isinstance(plan_data, dict) else ""
        )
        raw_features = data.get(
            "features",
            license_data.get(
                "features",
                entitlement.get(
                    "features",
                    activation.get(
                        "features", plan_data.get("features", {}) if isinstance(plan_data, dict) else {}
                    ),
                ),
            ),
        )
        if isinstance(raw_features, list):
            features = {name: name in raw_features for name in FEATURE_NAMES}
        elif isinstance(raw_features, dict):
            features = {name: bool(raw_features.get(name, False)) for name in FEATURE_NAMES}
        else:
            raise ValueError("Invalid activation features")
        interval = data.get("heartbeat_interval", 60)
        if not isinstance(interval, int):
            interval = 60
        raw_device = data.get("device")
        raw_license = data.get("license")
        device_uuid = (
            data.get("device_uuid") or data.get("device_id") or device.get("uuid")
            or device.get("device_uuid") or device.get("id") or activation.get("device_uuid")
            or activation.get("device_id")
            or (raw_device if isinstance(raw_device, (str, int)) else None)
        )
        license_id = (
            data.get("license_id") or data.get("license_uuid") or license_data.get("uuid")
            or license_data.get("license_id") or license_data.get("id") or entitlement.get("license_id")
            or activation.get("license_id")
            or (raw_license if isinstance(raw_license, (str, int)) else None)
        )
        if not device_uuid or not license_id:
            raise ValueError("Activation response is missing device or license identity")
        return cls(
            device_uuid=str(device_uuid), license_id=str(license_id), plan=str(plan), features=features,
            expires_at=data.get(
                "expires_at", license_data.get("expires_at", entitlement.get("expires_at"))
            ),
            last_seen=data.get("last_seen", device.get("last_seen_at")), heartbeat_interval=max(30, interval),
        )


class DeviceSessionStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def save(self, session: DeviceSession) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(asdict(session), stream, ensure_ascii=False, indent=2)
            os.replace(temporary, self.path)
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)

    def load(self) -> DeviceSession | None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return DeviceSession(**data) if isinstance(data, dict) else None
        except (OSError, ValueError, TypeError, UnicodeError):
            return None

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)
