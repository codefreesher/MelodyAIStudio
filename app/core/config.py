"""Persist non-secret application preferences as JSON."""

import json
import os
import tempfile
from dataclasses import asdict, dataclass, fields
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    language: str = "vi"
    theme: str = "pink_light"
    check_updates_automatically: bool = True
    github_owner: str = ""
    github_repository: str = ""
    backend_base_url: str = ""

    @classmethod
    def load(cls, path: Path) -> "AppConfig":
        if not path.exists():
            config = cls()
            config.save(path)
            return config
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Configuration must be a JSON object")
        defaults = cls()
        values = {}
        for field in fields(cls):
            value = data.get(field.name, getattr(defaults, field.name))
            if type(value) is not type(getattr(defaults, field.name)):
                raise ValueError(f"Invalid configuration field: {field.name}")
            values[field.name] = value
        return cls(**values)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                delete=False,
            ) as stream:
                temporary = Path(stream.name)
                json.dump(asdict(self), stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
