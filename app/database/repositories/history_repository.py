"""Parameterized history queries."""

import json
from datetime import datetime, timezone

from app.database.database import Database
from app.models.generation import Generation


class HistoryRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def save(self, result: Generation) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        metadata = dict(result.metadata, paths=[str(path) for path in result.paths])
        with self.database.connect() as connection:
            connection.execute(
                """INSERT INTO history(uuid,type,title,provider,prompt,result_path,thumbnail_path,metadata_json,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(uuid) DO UPDATE SET metadata_json=excluded.metadata_json,
                title=excluded.title,updated_at=excluded.updated_at""",
                (
                    result.uuid,
                    result.type,
                    result.title,
                    result.provider,
                    result.prompt,
                    str(result.paths[0]),
                    str(result.paths[0]) if result.type == "image" else "",
                    json.dumps(metadata, ensure_ascii=False),
                    timestamp,
                    timestamp,
                ),
            )
            connection.execute(
                "INSERT OR REPLACE INTO generations VALUES(?,?,?,?)",
                (result.uuid, result.type, "completed", timestamp),
            )
            connection.execute(
                "INSERT OR IGNORE INTO projects VALUES(?,?,?,?)",
                (result.uuid, result.title, result.type, timestamp),
            )

    def list(
        self, kind: str = "", search: str = "", page: int = 0, size: int = 20, ascending: bool = False
    ) -> tuple[list[dict], int]:
        where = 'WHERE (?="" OR type=?) AND (title LIKE ? OR prompt LIKE ?)'
        params = (kind, kind, f"%{search}%", f"%{search}%")
        order = "ASC" if ascending else "DESC"
        with self.database.connect() as connection:
            count = connection.execute("SELECT count(*) FROM history " + where, params).fetchone()[0]
            rows = connection.execute(
                "SELECT * FROM history "
                + where
                + f" ORDER BY created_at {order},id {order} LIMIT ? OFFSET ?",
                (*params, size, max(0, page) * size),
            ).fetchall()
        return [dict(row) for row in rows], count

    def delete(self, uuid: str) -> None:
        with self.database.connect() as connection:
            connection.execute("DELETE FROM history WHERE uuid=?", (uuid,))
            connection.execute("DELETE FROM projects WHERE id=?", (uuid,))
