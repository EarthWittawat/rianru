import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

# Below this many attempts a topic is too thinly sampled to call "weak" — one
# unlucky answer should not outrank a topic that has been genuinely failed.
MIN_ATTEMPTS_FOR_WEAKNESS = 3

SCHEMA = """
CREATE TABLE IF NOT EXISTS quiz_attempt (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id   TEXT    NOT NULL,
    topic         TEXT    NOT NULL,
    format        TEXT    NOT NULL,
    chosen_answer TEXT,
    is_correct    INTEGER NOT NULL,
    graded_by     TEXT    NOT NULL,
    created_at    TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempt_topic   ON quiz_attempt(topic);
CREATE INDEX IF NOT EXISTS idx_attempt_created ON quiz_attempt(created_at);
"""


@contextmanager
def connect():
    path = Path(settings.progress_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with connect() as connection:
        connection.executescript(SCHEMA)


def record_attempt(
    question_id: str,
    topic: str,
    question_format: str,
    is_correct: bool,
    graded_by: str,
    chosen_answer: str | None = None,
) -> int:
    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO quiz_attempt
                (question_id, topic, format, chosen_answer, is_correct,
                 graded_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                question_id,
                topic,
                question_format,
                chosen_answer,
                int(bool(is_correct)),
                graded_by,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return cursor.lastrowid


def topic_stats() -> list[dict]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT topic,
                   COUNT(*)                AS attempted,
                   SUM(is_correct)         AS correct,
                   MAX(created_at)         AS last_attempt_at
            FROM quiz_attempt
            GROUP BY topic
            ORDER BY topic
            """
        ).fetchall()

    return [
        {
            "topic": row["topic"],
            "attempted": row["attempted"],
            "correct": row["correct"],
            "accuracy": row["correct"] / row["attempted"],
            "last_attempt_at": row["last_attempt_at"],
        }
        for row in rows
    ]


def weak_topics(
    limit: int = 5, min_attempts: int = MIN_ATTEMPTS_FOR_WEAKNESS
) -> list[dict]:
    candidates = [s for s in topic_stats() if s["attempted"] >= min_attempts]
    candidates.sort(key=lambda s: (s["accuracy"], -s["attempted"]))
    return candidates[:limit]


def recent_attempts(topic: str | None = None, limit: int = 20) -> list[dict]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT id, question_id, topic, format, chosen_answer,
                   is_correct, graded_by, created_at
            FROM quiz_attempt
            WHERE (? IS NULL OR topic = ?)
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (topic, topic, limit),
        ).fetchall()

    return [dict(row) for row in rows]
