"""Non-secret settings storage."""

import json

from app.database.database import Database


class SettingsRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get(self, key: str, default: object = None) -> object:
        with self.database.connect() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, key: str, value: object) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value, ensure_ascii=False)),
            )
