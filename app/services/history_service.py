"""History access and export; deleting a row never removes arbitrary files."""

import json
import shutil
from pathlib import Path

from app.database.repositories.history_repository import HistoryRepository


class HistoryService:
    def __init__(self, repository: HistoryRepository) -> None:
        self.repository = repository

    def list(self, **filters: object) -> tuple[list[dict], int]:
        return self.repository.list(**filters)

    def delete(self, uuid: str) -> None:
        self.repository.delete(uuid)

    def export(self, row: dict, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        for value in json.loads(row["metadata_json"]).get("paths", [row["result_path"]]):
            source = Path(value)
            if not source.is_file():
                raise ValueError("Tệp kết quả không còn tồn tại.")
            target = folder / source.name
            if source.resolve() != target.resolve():
                shutil.copy2(source, target)
