"""Backend-replaceable activation interface, independent of Qt."""

from typing import Protocol

from app.models.license import License


class ActivationBackend(Protocol):
    def activate(self, token: str) -> License: ...


class ActivationService:
    def __init__(self, backend: ActivationBackend, machine_id: str) -> None:
        self.backend = backend
        self.machine_id = machine_id

    def activate(self, token: str) -> License:
        return self.backend.activate(token.strip())
