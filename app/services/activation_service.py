"""Activation orchestration, independent of Qt."""

import logging
from datetime import datetime, timezone
from typing import Protocol

from app.api.api_client import ApiError
from app.api.license_api import LicenseApi
from app.models.license import License
from app.security.credential_vault import CredentialVault
from app.security.device_session import DeviceSession, DeviceSessionStore
from app.services.device_info_service import DeviceInfoService

logger = logging.getLogger("melodyai")
DEVICE_TOKEN_KEY = "melodyai.device_token"


class ActivationBackend(Protocol):
    def activate(self, token: str) -> License: ...


class ActivationService:
    def __init__(
        self,
        backend: ActivationBackend | LicenseApi,
        machine_id: str,
        device_info: DeviceInfoService | None = None,
        vault: CredentialVault | None = None,
        sessions: DeviceSessionStore | None = None,
        local_verifier: object | None = None,
    ) -> None:
        self.backend = backend
        self.machine_id = machine_id
        self.device_info = device_info
        self.vault = vault
        self.sessions = sessions
        self.local_verifier = local_verifier

    def activate(self, token: str) -> License | DeviceSession:
        key = token.strip()
        # Signed legacy keys can be rejected locally before making a request.
        if key.startswith("MLAI1.") and self.local_verifier is not None:
            self.local_verifier.verify(key, self.machine_id)
        if not all((self.device_info, self.vault, self.sessions)):
            return self.backend.activate(key)  # compatibility with the original local backend
        try:
            data = self.backend.activate(key, self.machine_id, self.device_info.activation_payload())
            device_token = data.get("device_token")
            if not isinstance(device_token, str) or not device_token:
                raise ValueError("Activation response has no device token")
            try:
                session = DeviceSession.from_response(data)
            except (KeyError, TypeError, ValueError) as exc:
                shape = {
                    name: sorted(value.keys()) if isinstance(value, dict) else type(value).__name__
                    for name, value in data.items()
                    if name not in {"device_token", "token", "access_token"}
                }
                logger.warning("Invalid activation response shape=%s", shape)
                raise ApiError("INVALID_RESPONSE", "Phản hồi kích hoạt từ máy chủ không hợp lệ.") from exc
            session.last_server_check = datetime.now(timezone.utc).isoformat()
            session.last_seen = session.last_seen or session.last_server_check
            self.vault.set(DEVICE_TOKEN_KEY, device_token)
            try:
                self.sessions.save(session)
            except Exception:
                self.vault.delete(DEVICE_TOKEN_KEY)
                raise
            logger.info("Activation succeeded license_id=%s device_uuid=%s", session.license_id, session.device_uuid)
            return session
        except Exception as error:
            logger.warning("Activation failed code=%s", getattr(error, "code", type(error).__name__))
            raise
