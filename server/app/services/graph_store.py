from app.services.chunking import Chunk
from app.services.embeddings import EMBEDDING_DIM, embed_text, embed_texts
from app.services.neo4j_client import get_driver

VECTOR_INDEX = "chunk_embedding_index"


def ensure_schema() -> None:
    with get_driver().session() as session:
        session.run(
            "CREATE CONSTRAINT document_id IF NOT EXISTS "
            "FOR (d:Document) REQUIRE d.id IS UNIQUE"
        )
        session.run(
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS "
            "FOR (c:Chunk) REQUIRE c.id IS UNIQUE"
        )
        session.run(
            "CREATE CONSTRAINT entity_name IF NOT EXISTS "
            "FOR (e:Entity) REQUIRE e.name IS UNIQUE"
        )
        session.run(
            f"CREATE VECTOR INDEX {VECTOR_INDEX} IF NOT EXISTS "
            "FOR (c:Chunk) ON (c.embedding) OPTIONS {indexConfig: {"
            "`vector.dimensions`: $dim, `vector.similarity_function`: 'cosine'}}",
            dim=EMBEDDING_DIM,
        )


def write_document(
    doc_id: str,
    title: str,
    course: str,
    topic: str,
    activity_type: str,
    file_path: str,
    chunks: list[Chunk],
) -> int:
    embeddings = embed_texts([c.text for c in chunks]) if chunks else []
    rows = [
        {
            "id": f"{doc_id}::{index}",
            "index": index,
            "text": chunk.text,
            "page": chunk.page,
            "cell_index": chunk.cell_index,
            "cell_type": chunk.cell_type,
            "embedding": embedding,
        }
        for index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    with get_driver().session() as session:
        # Chunks are replaced wholesale on re-ingest, which would sever any
        # highlights hanging off them. Highlights are the student's own work,
        # so they are detached here and re-attached by chunk index below.
        session.run(
            """
            MERGE (d:Document {id: $doc_id})
            SET d.title = $title,
                d.course = $course,
                d.topic = $topic,
                d.activity_type = $activity_type,
                d.file_path = $file_path
            WITH d
            OPTIONAL MATCH (d)-[:HAS_CHUNK]->(old:Chunk)
            DETACH DELETE old
            """,
            doc_id=doc_id,
            title=title,
            course=course,
            topic=topic,
            activity_type=activity_type,
            file_path=file_path,
        )
        session.run(
            """
            MATCH (d:Document {id: $doc_id})
            UNWIND $rows AS row
            CREATE (c:Chunk {
                id: row.id,
                index: row.index,
                text: row.text,
                page: row.page,
                cell_index: row.cell_index,
                cell_type: row.cell_type,
                embedding: row.embedding
            })
            MERGE (d)-[:HAS_CHUNK]->(c)
            """,
            doc_id=doc_id,
            rows=rows,
        )
        session.run(
            """
            MATCH (h:Highlight {document_id: $doc_id})
            WHERE NOT (:Chunk)-[:HAS_HIGHLIGHT]->(h)
            MATCH (d:Document {id: $doc_id})-[:HAS_CHUNK]->(c:Chunk)
            WHERE c.index = h.chunk_index
            MERGE (c)-[:HAS_HIGHLIGHT]->(h)
            """,
            doc_id=doc_id,
        )
    return len(rows)


def write_entities(
    chunk_id: str, entities: list[dict], relations: list[dict]
) -> None:
    if not entities:
        return

    with get_driver().session() as session:
        session.run(
            """
            MATCH (c:Chunk {id: $chunk_id})
            UNWIND $entities AS entity
            MERGE (e:Entity {name: entity.name})
              ON CREATE SET e.type = entity.type
            MERGE (c)-[:MENTIONS]->(e)
            """,
            chunk_id=chunk_id,
            entities=entities,
        )
        if relations:
            session.run(
                """
                UNWIND $relations AS rel
                MATCH (source:Entity {name: rel.source})
                MATCH (target:Entity {name: rel.target})
                MERGE (source)-[r:RELATES_TO {type: rel.type}]->(target)
                """,
                relations=relations,
            )


def set_document_positions(positions: dict[str, int]) -> None:
    """Record where each document sits in the course's own teaching order.

    The syllabus is a designed sequence, so this is recorded truth rather than
    an inference: lecture 1 genuinely comes before lecture 6.
    """
    if not positions:
        return

    rows = [{"id": doc_id, "position": position} for doc_id, position in positions.items()]
    with get_driver().session() as session:
        session.run(
            """
            UNWIND $rows AS row
            MATCH (d:Document {id: row.id})
            SET d.position = row.position
            """,
            rows=rows,
        )


def concept_positions(
    course: str, document_ids: list[str] | None = None
) -> dict[str, float]:
    """Each concept, keyed to the earliest positioned document that teaches it.

    A concept introduced in lecture 1 and revisited in lecture 6 belongs to
    lecture 1: that is where a student meets it first.

    `document_ids` restricts the reading to those documents. Placing practice
    material needs that: without it, a lab positioned by an earlier run feeds
    its own position back in and drags itself across the course.
    """
    with get_driver().session() as session:
        result = session.run(
            """
            MATCH (d:Document {course: $course})-[:HAS_CHUNK]->(:Chunk)-[:MENTIONS]->(e:Entity)
            WHERE d.position IS NOT NULL
              AND ($ids IS NULL OR d.id IN $ids)
            RETURN e.name AS name, min(d.position) AS position
            """,
            course=course,
            ids=document_ids,
        )
        return {record["name"]: record["position"] for record in result}


def concept_frequency(course: str, document_ids: list[str] | None = None) -> dict[str, int]:
    """How many documents mention each concept — the rarity signal for placement."""
    with get_driver().session() as session:
        result = session.run(
            """
            MATCH (d:Document {course: $course})-[:HAS_CHUNK]->(:Chunk)-[:MENTIONS]->(e:Entity)
            WHERE $ids IS NULL OR d.id IN $ids
            RETURN e.name AS name, count(DISTINCT d) AS documents
            """,
            course=course,
            ids=document_ids,
        )
        return {record["name"]: record["documents"] for record in result}


def related_concept_pairs(course: str) -> list[tuple[str, str]]:
    """Concept pairs the material itself connects, in one course."""
    with get_driver().session() as session:
        result = session.run(
            """
            MATCH (a:Entity)-[:RELATES_TO]-(b:Entity)
            WHERE a.name < b.name
              AND EXISTS {
                MATCH (:Document {course: $course})-[:HAS_CHUNK]->(:Chunk)-[:MENTIONS]->(a)
              }
              AND EXISTS {
                MATCH (:Document {course: $course})-[:HAS_CHUNK]->(:Chunk)-[:MENTIONS]->(b)
              }
            RETURN DISTINCT a.name AS left, b.name AS right
            """,
            course=course,
        )
        return [(record["left"], record["right"]) for record in result]


def write_requirements(edges: list[dict]) -> int:
    """Store prerequisite edges. (a)-[:REQUIRES]->(b) reads: learn b before a."""
    if not edges:
        return 0

    with get_driver().session() as session:
        summary = session.run(
            """
            UNWIND $edges AS edge
            MATCH (source:Entity {name: edge.source})
            MATCH (target:Entity {name: edge.target})
            MERGE (source)-[r:REQUIRES]->(target)
            SET r.origin = edge.origin, r.reason = edge.reason
            """,
            edges=edges,
        ).consume()
    return summary.counters.relationships_created


def clear_requirements(course: str, origin: str | None = None) -> None:
    """Prerequisites are rebuilt from scratch; stale edges would outlive their reason.

    Scoped to one course. An unscoped delete here quietly wiped every edge in
    the database the first time a test exercised it.
    """
    with get_driver().session() as session:
        session.run(
            """
            MATCH (a:Entity)-[r:REQUIRES]->(:Entity)
            WHERE ($origin IS NULL OR r.origin = $origin)
              AND EXISTS {
                MATCH (:Document {course: $course})-[:HAS_CHUNK]->(:Chunk)-[:MENTIONS]->(a)
              }
            DELETE r
            """,
            course=course,
            origin=origin,
        )


def concepts_by_topic(course: str) -> dict[str, list[str]]:
    """Concepts grouped by the topic that teaches them, in teaching order."""
    with get_driver().session() as session:
        result = session.run(
            """
            MATCH (d:Document {course: $course})-[:HAS_CHUNK]->(:Chunk)-[:MENTIONS]->(e:Entity)
            WHERE d.position IS NOT NULL
            WITH d.topic AS topic, min(d.position) AS position,
                 collect(DISTINCT e.name) AS concepts
            RETURN topic, position, concepts
            ORDER BY position
            """,
            course=course,
        )
        return {record["topic"]: record["concepts"] for record in result}


def clear_document_positions(course: str) -> None:
    """Positions are recomputed from scratch, never accumulated."""
    with get_driver().session() as session:
        session.run(
            "MATCH (d:Document {course: $course}) REMOVE d.position", course=course
        )


def document_concepts(course: str) -> dict[str, list[str]]:
    """Every document in the course, with the concepts its chunks mention."""
    with get_driver().session() as session:
        result = session.run(
            """
            MATCH (d:Document {course: $course})
            OPTIONAL MATCH (d)-[:HAS_CHUNK]->(:Chunk)-[:MENTIONS]->(e:Entity)
            RETURN d.id AS id, collect(DISTINCT e.name) AS concepts
            """,
            course=course,
        )
        return {record["id"]: [c for c in record["concepts"] if c] for record in result}


def similarity_search(query: str, top_k: int = 6) -> list[dict]:
    query_embedding = embed_text(query)
    with get_driver().session() as session:
        result = session.run(
            f"""
            CALL db.index.vector.queryNodes('{VECTOR_INDEX}', $top_k, $embedding)
            YIELD node, score
            MATCH (d:Document)-[:HAS_CHUNK]->(node)
            RETURN node.id AS chunk_id,
                   node.text AS text,
                   node.page AS page,
                   d.id AS document_id,
                   d.title AS document_title,
                   d.topic AS topic,
                   score
            ORDER BY score DESC
            """,
            top_k=top_k,
            embedding=query_embedding,
        )
        return [record.data() for record in result]
