"""Short-lived SQLite connections are safe across generation workers."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            if connection.execute("PRAGMA user_version").fetchone()[0] > 1:
                raise ValueError("Database được tạo bởi phiên bản MelodyAI mới hơn.")
            connection.executescript(Path(__file__).with_name("schema.sql").read_text())

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()
