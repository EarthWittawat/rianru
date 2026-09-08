"""Shared skip conditions for tests that need more than a running database.

Some tests read the course files themselves, and some assume a corpus has
already been ingested. Neither is true on a fresh checkout or on CI, where the
course material is deliberately absent. Those tests skip themselves rather than
fail, so a red suite always means real breakage.
"""

from functools import lru_cache

import pytest

from app.services.neo4j_client import get_driver


@lru_cache(maxsize=1)
def _corpus_is_ingested() -> bool:
    try:
        with get_driver().session() as session:
            record = session.run("MATCH (d:Document) RETURN count(d) AS n").single()
    except Exception:
        return False
    return bool(record and record["n"])


requires_ingested_corpus = pytest.mark.skipif(
    not _corpus_is_ingested(),
    reason="no ingested corpus in Neo4j; run scripts/ingest.py first",
)
