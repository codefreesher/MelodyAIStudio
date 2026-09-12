"""Collect the minimal device description required by activation."""

import platform
import socket

from app.security.machine_id import get_machine_id


class DeviceInfoService:
    def __init__(self, app_version: str) -> None:
        self.app_version = app_version

    def collect(self) -> dict[str, str]:
        hostname = socket.gethostname().strip()[:255]
        return {
            "machine_id": get_machine_id(),
            "hostname": hostname,
            "device_name": hostname,
            "os_name": platform.system().strip()[:50],
            # Laravel's activation contract caps these fields at 50 chars.
            # platform.version() is commonly much longer on Linux builds.
            "os_version": platform.version().strip()[:50],
            "architecture": platform.machine().strip()[:50],
            "app_version": self.app_version.strip()[:50],
        }

    def activation_payload(self) -> dict[str, str]:
        result = self.collect()
        result.pop("machine_id")
        return result
