"""Catalog metadata. Install URLs/digests must come from a vetted manifest."""

import json
import re
from pathlib import Path

DEFAULT_RESOURCES = [
    {"id": "ollama", "name": "Ollama", "description": "AI model chạy local"},
    {"id": "ffmpeg", "name": "FFmpeg", "description": "Xử lý audio/video"},
    {"id": "python", "name": "Python Runtime", "description": "Chạy các model local"},
    {"id": "stable-diffusion", "name": "Stable Diffusion WebUI", "description": "Tạo ảnh local"},
    {"id": "tts-models", "name": "TTS Models", "description": "Giọng nói offline"},
]


def load_manifest(path: Path) -> list[dict]:
    if not path.exists():
        return [
            dict(item, version="", url="", sha256="", archive_type="zip", executable="")
            for item in DEFAULT_RESOURCES
        ]
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Manifest phải là danh sách.")
    ids = set()
    for item in data:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or not isinstance(item.get("name"), str)
        ):
            raise ValueError("Mỗi resource cần id và name dạng chuỗi.")
        if not isinstance(item.get("executable", ""), str):
            raise ValueError("Executable phải là chuỗi.")
        if not re.fullmatch(r"[a-z0-9-]+", item["id"]) or item["id"] in ids:
            raise ValueError("Resource ID không hợp lệ/trùng.")
        ids.add(item["id"])
        executable = Path(item.get("executable", "").replace("\\", "/"))
        if executable.is_absolute() or ".." in executable.parts or ":" in str(executable):
            raise ValueError("Executable phải nằm trong resource folder.")
        if item.get("archive_type") != "zip":
            raise ValueError("Resource hiện hỗ trợ archive ZIP.")
    return data
