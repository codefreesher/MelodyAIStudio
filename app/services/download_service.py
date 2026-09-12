"""Bounded HTTPS streaming download with cancellation and mandatory digest."""

import hashlib
import re
import threading
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlparse

import httpx


def verify_sha256(path: Path, expected: str) -> None:
    if not re.fullmatch(r"[a-fA-F0-9]{64}", expected):
        raise ValueError("Thiếu SHA256 hợp lệ.")
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual.lower() != expected.lower():
        raise ValueError("SHA256 không khớp. Không sử dụng tệp tải về.")


class DownloadService:
    def download(
        self,
        url: str,
        destination: Path,
        sha256: str,
        progress: Callable[[int], None] = lambda value: None,
        cancel: threading.Event | None = None,
        limit: int = 8 * 1024**3,
    ) -> Path:
        if urlparse(url).scheme != "https":
            raise ValueError("Download yêu cầu HTTPS.")
        if not re.fullmatch(r"[a-fA-F0-9]{64}", sha256):
            raise ValueError("Manifest thiếu SHA256.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_suffix(destination.suffix + ".part")
        try:
            with httpx.Client(timeout=60, follow_redirects=False) as client:
                for _ in range(6):
                    with client.stream("GET", url) as response:
                        if response.is_redirect:
                            url = str(response.url.join(response.headers["location"]))
                            if urlparse(url).scheme != "https":
                                raise ValueError("Redirect không dùng HTTPS.")
                            continue
                        response.raise_for_status()
                        total = int(response.headers.get("content-length", 0))
                        count = 0
                        if total > limit:
                            raise ValueError("Tệp vượt giới hạn tải.")
                        with partial.open("wb") as output:
                            for block in response.iter_bytes(65536):
                                if cancel and cancel.is_set():
                                    raise ValueError("Đã hủy tải.")
                                count += len(block)
                                if count > limit:
                                    raise ValueError("Tệp vượt giới hạn tải.")
                                output.write(block)
                                progress(min(99, count * 100 // total) if total else 0)
                        break
                else:
                    raise ValueError("Quá nhiều redirect.")
            verify_sha256(partial, sha256)
            partial.replace(destination)
            progress(100)
            return destination
        finally:
            partial.unlink(missing_ok=True)
