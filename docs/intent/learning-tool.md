# Intent: Personal Learning Tool (CPE393 first)

Confirmed via interview-me on 2026-09-07.

## Outcome
Local web app for CPE393 (Text Analytics) — PDF viewer with click-to-explain
and highlight, a chat tutor grounded in the course docs (via existing vLLM
endpoint), auto-generated quiz/flashcard material, and a knowledge graph
(Neo4j) visualized on-page. Highlights saved from the PDF viewer become
linked nodes in the graph.

## User
Just the user, running locally on their own machine.

## Why now
Personal study tool meant to be used across the whole semester — not a
last-minute exam-cram build. No hard deadline driving this.

## Success looks like
1. Open a CPE393 PDF in the viewer.
2. Click a term/sentence → get an AI explanation in a side panel.
3. Save that explanation as a highlight → it appears as a linked node in a
   visual knowledge graph.
4. Ask the chat tutor a question → answer is grounded in the ingested course
   docs (RAG), not generic.
5. Generate quiz/flashcard questions from the material for exam prep.

## Constraints
- Local-only: Neo4j via Docker, local dev server (no Vercel/cloud for now).
- Reuse the existing vLLM endpoint already configured in `D:\leb2\.env`
  (`VLLM_URL`, `VLLM_MODEL`, `VLLM_API_KEY`).
- Build against CPE393 first (richest existing content: labs, PDFs,
  notebooks across 6 topics) before expanding to CPE401 / CPE494.

## Out of scope (for now)
- Vercel/cloud deployment.
- CPE401 and CPE494 support.
- Multi-user support or auth.
- Mobile access.

## Open technical decisions (not user-facing, resolved at build/spec time)
- Embedding model for RAG (vLLM gateway serves the chat model
  `qwen3.8-27b-fp8`; may need a separate embedding source, e.g. local
  sentence-transformers).
- Neo4j 5.x native vector index vs. separate vector store (leaning: use
  Neo4j's vector index to keep one DB for both graph + retrieval).
- Frontend framework choice (not yet decided in interview).

## Next step
Hand off to spec-driven-development to turn this into a written spec.
