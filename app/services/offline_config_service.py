"""Local configuration and Ollama management, called off the UI thread."""

import json
import shlex
import threading
from urllib.parse import urlparse

import httpx

from app.database.repositories.settings_repository import SettingsRepository
from app.resources_manager.process_manager import ProcessManager


class OfflineConfigService:
    def __init__(self, settings: SettingsRepository, processes: ProcessManager) -> None:
        self.settings, self.processes = settings, processes
        self.cancel_event = threading.Event()

    def load(self, name: str) -> dict:
        return self.settings.get(
            "offline:" + name,
            {"url": "http://127.0.0.1:11434" if name == "Ollama" else "http://127.0.0.1:7860"},
        )

    def _url(self, data: dict) -> str:
        url = data.get("url", "").rstrip("/")
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError("Offline URL phải trỏ tới localhost.")
        return url

    def save(self, name: str, data: dict) -> str:
        self._url(data)
        self.settings.set("offline:" + name, data)
        return "Đã lưu cấu hình Offline."

    def test(self, name: str, data: dict) -> str:
        url = self._url(data)
        endpoint = (
            "/api/tags" if name == "Ollama" else "/sdapi/v1/sd-models" if name == "Stable Diffusion" else ""
        )
        response = httpx.get(url + endpoint, timeout=10)
        response.raise_for_status()
        if name == "Ollama":
            return "Running · Models: " + ", ".join(
                item["name"] for item in response.json().get("models", [])
            )
        return f"Running · HTTP {response.status_code}"

    def start(self, name: str, data: dict) -> str:
        arguments = ["serve"] if name == "Ollama" else shlex.split(data.get("arguments", ""))
        return self.processes.start(name, data.get("executable", ""), arguments)

    def stop(self, name: str, data: dict) -> str:
        return self.processes.stop(name)

    def pull(self, name: str, data: dict, progress=lambda value: None) -> str:
        if name != "Ollama":
            raise ValueError("Pull model chỉ áp dụng Ollama.")
        if not data.get("model"):
            raise ValueError("Nhập tên model.")
        with httpx.stream(
            "POST", self._url(data) + "/api/pull", json={"model": data["model"], "stream": True}, timeout=120
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if self.cancel_event.is_set():
                    raise ValueError("Đã hủy theo dõi tải model. Engine có thể vẫn hoàn tất lớp đang tải.")
                item = json.loads(line)
                if item.get("error"):
                    raise ValueError("Ollama không tải được model.")
                total, completed = item.get("total"), item.get("completed")
                if total:
                    progress(int(completed / total * 100))
        return "Đã tải model."

    def list_models(self, name: str, data: dict) -> list[dict]:
        if name != "Ollama":
            raise ValueError("Danh sách model chỉ áp dụng Ollama.")
        response = httpx.get(self._url(data) + "/api/tags", timeout=10)
        response.raise_for_status()
        return [
            {"name": item["name"], "size": item.get("size", 0)} for item in response.json().get("models", [])
        ]

    def delete(self, name: str, data: dict) -> str:
        if name != "Ollama" or not data.get("model"):
            raise ValueError("Chọn Ollama và nhập model cần xóa.")
        response = httpx.request(
            "DELETE", self._url(data) + "/api/delete", json={"model": data["model"]}, timeout=30
        )
        response.raise_for_status()
        return "Đã xóa model khỏi Ollama."
