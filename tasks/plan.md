# Implementation Plan: Personal Learning Tool (CPE393 MVP)

Source spec: `docs/SPEC-learning-tool.md`.

This plan covers the original MVP (Tasks 1-20), all complete. The work that
followed it — progress tracking and the multi-agent study coach — is tracked
in `tasks/study-coach.md`.

## Overview

Local Next.js + FastAPI + Neo4j app that ingests the CPE393 course folder,
then delivers one connected loop: view PDF → click term → AI explanation →
save as highlight → highlight appears in knowledge graph → chat tutor
answers grounded in the docs → quiz questions generated per topic. Built in
vertical slices, ingestion pipeline first since every other slice reads
data it produces.

## Architecture Decisions

- Ingestion runs as a standalone CLI (`scripts/ingest.py`), never inside a
  live API request — keeps the FastAPI process fast and avoids long-request
  timeouts, per spec boundaries.
- Neo4j is the only datastore — Document/Chunk/Entity/Highlight/QuizQuestion
  as nodes, dense embeddings on `Chunk` via Neo4j's native vector index. No
  second DB. (Amended 2026-09-08: personal quiz progress now lives in a
  separate local SQLite file. Neo4j remains the single source of truth for the
  course material itself — see the spec's Resolved Decisions.)
- vLLM API key stays server-side only; all vLLM calls go through FastAPI,
  never called directly from the browser.
- `manifest.json` is the source of truth for which files exist per class —
  ingestion reads it rather than walking the filesystem.

## Task List

### Phase 1: Foundation
- [x] Task 1: Neo4j via Docker Compose
- [x] Task 2: FastAPI backend skeleton + Neo4j connection
- [x] Task 3: Next.js frontend skeleton

### Checkpoint: Foundation
- [x] `docker compose up -d neo4j` runs cleanly, Bolt reachable
- [x] Backend `/health` confirms Neo4j connectivity
- [x] Frontend builds clean with nav to Viewer/Graph/Chat/Quiz (stub pages)
- [x] Reviewed — user approved autonomous run of Tasks 3-20

### Phase 2: Ingestion Pipeline
- [x] Task 4: PDF/notebook parsing + chunking (pure logic)
- [x] Task 5: Embedding service + Neo4j Document/Chunk write + vector index
- [x] Task 6: vLLM client service + prompt templates
- [x] Task 7: Entity/relation extraction → Neo4j Entity nodes
- [x] Task 8: `scripts/ingest.py` CLI wiring, run against CPE393

### Checkpoint: Ingestion
- [x] `python scripts/ingest.py --class CPE393` completes without error
- [x] Neo4j contains Document/Chunk/Entity nodes + vector index covering every file listed under CPE393 in `manifest.json` (spec Success Criteria #2)
- [x] Verified: 19 documents, 504 chunks, 715 distinct entities, 1557 entity mentions, 0 skipped — matches the 19 ingestable files in `manifest.json`

### Phase 3: PDF Viewer + Explain + Highlight
- [x] Task 9: Backend `/documents` list + serve endpoints
- [x] Task 10: Frontend PDF viewer page (selectable text)
- [x] Task 11: Backend `POST /explain`
- [x] Task 12: Frontend explain side panel

### Checkpoint: Viewer + Explain
- [x] Verified in browser: selected a passage in L2 Pattern Matching, got a grounded explanation citing page 2 (spec Success Criteria #3-4)

- [x] Task 13: Backend `POST /highlights`
- [x] Task 14: Frontend "Save highlight" wiring

### Checkpoint: Highlight loop
- [x] Verified in browser: saved a highlight, confirmed the `Highlight` node and its chunk relationship in Neo4j (spec Success Criteria #5)

### Phase 4: Knowledge Graph
- [x] Task 15: Backend `GET /graph` (nodes/edges, topic filter)
- [x] Task 16: Frontend `/graph` page (force-directed render, click-through)

### Checkpoint: Graph
- [x] Verified in browser: `/graph` renders the ingested graph and clicking a node shows its details (spec Success Criteria #6)

### Phase 5: Chat Tutor (RAG)
- [x] Task 17: Backend `POST /chat` (embed → vector search → context → vLLM)
- [x] Task 18: Frontend `/chat` page

### Checkpoint: Chat
- [x] Verified in browser: tutor answered TF-IDF from L6 and cited pages 19 and 27 (spec Success Criteria #7)

### Phase 6: Quiz / Flashcards
- [x] Task 19: Backend `POST /quiz/generate`
- [x] Task 20: Frontend `/quiz` page (reveal/self-check)

### Checkpoint: Complete
- [x] Verified in browser: `/quiz` generated questions from the intro lecture and self-check marks correct/incorrect (spec Success Criteria #8)
- [x] All 8 spec Success Criteria walked through end-to-end in a browser
- [x] Ready for review

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| PDF text extraction quality on slide decks (layout, figures) | Med | Use `pdfplumber`; accept imperfect extraction for MVP text-only retrieval; flag as known limitation (ColQwen deferred, see spec) |
| vLLM entity-extraction output isn't valid JSON | Med | Strict prompt + schema validation; skip/log malformed chunks rather than failing the whole ingest run |
| Browser text-selection granularity (word vs. sentence) awkward for click-to-explain | Low | Start with native browser selection (whatever the user drags over); refine later if it's unusable |
| Neo4j Docker image version lacks vector index support | Low | Pin image to `neo4j:5.15` or later at Task 1; verify at Foundation checkpoint |
| Embedding model download size/time on first run | Low | `all-MiniLM-L6-v2` is ~80MB; cache under a local model dir, document one-time download in README |

## Open Questions (carried from spec, non-blocking)

- Neo4j Community edition assumed sufficient — confirm at Task 1 checkpoint when the vector index is actually created.
- Tailwind CSS assumed for styling.
- Quiz format: both multiple-choice and short-answer, assumed at Task 19 — narrow if there's a preference.
- Graph rendering library: `react-force-graph-2d` assumed at Task 16; swap for `cytoscape.js` if preferred, no other impact.
