"""Public authenticated identity; contains no credentials."""

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: str
    username: str
    email: str
    plan: str = "DEVELOPMENT"
    expires_at: str | None = None
