"""Verified staged installs, repair and scoped removal."""

import shutil
import tempfile
import threading
from pathlib import Path

from app.resources_manager.extractor import extract_zip
from app.resources_manager.resource_manifest import load_manifest
from app.services.download_service import DownloadService, verify_sha256


class ResourceService:
    def __init__(self, root: Path, downloads: Path, manifest: Path) -> None:
        self.root, self.downloads, self.manifest = root, downloads, manifest
        self.cancel_event = threading.Event()

    def list(self) -> list[dict]:
        return [
            dict(item, installed=(self.root / item["id"] / ".installed").exists())
            for item in load_manifest(self.manifest)
        ]

    def perform(self, resource: dict, action: str, progress=lambda value: None) -> str:
        # Resolve trusted metadata again instead of trusting mutable UI rows.
        item = next(value for value in load_manifest(self.manifest) if value["id"] == resource["id"])
        destination = self.root / item["id"]
        archive = self.downloads / (item["id"] + ".zip")
        if action == "remove":
            shutil.rmtree(destination, ignore_errors=False) if destination.exists() else None
            return "Đã gỡ tài nguyên."
        if not item.get("url") or not item.get("sha256"):
            raise ValueError("Chưa cấu hình URL/SHA256. Nhập manifest tài nguyên đã kiểm duyệt.")
        if action in ("download", "repair") or not archive.exists():
            DownloadService().download(item["url"], archive, item["sha256"], progress, self.cancel_event)
        verify_sha256(archive, item["sha256"])
        if action == "download":
            return "Đã tải và xác minh SHA256."
        self.root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=self.root) as temp:
            staging = Path(temp) / "content"
            extract_zip(archive, staging)
            if item.get("executable") and not (staging / item["executable"]).is_file():
                raise ValueError("Archive thiếu executable theo manifest.")
            if self.cancel_event.is_set():
                raise ValueError("Đã hủy cài đặt.")
            (staging / ".installed").write_text(item.get("version", ""), encoding="utf-8")
            backup = Path(temp) / "backup"
            if destination.exists():
                destination.rename(backup)
            try:
                staging.rename(destination)
            except OSError:
                if backup.exists():
                    backup.rename(destination)
                raise
        return "Đã cài tài nguyên."
