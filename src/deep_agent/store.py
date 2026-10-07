"""Application-owned task records. Remote identifiers confer no authorization."""

import json
import sqlite3
import threading
from pathlib import Path
from uuid import uuid4


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        with self.connection:
            self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, viewer TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (session TEXT NOT NULL, content TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, session TEXT NOT NULL, viewer TEXT NOT NULL, payload TEXT NOT NULL);
            """)

    def create(self, viewer: str) -> dict:
        sid = str(uuid4())
        with self.lock, self.connection:
            self.connection.execute("INSERT INTO sessions VALUES (?,?)", (sid, viewer))
        return {"id": sid}

    def owned(self, viewer: str, sid: str) -> dict:
        with self.lock:
            row = self.connection.execute(
                "SELECT id FROM sessions WHERE id=? AND viewer=?", (sid, viewer)
            ).fetchone()
            if not row:
                raise KeyError("not found")
            events = self.connection.execute(
                "SELECT content FROM events WHERE session=? ORDER BY rowid", (sid,)
            ).fetchall()
            return {"id": sid, "events": [json.loads(row["content"]) for row in events]}

    def sessions(self, viewer: str) -> list:
        with self.lock:
            return [
                dict(row)
                for row in self.connection.execute(
                    "SELECT id FROM sessions WHERE viewer=? ORDER BY rowid DESC LIMIT 50", (viewer,)
                )
            ]

    def event(self, viewer: str, sid: str, event: dict) -> None:
        with self.lock, self.connection:
            self.owned(viewer, sid)
            self.connection.execute("INSERT INTO events VALUES (?,?)", (sid, json.dumps(event)))

    def delete(self, viewer: str, sid: str) -> None:
        with self.lock, self.connection:
            self.owned(viewer, sid)
            self.connection.execute("DELETE FROM events WHERE session=?", (sid,))
            self.connection.execute("DELETE FROM tasks WHERE session=? AND viewer=?", (sid, viewer))
            self.connection.execute("DELETE FROM sessions WHERE id=? AND viewer=?", (sid, viewer))

    def put_task(self, viewer: str, sid: str, payload: dict, task_id: str | None = None) -> dict:
        with self.lock, self.connection:
            self.owned(viewer, sid)
            tid = task_id or str(uuid4())
            if task_id:
                self.task(viewer, tid)
            data = dict(payload, id=tid, session_id=sid)
            self.connection.execute(
                "INSERT OR REPLACE INTO tasks VALUES (?,?,?,?)",
                (tid, sid, viewer, json.dumps(data)),
            )
            return data

    def task(self, viewer: str, tid: str) -> dict:
        with self.lock:
            row = self.connection.execute(
                "SELECT payload FROM tasks WHERE id=? AND viewer=?", (tid, viewer)
            ).fetchone()
            if not row:
                raise KeyError("not found")
            return json.loads(row["payload"])
