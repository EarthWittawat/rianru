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
