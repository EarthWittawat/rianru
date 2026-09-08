# Spec: Personal Learning Tool (CPE393 MVP)

Source intent: `docs/intent/learning-tool.md` (confirmed via interview-me, 2026-09-07).

## Objective

A local, single-user web app that turns the user's existing CPE393 (Text
Analytics) course materials — PDFs, Jupyter notebooks, lab/quiz descriptions
— into an interactive study loop:

1. Read a source PDF in-browser.
2. Click a term/sentence → get an AI explanation grounded in the course
   material (via the user's existing vLLM endpoint).
3. Save that explanation as a highlight → it becomes a linked node in a
   visual knowledge graph (Neo4j).
4. Ask a chat tutor questions answered via retrieval over the ingested docs
   (RAG), not generic knowledge.
5. Generate quiz/flashcard questions from the material for exam prep.

**User:** the course's own student, running this on their own machine, for
personal study across the semester (no deadline pressure, no other users).

**Success looks like:** all five steps above work end-to-end against the
CPE393 folder specifically — see Success Criteria.

**Explicitly out of scope for this spec:** Vercel/cloud deployment, multi-user
or auth, mobile. (Support for more than one course *was* out of scope and is
now built — see Resolved Decisions.)

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS | "website," needs a PDF viewer with a text layer + a graph viz — React ecosystem covers both (`react-pdf`/pdf.js, a force-graph library) |
| Backend | Python 3.11 + FastAPI | PDF/notebook parsing, embeddings, Neo4j driver, and vLLM calls are all easier in Python; serves a REST API to the Next.js app on localhost |
| Database | Neo4j 5.x (Community, Docker) for course knowledge; SQLite for personal progress | Neo4j holds Documents, Chunks, Entities, Highlights and QuizQuestions — graph *and* vector index in one place. Personal progress (quiz attempts, scores, timestamps) is tabular time-series data and lives in a separate local SQLite file — see Resolved Decisions |
| Embeddings | `sentence-transformers` (local, e.g. `all-MiniLM-L6-v2`), single dense vector/chunk | vLLM gateway is chat-only; dense embeddings fit Neo4j's native vector index directly, no GPU needed. ColBERT (text late-interaction) / ColQwen (ColPali-style vision-language, page-as-image) considered and explicitly deferred — no local GPU, and both need multi-vector storage outside Neo4j (RAGatouille/PLAID or similar), which breaks "Neo4j = single source of truth." Documented as a future upgrade path once GPU is available, not MVP scope. |
| LLM | Existing vLLM gateway (`VLLM_URL`, `VLLM_MODEL`, `VLLM_API_KEY` in `D:\leb2\.env`) | Already provisioned — reused for explanations, chat tutor, entity/relation extraction, and quiz generation, all via prompted chat completions |
| PDF rendering | `pdf.js` / `react-pdf` | Text layer needed for click-to-select and highlight overlays |
| Graph viz | `react-force-graph-2d` (or `cytoscape.js`) | Force-directed rendering of Neo4j nodes/edges |
| Agent framework | LangChain 1.4 (`langchain`, `langchain-openai`) | The study coach is a supervisor agent whose tools are two specialist agents (progress, material) — subagents-as-tools, which LangChain recommends over the deprecated supervisor package. Multi-agent is a confirmed requirement, not an implementation detail: see `docs/intent/study-coach-agents.md` |

## Commands

```
# Neo4j (from repo root)
docker compose up -d neo4j
docker compose down

# Backend (from server/)
uvicorn app.main:app --reload --port 8000        # dev server
pytest                                            # tests
pytest -m "not slow"                              # skip tests that hit the vLLM gateway
ruff check . --fix                                # lint

# Ingestion (from server/, run manually — not inside a live request)
python scripts/ingest.py --class CPE393

# Frontend (from web/)
npm run dev                                       # dev server, port 3000
npm test                                           # component tests (Vitest + RTL)
npm run lint
```

## Project Structure

```
D:\leb2/
  .env                    → existing leb2 + vLLM credentials (never committed)
  manifest.json           → existing course/file index (read by ingest script);
                              local only, not committed — it lists the enrolled
                              classes and their assignments
  docker-compose.yml       → Neo4j service definition
  docs/
    intent/                → confirmed intents (interview-me output)
    SPEC-learning-tool.md   → this file
  server/                  → FastAPI backend
    app/
      main.py
      routers/             → explain.py, chat.py, graph.py, quiz.py, highlights.py,
                              progress.py, coach.py
      services/            → neo4j_client.py, vllm_client.py, embeddings.py, chunking.py,
                              progress.py (SQLite), study_plan.py
      agents/              → llm.py (gateway as a LangChain model), tools.py,
                              specialists.py (progress + material agents), coach.py
    data/                  → progress.db (SQLite, gitignored — personal, not course data)
      models/              → pydantic schemas
    scripts/
      ingest.py            → parses manifest.json → PDFs/ipynb → chunks → embeds →
                              extracts entities/relations via vLLM → writes to Neo4j
    tests/
  web/                     → Next.js frontend
    app/
      viewer/[docId]/      → PDF viewer page
      graph/                → knowledge graph page
      chat/                 → chat tutor page
      quiz/                 → quiz/flashcard page
      coach/                → study plan page
    components/
    lib/
    tests/
```

## Code Style

**Backend (Python):** type-hinted, one FastAPI router per feature, Pydantic
models for request/response shapes.

```python
# server/app/routers/explain.py
from fastapi import APIRouter
from app.models.explain import ExplainRequest, ExplainResponse
from app.services.vllm_client import explain_selection

router = APIRouter(prefix="/explain", tags=["explain"])

@router.post("", response_model=ExplainResponse)
async def explain(req: ExplainRequest) -> ExplainResponse:
    return await explain_selection(req.chunk_id, req.selected_text)
```

**Frontend (TypeScript/React):** functional components, named exports,
Tailwind utility classes over custom CSS.

```tsx
// web/components/HighlightPanel.tsx
export function HighlightPanel({ explanation, onSave }: HighlightPanelProps) {
  return (
    <aside className="w-80 border-l border-neutral-200 p-4">
      <p className="text-sm text-neutral-700">{explanation}</p>
      <button onClick={onSave} className="mt-3 rounded bg-neutral-900 px-3 py-1.5 text-white">
        Save highlight
      </button>
    </aside>
  );
}
```

## Testing Strategy

Personal tool, single user — pragmatic bar, not exhaustive coverage:

- **Backend:** `pytest` unit tests for pure logic — PDF/notebook chunking,
  prompt construction, RAG retrieval assembly. Integration tests against a
  local test Neo4j instance (or the dev one) for ingestion write paths and
  vector search.
- **Frontend:** Vitest + React Testing Library for the PDF viewer's
  selection/highlight interaction and the graph page's render-from-data
  path. No e2e suite for the MVP — manual verification of the full click →
  explain → save → graph loop is acceptable at this stage.
- No fixed coverage percentage target; tests exist for logic that can
  silently break (chunking, retrieval, graph writes), not for glue code.

## Boundaries

- **Always:** treat `D:\leb2\<class folders>` as read-only source material
  (ingestion reads, never writes/deletes originals); keep `.env` out of any
  version control; run `scripts/ingest.py` manually, never from a live web
  request; use `manifest.json` as the source of file listings rather than
  re-walking the filesystem.
- **Ask first:** adding dependencies beyond the stack above; changing the
  Neo4j node/relationship schema after the first working version; any move
  toward cloud deployment, multi-class support, or auth.
- **Never:** commit `.env` or the vLLM API key; expose the vLLM API key to
  the browser (all vLLM calls go through the FastAPI backend); modify or
  delete files under the course folders.

## Success Criteria

1. `docker compose up -d neo4j` runs Neo4j 5.x locally, reachable via Bolt.
2. `python scripts/ingest.py --class CPE393` populates Neo4j with
   `Document`/`Chunk`/`Entity` nodes (+ relationships) and a vector index
   over `Chunk.embedding`, covering every file listed under CPE393 in
   `manifest.json`.
3. `web/app/viewer/[docId]` renders a CPE393 PDF with selectable text.
4. Selecting text and requesting an explanation returns an AI explanation
   grounded in the surrounding chunk, shown in a side panel.
5. "Save highlight" persists a `Highlight` node linked to its source
   `Chunk` (and any recognized `Entity` nodes).
6. `/graph` renders the Neo4j graph (force-directed), filterable by topic;
   clicking a node surfaces its source highlight/chunk.
7. `/chat` answers a question using retrieved CPE393 chunks (RAG), not
   unretrieved general knowledge.
8. `/quiz` generates N questions from a chosen topic's chunks and renders
   them with reveal/self-check.
9. Answering a quiz question records an attempt in SQLite with its topic and
   correctness, graded server-side from the stored answer — the client cannot
   assert its own correctness. The home page ranks topics weakest-first.
10. `POST /coach/plan` runs the LangChain coach — a supervisor whose tools are
   a progress agent over the recorded attempts and a material agent over the
   ingested documents — and returns concrete study tasks, each with a topic, a
   source document and page, and why it was chosen. Nothing in a task is
   invented: scores come from the attempt history and pages from the material.
11. `/coach` generates a plan on one explicit action, persists it, re-reads the
   latest plan on load without re-running the agent, and lets tasks be ticked
   off durably.

## Open Questions

1. Neo4j Community edition is assumed sufficient for a single local
   instance with a vector index (available since 5.11+) — confirm no need
   for Enterprise/Aura features.
2. Tailwind CSS assumed for styling — confirm or name a preference.
3. Quiz question format — multiple-choice, short-answer, or both? Assumed
   both, generated per-topic, until narrowed during planning.
4. `react-force-graph-2d` vs `cytoscape.js` for graph rendering — either
   works; pick during implementation unless there's a preference now.

## Resolved Decisions

- **Progress storage — SQLite alongside Neo4j (2026-09-08):** this spec
  originally recorded "Neo4j is the only datastore". That no longer holds.
  Quiz attempts, scores and timestamps are tabular time-series data that the
  study coach queries repeatedly; keeping them out of the course-knowledge
  graph keeps both stores clean and avoids mixing personal history into
  shared course structure. Progress lives at `server/data/progress.db`
  (gitignored). Neo4j remains the single source of truth for everything about
  the *course material* itself. See `docs/intent/study-coach-agents.md`.
- **GPU available (2026-09-08):** the machine has an RTX 5070 Ti (Blackwell,
  sm_120) running CUDA 12.8 torch, so embeddings run on GPU. This invalidates
  the "no local GPU" premise the ColBERT/ColQwen deferral below rests on —
  that decision is now open to revisit on quality grounds rather than closed
  on hardware grounds.
- **Embeddings — dense, then late interaction (2026-09-08):** dense
  `sentence-transformers` shipped first, and still answers any course without
  an index. ColBERT (text) and ColPali/ColQwen2 (page images) are now built on
  top of it, which reverses the 2026-09-07 deferral below: the GPU exists, and
  the multi-vector storage that was going to need PLAID turned out not to. A
  course is a few hundred chunks and a couple of hundred pages, so every vector
  fits in memory and scoring is a direct pass — `server/data/colbert/` and
  `server/data/colpali/`, one compressed float16 file per course, 6 MB and
  27 MB respectively for CPE393.

  ColPali answers with a place rather than a passage. The gateway serves a text
  model, so a page image has nowhere to go; what visual search returns is the
  document and page to open, which is what "find the slide with the chart"
  actually asks for.

- **One course at a time is over (2026-09-08):** the spec's "explicitly out of
  scope: CPE401 / CPE494 support" no longer holds. Every list, the path, and
  the tutor take a course; the class is chosen in the interface and remembered
  in the browser. Retrieval is scoped with it, because a tutor answering a
  text-analytics question out of a cloud-security lecture is worse than no
  answer.
