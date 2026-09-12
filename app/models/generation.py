"""Provider-neutral creative output, files live outside SQLite."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Generation:
    uuid: str
    type: str
    title: str
    prompt: str
    paths: list[Path]
    provider: str = "Mock"
    metadata: dict = field(default_factory=dict)
