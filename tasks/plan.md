# Implementation Plan: Personal Learning Tool (CPE393 MVP)

Source spec: `docs/SPEC-learning-tool.md`.

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
  second DB.
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
- [ ] Task 8: `scripts/ingest.py` CLI wiring, run against CPE393

### Checkpoint: Ingestion
- [ ] `python scripts/ingest.py --class CPE393` completes without error
- [ ] Neo4j contains Document/Chunk/Entity nodes + vector index covering every file listed under CPE393 in `manifest.json` (spec Success Criteria #2)
- [ ] Manual check: spot-query Neo4j Browser, counts match manifest file list
- [ ] Review with human before proceeding

### Phase 3: PDF Viewer + Explain + Highlight
- [ ] Task 9: Backend `/documents` list + serve endpoints
- [ ] Task 10: Frontend PDF viewer page (selectable text)
- [ ] Task 11: Backend `POST /explain`
- [ ] Task 12: Frontend explain side panel

### Checkpoint: Viewer + Explain
- [ ] Manual: open a CPE393 PDF, select text, get grounded explanation in side panel (spec Success Criteria #3-4)

- [ ] Task 13: Backend `POST /highlights`
- [ ] Task 14: Frontend "Save highlight" wiring

### Checkpoint: Highlight loop
- [ ] Manual: save a highlight, confirm `Highlight` node + relationships exist in Neo4j (spec Success Criteria #5)
- [ ] Review with human before proceeding

### Phase 4: Knowledge Graph
- [ ] Task 15: Backend `GET /graph` (nodes/edges, topic filter)
- [ ] Task 16: Frontend `/graph` page (force-directed render, click-through)

### Checkpoint: Graph
- [ ] Manual: `/graph` shows real ingested + highlight data; clicking a node surfaces its source (spec Success Criteria #6)

### Phase 5: Chat Tutor (RAG)
- [ ] Task 17: Backend `POST /chat` (embed → vector search → context → vLLM)
- [ ] Task 18: Frontend `/chat` page

### Checkpoint: Chat
- [ ] Manual: chat answers a CPE393 question using retrieved chunks, not generic knowledge (spec Success Criteria #7)

### Phase 6: Quiz / Flashcards
- [ ] Task 19: Backend `POST /quiz/generate`
- [ ] Task 20: Frontend `/quiz` page (reveal/self-check)

### Checkpoint: Complete
- [ ] Manual: `/quiz` generates topic questions, reveal/self-check works (spec Success Criteria #8)
- [ ] All 8 spec Success Criteria walked through end-to-end in one session
- [ ] Ready for review

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
