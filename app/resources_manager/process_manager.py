"""Only manage processes started by this application; no shell execution."""

import subprocess
from pathlib import Path


class ProcessManager:
    def __init__(self) -> None:
        self.processes: dict[str, subprocess.Popen] = {}

    def start(self, name: str, executable: str, arguments: list[str]) -> str:
        process = self.processes.get(name)
        if process and process.poll() is None:
            return "Đang chạy."
        path = Path(executable).expanduser().resolve()
        if not path.is_file():
            raise ValueError("Executable không tồn tại.")
        self.processes[name] = subprocess.Popen(
            [str(path), *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        return "Đã gửi lệnh khởi động. Nhấn Test để kiểm tra dịch vụ."

    def stop(self, name: str) -> str:
        process = self.processes.get(name)
        if not process or process.poll() is not None:
            return "Không có tiến trình do MelodyAI quản lý."
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        return "Đã dừng tiến trình."
