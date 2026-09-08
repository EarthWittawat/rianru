# Task List: Personal Learning Tool (CPE393 MVP)

Plan: `tasks/plan.md` · Spec: `docs/SPEC-learning-tool.md`

---

## Phase 1: Foundation

### Task 1: Neo4j via Docker Compose ✅
**Description:** Add a `docker-compose.yml` at repo root defining a `neo4j:5.15` (or later) Community service with Bolt (7687) and HTTP (7474) ports exposed, a named volume for data, and auth credentials read from `.env`.

**Acceptance criteria:**
- [x] `docker compose up -d neo4j` starts a healthy container
- [x] Neo4j Browser reachable at `http://localhost:7474`
- [x] Vector index syntax (`CREATE VECTOR INDEX ...`) succeeds against a scratch node

**Verification:**
- [x] Manual: `docker compose ps` shows `neo4j` healthy
- [x] Manual: ran `CREATE VECTOR INDEX ... FOR (n:ScratchTest) ON (n.embedding)` via cypher-shell — index reached `POPULATING`/would go `ONLINE`; scratch node + index cleaned up after

**Dependencies:** None

**Files likely touched:** `docker-compose.yml`

**Estimated scope:** Small: 1 file

---

### Task 2: FastAPI backend skeleton + Neo4j connection ✅
**Description:** Scaffold `server/` with FastAPI app, `.env` loading (`VLLM_URL`, `VLLM_MODEL`, `VLLM_API_KEY`, Neo4j creds), a Neo4j driver service, and a `/health` endpoint that round-trips a Neo4j query.

**Acceptance criteria:**
- [x] `uvicorn app.main:app --reload --port 8000` runs
- [x] `GET /health` returns 200 and confirms Neo4j connectivity
- [x] Config loaded from `.env` via `pydantic-settings` (no hardcoded secrets)

**Verification:**
- [x] `pytest` (1 test, real Neo4j connectivity check) passes
- [x] Manual: `curl localhost:8000/health` returns `{"neo4j": "ok"}`; `ruff check .` clean

**Dependencies:** Task 1

**Files likely touched:** `server/app/main.py`, `server/app/config.py`, `server/app/services/neo4j_client.py`, `server/tests/test_health.py`

**Estimated scope:** Small: 3 files

---

### Task 3: Next.js frontend skeleton ✅
**Description:** Scaffold `web/` with Next.js App Router, TypeScript, Tailwind. Add a shared layout with nav links to `/viewer`, `/graph`, `/chat`, `/quiz` (stub pages, placeholder content).

**Note:** scaffolded on Next.js 16.3.4 (not 14) — `params` is a Promise in this version, relevant for Task 10's dynamic route.

**Acceptance criteria:**
- [x] `npm run dev` serves the app at `localhost:3000`
- [x] Nav links route to all four stub pages without error

**Verification:**
- [x] `npm run lint` passes
- [x] `npm test` — NavBar renders all links, marks active route (2 tests)
- [x] `npm run build` clean, all 6 routes prerendered

**Dependencies:** None (parallel with Task 1/2)

**Files likely touched:** `web/app/layout.tsx`, `web/app/viewer/page.tsx`, `web/app/graph/page.tsx`, `web/app/chat/page.tsx`, `web/app/quiz/page.tsx`

**Estimated scope:** Small: 5 files

---

## Checkpoint: Foundation
- [x] `docker compose up -d neo4j` runs cleanly, Bolt reachable
- [x] Backend `/health` confirms Neo4j connectivity
- [x] Frontend dev server renders shell with working nav
- [x] **Reviewed** — user approved the autonomous run of Tasks 3-20

---

## Phase 2: Ingestion Pipeline

### Task 4: PDF/notebook parsing + chunking ✅
**Description:** Pure-logic service that takes a file path (PDF or `.ipynb`) and returns a list of text chunks with metadata (source file, page number if PDF, cell index if notebook). No I/O to Neo4j here — this is unit-testable in isolation.

**Acceptance criteria:**
- [x] Given a CPE393 lecture PDF, returns non-empty chunks with page numbers
- [x] Given a lab `.ipynb`, returns chunks from markdown + code cells with cell index
- [x] Chunk size is configurable (default 1500 chars, 200 char overlap)
- [x] `.md` supported too (lab/quiz `description.md` files listed in `manifest.json`)

**Verification:**
- [x] `pytest tests/test_chunking.py` — 5 tests against real CPE393 PDF + notebook
- [x] Manual: `L2 - Pattern Matching.pdf` → 22 chunks over 22 pages, slide bullet structure preserved; `Lab1_regex.ipynb` → 38 chunks across markdown + code cells

**Note:** Windows console is cp1252 — ingest script output must force UTF-8 or it crashes on bullet glyphs (`●`) in slide text.

**Dependencies:** Task 2

**Files likely touched:** `server/app/services/chunking.py`, `server/tests/test_chunking.py`

**Estimated scope:** Medium: 2 files

---

### Task 5: Embedding service + Neo4j Document/Chunk write + vector index
**Description:** Wrap `sentence-transformers` (`all-MiniLM-L6-v2`) as an embedding service. Write `Document` and `Chunk` nodes to Neo4j (`Document -[:HAS_CHUNK]-> Chunk`), store `Chunk.embedding`, and create the vector index over it.

**Acceptance criteria:**
- [x] Embedding service returns a fixed-dim vector for a given text
- [x] Writing a document's chunks creates one `Document` node + N `Chunk` nodes with correct relationships
- [x] Vector index exists and a similarity query returns the source chunk for a near-duplicate query string

**Verification:**
- [x] `pytest server/tests/test_embeddings.py` (unit, mocked model ok for speed) passes
- [x] Manual: run against 1 file, query Neo4j Browser for the resulting nodes

**Dependencies:** Task 1, Task 4

**Files likely touched:** `server/app/services/embeddings.py`, `server/app/services/neo4j_client.py` (extend), `server/tests/test_embeddings.py`

**Estimated scope:** Medium: 3 files

---

### Task 6: vLLM client service + prompt templates
**Description:** Thin async client wrapping `VLLM_URL`/`VLLM_MODEL`/`VLLM_API_KEY` for chat completions. Add a `prompts/` module with templates for: explanation, entity/relation extraction (structured JSON), quiz generation, chat-tutor system prompt.

**Acceptance criteria:**
- [x] Client sends a chat completion request and returns the model's text
- [x] Errors (timeout, non-200) surface as a typed exception, not a silent failure

**Verification:**
- [x] `pytest server/tests/test_vllm_client.py` (mocked HTTP) passes
- [x] Manual: one live call against the real gateway, confirm response

**Dependencies:** Task 2

**Files likely touched:** `server/app/services/vllm_client.py`, `server/app/prompts/*.py`, `server/tests/test_vllm_client.py`

**Estimated scope:** Small: 3 files

---

### Task 7: Entity/relation extraction → Neo4j Entity nodes
**Description:** For each chunk, prompt vLLM (via Task 6's client) to extract entities and relations as structured JSON; validate the JSON; write `Entity` nodes and `Chunk -[:MENTIONS]-> Entity` (plus `Entity -[:RELATES_TO]-> Entity` where the model returns a relation).

**Acceptance criteria:**
- [x] Malformed LLM JSON is logged and skipped, not fatal to the run
- [x] At least one entity extracted per non-trivial chunk in a sample lecture PDF
- [x] Duplicate entity names within a document are merged (`MERGE`, not `CREATE`)

**Verification:**
- [x] `pytest server/tests/test_entity_extraction.py` (mocked vLLM responses, incl. one malformed case) passes
- [x] Manual: run against `L2 - Pattern Matching.pdf`, inspect resulting `Entity` nodes in Neo4j Browser

**Dependencies:** Task 5, Task 6

**Files likely touched:** `server/app/services/entity_extraction.py`, `server/tests/test_entity_extraction.py`

**Estimated scope:** Medium: 2 files

---

### Task 8: `scripts/ingest.py` CLI wiring
**Description:** CLI that reads `manifest.json`, filters to `--class CPE393`, walks its `assessment_activities` + `learning_activities` file lists, and runs each file through chunking → embedding/write → entity extraction, with progress logging.

**Acceptance criteria:**
- [x] `python scripts/ingest.py --class CPE393` processes every file listed for CPE393 in `manifest.json`
- [x] Re-running is idempotent (uses `MERGE`, doesn't duplicate nodes)
- [x] Prints a summary (files processed, chunks created, entities created, any skipped/errored files)

**Verification:**
- [x] Manual: full run against CPE393, confirm summary counts look sane
- [x] Manual: re-run, confirm node counts unchanged (idempotency)

**Dependencies:** Task 4, Task 5, Task 7

**Files likely touched:** `server/scripts/ingest.py`

**Estimated scope:** Small: 1 file

---

## Checkpoint: Ingestion
- [x] `python scripts/ingest.py --class CPE393` completes without error
- [x] Neo4j contains Document/Chunk/Entity nodes + vector index covering every CPE393 file in `manifest.json` (spec Success Criteria #2)
- [x] Manual: spot-query Neo4j Browser, counts match manifest file list
- [x] **Reviewed** — user approved the autonomous run of Tasks 3-20

---

## Phase 3: PDF Viewer + Explain + Highlight

### Task 9: Backend `/documents` list + serve endpoints
**Description:** `GET /documents` lists ingested `Document` nodes (title, topic, file type). `GET /documents/{id}/file` streams the original PDF from its path under the CPE393 folder (read-only).

**Acceptance criteria:**
- [x] `/documents` returns all ingested CPE393 documents with metadata
- [x] `/documents/{id}/file` streams a valid PDF the browser can render

**Verification:**
- [x] `pytest server/tests/test_documents.py` passes
- [x] Manual: `curl` the file endpoint, confirm valid PDF bytes

**Dependencies:** Checkpoint: Ingestion

**Files likely touched:** `server/app/routers/documents.py`, `server/tests/test_documents.py`

**Estimated scope:** Small: 2 files

---

### Task 10: Frontend PDF viewer page (selectable text)
**Description:** `/viewer/[docId]` page using `react-pdf`/pdf.js to render the PDF from `/documents/{id}/file`, with a document picker (from `/documents`) and a working text layer (native browser selection).

**Acceptance criteria:**
- [x] Selecting a document from the list renders its PDF
- [x] Text in the PDF is selectable (not just an image)

**Verification:**
- [x] `npm test` (component test rendering a mock PDF) passes
- [x] Manual: open a real CPE393 PDF, select a sentence

**Dependencies:** Task 3, Task 9

**Files likely touched:** `web/app/viewer/[docId]/page.tsx`, `web/components/PdfViewer.tsx`

**Estimated scope:** Medium: 2 files

---

### Task 11: Backend `POST /explain`
**Description:** Accepts `{chunk_id, selected_text}`, fetches the source chunk's surrounding context from Neo4j, prompts vLLM (Task 6 client) for a grounded explanation, returns it.

**Acceptance criteria:**
- [x] Given a valid chunk_id + selection, returns a non-empty explanation string
- [x] Explanation prompt includes the chunk's surrounding text as context (not just the selection alone)

**Verification:**
- [x] `pytest server/tests/test_explain.py` (mocked vLLM) passes
- [x] Manual: real call against a CPE393 chunk

**Dependencies:** Task 6, Checkpoint: Ingestion

**Files likely touched:** `server/app/routers/explain.py`, `server/app/models/explain.py`, `server/tests/test_explain.py`

**Estimated scope:** Small: 3 files

---

### Task 12: Frontend explain side panel
**Description:** On text selection in the viewer, show a "Explain" affordance; clicking it calls `POST /explain` and renders the result in a side panel (`HighlightPanel` component).

**Acceptance criteria:**
- [x] Selecting text and clicking "Explain" shows a loading state, then the explanation
- [x] Panel shows the originally selected text alongside the explanation

**Verification:**
- [x] `npm test` for `HighlightPanel` passes
- [x] Manual: select → explain round-trip in browser

**Dependencies:** Task 10, Task 11

**Files likely touched:** `web/components/HighlightPanel.tsx`, `web/app/viewer/[docId]/page.tsx`

**Estimated scope:** Small: 2 files

---

## Checkpoint: Viewer + Explain
- [x] Manual: open a CPE393 PDF, select text, get grounded explanation in side panel (spec Success Criteria #3-4)

---

### Task 13: Backend `POST /highlights`
**Description:** Accepts `{chunk_id, selected_text, explanation}`, creates a `Highlight` node linked `Chunk -[:EXPLAINS]-> Highlight` (or equivalent direction per schema) and `Highlight -[:MENTIONS]-> Entity` for any entities recognized in the selection.

**Acceptance criteria:**
- [x] Saving a highlight creates exactly one `Highlight` node with correct relationships
- [x] If the selected text overlaps a known `Entity`, the `MENTIONS` relationship is created

**Verification:**
- [x] `pytest server/tests/test_highlights.py` passes
- [x] Manual: Neo4j Browser query confirms the new node/edges

**Dependencies:** Checkpoint: Ingestion, Task 11

**Files likely touched:** `server/app/routers/highlights.py`, `server/app/models/highlight.py`, `server/tests/test_highlights.py`

**Estimated scope:** Small: 3 files

---

### Task 14: Frontend "Save highlight" wiring
**Description:** Add a "Save highlight" button to `HighlightPanel`; on click, calls `POST /highlights` and shows a saved confirmation state.

**Acceptance criteria:**
- [x] Clicking "Save highlight" persists it and updates the button to a "Saved" state
- [x] Errors (network/API failure) show a visible message, not a silent no-op

**Verification:**
- [x] `npm test` for the save interaction passes
- [x] Manual: save a highlight, confirm via Task 13's verification query

**Dependencies:** Task 12, Task 13

**Files likely touched:** `web/components/HighlightPanel.tsx`

**Estimated scope:** Small: 1 file

---

## Checkpoint: Highlight loop
- [x] Manual: save a highlight, confirm `Highlight` node + relationships exist in Neo4j (spec Success Criteria #5)
- [x] **Reviewed** — user approved the autonomous run of Tasks 3-20

---

## Phase 4: Knowledge Graph

### Task 15: Backend `GET /graph`
**Description:** Returns nodes + edges (Document/Chunk/Entity/Highlight and their relationships) in a shape a force-graph library can consume, with an optional `?topic=` filter.

**Acceptance criteria:**
- [x] Returns valid `{nodes: [...], edges: [...]}` for the full CPE393 graph
- [x] `?topic=` filters to nodes reachable from that topic's documents

**Verification:**
- [x] `pytest server/tests/test_graph.py` passes
- [x] Manual: `curl /graph` and `/graph?topic=...`, sanity-check shape

**Dependencies:** Checkpoint: Highlight loop

**Files likely touched:** `server/app/routers/graph.py`, `server/tests/test_graph.py`

**Estimated scope:** Small: 2 files

---

### Task 16: Frontend `/graph` page
**Description:** Render `GET /graph` data with `react-force-graph-2d`, color-coded by node type, topic filter dropdown, click-through from a node to its source document/highlight.

**Acceptance criteria:**
- [x] Graph renders real ingested + highlight data
- [x] Clicking a node navigates to (or previews) its source

**Verification:**
- [x] `npm test` for graph data-to-render mapping passes
- [x] Manual: click through several node types

**Dependencies:** Task 3, Task 15

**Files likely touched:** `web/app/graph/page.tsx`, `web/components/KnowledgeGraph.tsx`

**Estimated scope:** Medium: 2 files

---

## Checkpoint: Graph
- [x] Manual: `/graph` shows real ingested + highlight data; clicking a node surfaces its source (spec Success Criteria #6)

---

## Phase 5: Chat Tutor (RAG)

### Task 17: Backend `POST /chat`
**Description:** Accepts `{message, history?}`; embeds the message, runs a Neo4j vector-index similarity search for top-k chunks, builds a context block, prompts vLLM with the chat-tutor system prompt (Task 6), returns the grounded answer.

**Acceptance criteria:**
- [x] Answer is built from retrieved chunk text, not the raw question alone (verify via a question whose answer only appears in one specific lecture)
- [x] Returns retrieved chunk references alongside the answer (for later citation display)

**Verification:**
- [x] `pytest server/tests/test_chat.py` (mocked vLLM, real Neo4j vector search) passes
- [x] Manual: ask a CPE393-specific question, confirm grounded answer

**Dependencies:** Task 5, Task 6, Checkpoint: Ingestion

**Files likely touched:** `server/app/routers/chat.py`, `server/app/services/retrieval.py`, `server/tests/test_chat.py`

**Estimated scope:** Medium: 3 files

---

### Task 18: Frontend `/chat` page
**Description:** Simple chat UI — message list, input box, calls `POST /chat`, renders streamed or one-shot response.

**Acceptance criteria:**
- [x] Sending a message shows it in the thread, then the tutor's response
- [x] Loading/error states are visible, not silent

**Verification:**
- [x] `npm test` for the chat component passes
- [x] Manual: full conversation round-trip in browser

**Dependencies:** Task 3, Task 17

**Files likely touched:** `web/app/chat/page.tsx`, `web/components/ChatThread.tsx`

**Estimated scope:** Small: 2 files

---

## Checkpoint: Chat
- [x] Manual: chat answers a CPE393 question using retrieved chunks, not generic knowledge (spec Success Criteria #7)

---

## Phase 6: Quiz / Flashcards

### Task 19: Backend `POST /quiz/generate`
**Description:** Accepts `{topic}`; fetches that topic's chunks, prompts vLLM to generate N mixed multiple-choice/short-answer questions with answers, stores `QuizQuestion` nodes linked to source chunks, returns the set.

**Acceptance criteria:**
- [x] Generated questions reference real content from the topic's chunks (spot-checkable)
- [x] Both question formats appear across a generated set
- [x] Questions persisted as `QuizQuestion` nodes, re-fetchable without regenerating

**Verification:**
- [x] `pytest server/tests/test_quiz.py` (mocked vLLM) passes
- [x] Manual: generate for "Pattern Matching," eyeball question quality against `L2 - Pattern Matching.pdf`

**Dependencies:** Task 6, Checkpoint: Ingestion

**Files likely touched:** `server/app/routers/quiz.py`, `server/app/models/quiz.py`, `server/tests/test_quiz.py`

**Estimated scope:** Medium: 3 files

---

### Task 20: Frontend `/quiz` page
**Description:** Topic picker → generate/fetch questions → render with reveal (for short-answer) or select-and-check (for multiple-choice) interaction.

**Acceptance criteria:**
- [x] Picking a topic and generating shows a working question set
- [x] Reveal/self-check interaction works for both question types

**Verification:**
- [x] `npm test` for the quiz component passes
- [x] Manual: run through a generated quiz set

**Dependencies:** Task 3, Task 19

**Files likely touched:** `web/app/quiz/page.tsx`, `web/components/QuizCard.tsx`

**Estimated scope:** Medium: 2 files

---

## Checkpoint: Complete
- [x] Manual: `/quiz` generates topic questions, reveal/self-check works (spec Success Criteria #8)
- [x] All 8 spec Success Criteria walked through end-to-end in one sitting
- [x] Ready for review


---

## Completion record

All 20 tasks completed and committed individually, each with its own tests.

- Backend: 50 pytest tests passing (`cd server && .venv/Scripts/python.exe -m pytest`)
- Frontend: 8 Vitest tests passing, `npm run lint` and `npm run build` clean
- Ingest: 19 documents, 504 chunks, 715 distinct entities, 1557 entity mentions,
  0 skipped — matching the 19 ingestable CPE393 files in `manifest.json`
- All 8 spec success criteria walked through in a real browser, not just tests

### Bugs found by running it, not by testing it

1. **Rate limits were silently dropping data.** The gateway caps parallel
   requests per key at 3; the first ingest ran 8 workers, and because entity
   extraction treats a failed call as "no entities", most chunks were being
   dropped from the graph instead of retried. Now retries with backoff.
2. **Re-ingesting destroyed saved highlights.** `write_document` replaces a
   document's chunks, which orphaned every highlight hanging off them — the
   student's own work, silently lost on any re-run. Highlights now carry
   `document_id` and `chunk_index` and are re-attached, with a regression test.
3. **pdfjs-dist version mismatch.** react-pdf's bundled API rejects a
   mismatched worker; pinned to 5.4.296.
4. **CORS was pinned to port 3000**, which Grafana already holds on this
   machine, so Next fell back to 3001 and every request failed.
5. **Graph nodes rendered ~2px** with the default area scaling — unreadable
   and effectively unclickable.

### Known limitations

- Retrieval is text-only. Figures, tables and slide layout are not searchable
  (ColBERT/ColQwen deferred — no local GPU; see the spec's Resolved Decisions).
- Some notebook code cells yield no entities: the model answers
  conversationally instead of returning JSON. Handled, but those chunks add
  nothing to the graph.
- Highlight re-attachment anchors on chunk index, so if a source file itself
  changes, a highlight may land on a shifted chunk.
- No course other than CPE393 is ingested; the ingest CLI takes `--class` and
  would work, but nothing else was verified against them.
