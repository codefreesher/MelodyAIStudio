"""Select a newer stable Windows installer with a published SHA256 digest."""

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from packaging.version import Version


@dataclass(frozen=True)
class Release:
    version: str
    notes: str
    name: str
    url: str
    sha256: str
    size: int = 0
    html_url: str = ""


def select_release(data: dict, current: str) -> Release | None:
    if data.get("draft") or data.get("prerelease"):
        return None
    version = Version(data["tag_name"].removeprefix("v"))
    if version <= Version(current) or version.is_prerelease:
        return None
    expected_name = f"MelodyAI-Setup-{version}.exe"
    for asset in data.get("assets", []):
        digest = asset.get("digest", "") or ""
        url = asset.get("browser_download_url", "")
        if asset.get("name") == expected_name and re.fullmatch(r"sha256:[a-fA-F0-9]{64}", digest):
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.hostname != "github.com":
                raise ValueError("Update URL không hợp lệ.")
            html_url = data.get("html_url") or ""
            if html_url and (urlparse(html_url).scheme != "https" or urlparse(html_url).hostname != "github.com"):
                html_url = ""
            return Release(
                str(version),
                data.get("body") or "",
                expected_name,
                url,
                digest[7:],
                size=int(asset.get("size") or 0),
                html_url=html_url,
            )
    raise ValueError("Release mới thiếu installer Windows hoặc SHA256 digest.")
