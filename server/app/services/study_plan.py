import json
import uuid
from datetime import datetime, timezone

from app.services.progress import connect

SCHEMA = """
CREATE TABLE IF NOT EXISTS study_plan (
    id         TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS study_task (
    id           TEXT    PRIMARY KEY,
    plan_id      TEXT    NOT NULL REFERENCES study_plan(id) ON DELETE CASCADE,
    position     INTEGER NOT NULL,
    action       TEXT    NOT NULL,
    topic        TEXT    NOT NULL,
    source       TEXT,
    why          TEXT,
    est_minutes  INTEGER,
    done         INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_task_plan ON study_task(plan_id);
"""


def init_db() -> None:
    with connect() as connection:
        connection.executescript(SCHEMA)


def save_plan(tasks: list[dict]) -> dict:
    plan_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    with connect() as connection:
        connection.execute(
            "INSERT INTO study_plan (id, created_at) VALUES (?, ?)",
            (plan_id, created_at),
        )
        connection.executemany(
            """
            INSERT INTO study_task
                (id, plan_id, position, action, topic, source, why, est_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(uuid.uuid4()),
                    plan_id,
                    position,
                    task["action"],
                    task["topic"],
                    json.dumps(task["source"]) if task.get("source") else None,
                    task.get("why"),
                    task.get("est_minutes"),
                )
                for position, task in enumerate(tasks)
            ],
        )

    return get_plan(plan_id)


def latest_plan() -> dict | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT id FROM study_plan ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
    return get_plan(row["id"]) if row else None


def get_plan(plan_id: str) -> dict | None:
    with connect() as connection:
        plan = connection.execute(
            "SELECT id, created_at FROM study_plan WHERE id = ?", (plan_id,)
        ).fetchone()
        if plan is None:
            return None
        tasks = connection.execute(
            """
            SELECT id, action, topic, source, why, est_minutes, done
            FROM study_task WHERE plan_id = ? ORDER BY position
            """,
            (plan_id,),
        ).fetchall()

    return {
        "id": plan["id"],
        "created_at": plan["created_at"],
        "tasks": [
            {
                "id": task["id"],
                "action": task["action"],
                "topic": task["topic"],
                "source": json.loads(task["source"]) if task["source"] else None,
                "why": task["why"],
                "est_minutes": task["est_minutes"],
                "done": bool(task["done"]),
            }
            for task in tasks
        ],
    }


def set_task_done(task_id: str, done: bool) -> bool:
    with connect() as connection:
        cursor = connection.execute(
            "UPDATE study_task SET done = ? WHERE id = ?", (int(done), task_id)
        )
        return cursor.rowcount > 0
