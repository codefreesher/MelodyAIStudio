"""Non-blocking device heartbeat scheduler."""

import logging
import platform
from datetime import datetime, timezone

from PySide6.QtCore import QObject, QThreadPool, QTimer, Signal, Slot

from app.api.api_client import ApiError
from app.api.device_api import DeviceApi
from app.security.credential_vault import CredentialVault
from app.security.device_session import DeviceSession, DeviceSessionStore
from app.services.activation_service import DEVICE_TOKEN_KEY
from app.utils.async_utils import Worker

logger = logging.getLogger(__name__)


class HeartbeatService(QObject):
    active = Signal(object)
    access_changed = Signal(str, str)
    network_error = Signal(str)

    def __init__(self, api: DeviceApi, vault: CredentialVault, store: DeviceSessionStore,
                 app_version: str, integrity_status: str = "ok", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.api, self.vault, self.store = api, vault, store
        self.app_version, self.integrity_status = app_version, integrity_status
        self.session: DeviceSession | None = None
        self.worker: Worker | None = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_now)

    def start(self, session: DeviceSession, immediate: bool = False) -> None:
        self.session = session
        self.timer.setInterval(max(30, session.heartbeat_interval) * 1000)
        self.timer.start()
        if immediate:
            self.check_now()

    def stop(self) -> None:
        self.timer.stop()

    def set_minimized(self, minimized: bool) -> None:
        if self.session:
            seconds = 120 if minimized else max(30, self.session.heartbeat_interval)
            self.timer.setInterval(seconds * 1000)

    @Slot()
    def check_now(self) -> None:
        if self.worker is not None:
            return
        token = self.vault.get(DEVICE_TOKEN_KEY)
        if not token:
            self.access_changed.emit("DEVICE_REVOKED", "Thiết bị đã bị thu hồi")
            return
        self.worker = Worker(lambda: self.api.heartbeat(
            token, self.app_version[:50], platform.version().strip()[:50], self.integrity_status
        ))
        self.worker.signals.result.connect(self._success)
        self.worker.signals.error.connect(self._failure)
        self.worker.signals.finished.connect(self._finished)
        QThreadPool.globalInstance().start(self.worker)

    @Slot(object)
    def _success(self, data: dict) -> None:
        status = str(data.get("status", "active")).upper()
        if status == "ACTIVE":
            if self.session:
                self.session.last_seen = data.get("last_seen") or datetime.now(timezone.utc).isoformat()
                self.session.last_server_check = datetime.now(timezone.utc).isoformat()
                if "features" in data:
                    merged = {**self.session.__dict__, **data}
                    merged.pop("status", None)
                    self.session = DeviceSession.from_response(merged)
                    self.session.last_seen = data.get("last_seen") or datetime.now(timezone.utc).isoformat()
                    self.session.last_server_check = datetime.now(timezone.utc).isoformat()
                if isinstance(data.get("heartbeat_interval"), int):
                    self.session.heartbeat_interval = max(30, data["heartbeat_interval"])
                    self.timer.setInterval(self.session.heartbeat_interval * 1000)
                self.store.save(self.session)
                self.active.emit(self.session)
            return
        self._handle_access_change(status)

    @Slot(object)
    def _failure(self, error: Exception) -> None:
        if isinstance(error, ApiError) and error.code in {
            "USER_LOCKED", "LICENSE_REVOKED", "LICENSE_EXPIRED", "DEVICE_REVOKED", "DEVICE_BLOCKED", "PLAN_DISABLED"
        }:
            self._handle_access_change(error.code, str(error))
            return
        logger.warning("Heartbeat network error code=%s", getattr(error, "code", type(error).__name__))
        self.network_error.emit("Không thể kết nối máy chủ.")

    def _handle_access_change(self, code: str, message: str = "") -> None:
        logger.warning("Server access status changed code=%s", code)
        self.stop()
        if code in {"DEVICE_REVOKED", "LICENSE_REVOKED", "LICENSE_EXPIRED", "USER_LOCKED"}:
            self.vault.delete(DEVICE_TOKEN_KEY)
            self.store.clear()
        self.access_changed.emit(code, message or str(ApiError(code)))

    @Slot()
    def _finished(self) -> None:
        self.worker = None
