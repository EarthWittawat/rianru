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
- [ ] `docker compose up -d neo4j` runs cleanly, Bolt reachable
- [ ] Backend `/health` confirms Neo4j connectivity
- [ ] Frontend dev server renders shell with working nav
- [ ] **Review with human before proceeding**

---

## Phase 2: Ingestion Pipeline

### Task 4: PDF/notebook parsing + chunking
**Description:** Pure-logic service that takes a file path (PDF or `.ipynb`) and returns a list of text chunks with metadata (source file, page number if PDF, cell index if notebook). No I/O to Neo4j here — this is unit-testable in isolation.

**Acceptance criteria:**
- [ ] Given a CPE393 lecture PDF, returns non-empty chunks with page numbers
- [ ] Given a lab `.ipynb`, returns chunks from markdown + code cells with cell index
- [ ] Chunk size is configurable (default ~500 tokens, with overlap)

**Verification:**
- [ ] `pytest server/tests/test_chunking.py` passes against 2-3 real CPE393 files
- [ ] Manual: print chunk count/lengths for `L1 - Intro.pdf`

**Dependencies:** Task 2

**Files likely touched:** `server/app/services/chunking.py`, `server/tests/test_chunking.py`

**Estimated scope:** Medium: 2 files

---

### Task 5: Embedding service + Neo4j Document/Chunk write + vector index
**Description:** Wrap `sentence-transformers` (`all-MiniLM-L6-v2`) as an embedding service. Write `Document` and `Chunk` nodes to Neo4j (`Document -[:HAS_CHUNK]-> Chunk`), store `Chunk.embedding`, and create the vector index over it.

**Acceptance criteria:**
- [ ] Embedding service returns a fixed-dim vector for a given text
- [ ] Writing a document's chunks creates one `Document` node + N `Chunk` nodes with correct relationships
- [ ] Vector index exists and a similarity query returns the source chunk for a near-duplicate query string

**Verification:**
- [ ] `pytest server/tests/test_embeddings.py` (unit, mocked model ok for speed) passes
- [ ] Manual: run against 1 file, query Neo4j Browser for the resulting nodes

**Dependencies:** Task 1, Task 4

**Files likely touched:** `server/app/services/embeddings.py`, `server/app/services/neo4j_client.py` (extend), `server/tests/test_embeddings.py`

**Estimated scope:** Medium: 3 files

---

### Task 6: vLLM client service + prompt templates
**Description:** Thin async client wrapping `VLLM_URL`/`VLLM_MODEL`/`VLLM_API_KEY` for chat completions. Add a `prompts/` module with templates for: explanation, entity/relation extraction (structured JSON), quiz generation, chat-tutor system prompt.

**Acceptance criteria:**
- [ ] Client sends a chat completion request and returns the model's text
- [ ] Errors (timeout, non-200) surface as a typed exception, not a silent failure

**Verification:**
- [ ] `pytest server/tests/test_vllm_client.py` (mocked HTTP) passes
- [ ] Manual: one live call against the real gateway, confirm response

**Dependencies:** Task 2

**Files likely touched:** `server/app/services/vllm_client.py`, `server/app/prompts/*.py`, `server/tests/test_vllm_client.py`

**Estimated scope:** Small: 3 files

---

### Task 7: Entity/relation extraction → Neo4j Entity nodes
**Description:** For each chunk, prompt vLLM (via Task 6's client) to extract entities and relations as structured JSON; validate the JSON; write `Entity` nodes and `Chunk -[:MENTIONS]-> Entity` (plus `Entity -[:RELATES_TO]-> Entity` where the model returns a relation).

**Acceptance criteria:**
- [ ] Malformed LLM JSON is logged and skipped, not fatal to the run
- [ ] At least one entity extracted per non-trivial chunk in a sample lecture PDF
- [ ] Duplicate entity names within a document are merged (`MERGE`, not `CREATE`)

**Verification:**
- [ ] `pytest server/tests/test_entity_extraction.py` (mocked vLLM responses, incl. one malformed case) passes
- [ ] Manual: run against `L2 - Pattern Matching.pdf`, inspect resulting `Entity` nodes in Neo4j Browser

**Dependencies:** Task 5, Task 6

**Files likely touched:** `server/app/services/entity_extraction.py`, `server/tests/test_entity_extraction.py`

**Estimated scope:** Medium: 2 files

---

### Task 8: `scripts/ingest.py` CLI wiring
**Description:** CLI that reads `manifest.json`, filters to `--class CPE393`, walks its `assessment_activities` + `learning_activities` file lists, and runs each file through chunking → embedding/write → entity extraction, with progress logging.

**Acceptance criteria:**
- [ ] `python scripts/ingest.py --class CPE393` processes every file listed for CPE393 in `manifest.json`
- [ ] Re-running is idempotent (uses `MERGE`, doesn't duplicate nodes)
- [ ] Prints a summary (files processed, chunks created, entities created, any skipped/errored files)

**Verification:**
- [ ] Manual: full run against CPE393, confirm summary counts look sane
- [ ] Manual: re-run, confirm node counts unchanged (idempotency)

**Dependencies:** Task 4, Task 5, Task 7

**Files likely touched:** `server/scripts/ingest.py`

**Estimated scope:** Small: 1 file

---

## Checkpoint: Ingestion
- [ ] `python scripts/ingest.py --class CPE393` completes without error
- [ ] Neo4j contains Document/Chunk/Entity nodes + vector index covering every CPE393 file in `manifest.json` (spec Success Criteria #2)
- [ ] Manual: spot-query Neo4j Browser, counts match manifest file list
- [ ] **Review with human before proceeding**

---

## Phase 3: PDF Viewer + Explain + Highlight

### Task 9: Backend `/documents` list + serve endpoints
**Description:** `GET /documents` lists ingested `Document` nodes (title, topic, file type). `GET /documents/{id}/file` streams the original PDF from its path under the CPE393 folder (read-only).

**Acceptance criteria:**
- [ ] `/documents` returns all ingested CPE393 documents with metadata
- [ ] `/documents/{id}/file` streams a valid PDF the browser can render

**Verification:**
- [ ] `pytest server/tests/test_documents.py` passes
- [ ] Manual: `curl` the file endpoint, confirm valid PDF bytes

**Dependencies:** Checkpoint: Ingestion

**Files likely touched:** `server/app/routers/documents.py`, `server/tests/test_documents.py`

**Estimated scope:** Small: 2 files

---

### Task 10: Frontend PDF viewer page (selectable text)
**Description:** `/viewer/[docId]` page using `react-pdf`/pdf.js to render the PDF from `/documents/{id}/file`, with a document picker (from `/documents`) and a working text layer (native browser selection).

**Acceptance criteria:**
- [ ] Selecting a document from the list renders its PDF
- [ ] Text in the PDF is selectable (not just an image)

**Verification:**
- [ ] `npm test` (component test rendering a mock PDF) passes
- [ ] Manual: open a real CPE393 PDF, select a sentence

**Dependencies:** Task 3, Task 9

**Files likely touched:** `web/app/viewer/[docId]/page.tsx`, `web/components/PdfViewer.tsx`

**Estimated scope:** Medium: 2 files

---

### Task 11: Backend `POST /explain`
**Description:** Accepts `{chunk_id, selected_text}`, fetches the source chunk's surrounding context from Neo4j, prompts vLLM (Task 6 client) for a grounded explanation, returns it.

**Acceptance criteria:**
- [ ] Given a valid chunk_id + selection, returns a non-empty explanation string
- [ ] Explanation prompt includes the chunk's surrounding text as context (not just the selection alone)

**Verification:**
- [ ] `pytest server/tests/test_explain.py` (mocked vLLM) passes
- [ ] Manual: real call against a CPE393 chunk

**Dependencies:** Task 6, Checkpoint: Ingestion

**Files likely touched:** `server/app/routers/explain.py`, `server/app/models/explain.py`, `server/tests/test_explain.py`

**Estimated scope:** Small: 3 files

---

### Task 12: Frontend explain side panel
**Description:** On text selection in the viewer, show a "Explain" affordance; clicking it calls `POST /explain` and renders the result in a side panel (`HighlightPanel` component).

**Acceptance criteria:**
- [ ] Selecting text and clicking "Explain" shows a loading state, then the explanation
- [ ] Panel shows the originally selected text alongside the explanation

**Verification:**
- [ ] `npm test` for `HighlightPanel` passes
- [ ] Manual: select → explain round-trip in browser

**Dependencies:** Task 10, Task 11

**Files likely touched:** `web/components/HighlightPanel.tsx`, `web/app/viewer/[docId]/page.tsx`

**Estimated scope:** Small: 2 files

---

## Checkpoint: Viewer + Explain
- [ ] Manual: open a CPE393 PDF, select text, get grounded explanation in side panel (spec Success Criteria #3-4)

---

### Task 13: Backend `POST /highlights`
**Description:** Accepts `{chunk_id, selected_text, explanation}`, creates a `Highlight` node linked `Chunk -[:EXPLAINS]-> Highlight` (or equivalent direction per schema) and `Highlight -[:MENTIONS]-> Entity` for any entities recognized in the selection.

**Acceptance criteria:**
- [ ] Saving a highlight creates exactly one `Highlight` node with correct relationships
- [ ] If the selected text overlaps a known `Entity`, the `MENTIONS` relationship is created

**Verification:**
- [ ] `pytest server/tests/test_highlights.py` passes
- [ ] Manual: Neo4j Browser query confirms the new node/edges

**Dependencies:** Checkpoint: Ingestion, Task 11

**Files likely touched:** `server/app/routers/highlights.py`, `server/app/models/highlight.py`, `server/tests/test_highlights.py`

**Estimated scope:** Small: 3 files

---

### Task 14: Frontend "Save highlight" wiring
**Description:** Add a "Save highlight" button to `HighlightPanel`; on click, calls `POST /highlights` and shows a saved confirmation state.

**Acceptance criteria:**
- [ ] Clicking "Save highlight" persists it and updates the button to a "Saved" state
- [ ] Errors (network/API failure) show a visible message, not a silent no-op

**Verification:**
- [ ] `npm test` for the save interaction passes
- [ ] Manual: save a highlight, confirm via Task 13's verification query

**Dependencies:** Task 12, Task 13

**Files likely touched:** `web/components/HighlightPanel.tsx`

**Estimated scope:** Small: 1 file

---

## Checkpoint: Highlight loop
- [ ] Manual: save a highlight, confirm `Highlight` node + relationships exist in Neo4j (spec Success Criteria #5)
- [ ] **Review with human before proceeding**

---

## Phase 4: Knowledge Graph

### Task 15: Backend `GET /graph`
**Description:** Returns nodes + edges (Document/Chunk/Entity/Highlight and their relationships) in a shape a force-graph library can consume, with an optional `?topic=` filter.

**Acceptance criteria:**
- [ ] Returns valid `{nodes: [...], edges: [...]}` for the full CPE393 graph
- [ ] `?topic=` filters to nodes reachable from that topic's documents

**Verification:**
- [ ] `pytest server/tests/test_graph.py` passes
- [ ] Manual: `curl /graph` and `/graph?topic=...`, sanity-check shape

**Dependencies:** Checkpoint: Highlight loop

**Files likely touched:** `server/app/routers/graph.py`, `server/tests/test_graph.py`

**Estimated scope:** Small: 2 files

---

### Task 16: Frontend `/graph` page
**Description:** Render `GET /graph` data with `react-force-graph-2d`, color-coded by node type, topic filter dropdown, click-through from a node to its source document/highlight.

**Acceptance criteria:**
- [ ] Graph renders real ingested + highlight data
- [ ] Clicking a node navigates to (or previews) its source

**Verification:**
- [ ] `npm test` for graph data-to-render mapping passes
- [ ] Manual: click through several node types

**Dependencies:** Task 3, Task 15

**Files likely touched:** `web/app/graph/page.tsx`, `web/components/KnowledgeGraph.tsx`

**Estimated scope:** Medium: 2 files

---

## Checkpoint: Graph
- [ ] Manual: `/graph` shows real ingested + highlight data; clicking a node surfaces its source (spec Success Criteria #6)

---

## Phase 5: Chat Tutor (RAG)

### Task 17: Backend `POST /chat`
**Description:** Accepts `{message, history?}`; embeds the message, runs a Neo4j vector-index similarity search for top-k chunks, builds a context block, prompts vLLM with the chat-tutor system prompt (Task 6), returns the grounded answer.

**Acceptance criteria:**
- [ ] Answer is built from retrieved chunk text, not the raw question alone (verify via a question whose answer only appears in one specific lecture)
- [ ] Returns retrieved chunk references alongside the answer (for later citation display)

**Verification:**
- [ ] `pytest server/tests/test_chat.py` (mocked vLLM, real Neo4j vector search) passes
- [ ] Manual: ask a CPE393-specific question, confirm grounded answer

**Dependencies:** Task 5, Task 6, Checkpoint: Ingestion

**Files likely touched:** `server/app/routers/chat.py`, `server/app/services/retrieval.py`, `server/tests/test_chat.py`

**Estimated scope:** Medium: 3 files

---

### Task 18: Frontend `/chat` page
**Description:** Simple chat UI — message list, input box, calls `POST /chat`, renders streamed or one-shot response.

**Acceptance criteria:**
- [ ] Sending a message shows it in the thread, then the tutor's response
- [ ] Loading/error states are visible, not silent

**Verification:**
- [ ] `npm test` for the chat component passes
- [ ] Manual: full conversation round-trip in browser

**Dependencies:** Task 3, Task 17

**Files likely touched:** `web/app/chat/page.tsx`, `web/components/ChatThread.tsx`

**Estimated scope:** Small: 2 files

---

## Checkpoint: Chat
- [ ] Manual: chat answers a CPE393 question using retrieved chunks, not generic knowledge (spec Success Criteria #7)

---

## Phase 6: Quiz / Flashcards

### Task 19: Backend `POST /quiz/generate`
**Description:** Accepts `{topic}`; fetches that topic's chunks, prompts vLLM to generate N mixed multiple-choice/short-answer questions with answers, stores `QuizQuestion` nodes linked to source chunks, returns the set.

**Acceptance criteria:**
- [ ] Generated questions reference real content from the topic's chunks (spot-checkable)
- [ ] Both question formats appear across a generated set
- [ ] Questions persisted as `QuizQuestion` nodes, re-fetchable without regenerating

**Verification:**
- [ ] `pytest server/tests/test_quiz.py` (mocked vLLM) passes
- [ ] Manual: generate for "Pattern Matching," eyeball question quality against `L2 - Pattern Matching.pdf`

**Dependencies:** Task 6, Checkpoint: Ingestion

**Files likely touched:** `server/app/routers/quiz.py`, `server/app/models/quiz.py`, `server/tests/test_quiz.py`

**Estimated scope:** Medium: 3 files

---

### Task 20: Frontend `/quiz` page
**Description:** Topic picker → generate/fetch questions → render with reveal (for short-answer) or select-and-check (for multiple-choice) interaction.

**Acceptance criteria:**
- [ ] Picking a topic and generating shows a working question set
- [ ] Reveal/self-check interaction works for both question types

**Verification:**
- [ ] `npm test` for the quiz component passes
- [ ] Manual: run through a generated quiz set

**Dependencies:** Task 3, Task 19

**Files likely touched:** `web/app/quiz/page.tsx`, `web/components/QuizCard.tsx`

**Estimated scope:** Medium: 2 files

---

## Checkpoint: Complete
- [ ] Manual: `/quiz` generates topic questions, reveal/self-check works (spec Success Criteria #8)
- [ ] All 8 spec Success Criteria walked through end-to-end in one sitting
- [ ] Ready for review
