# Task List: Progress Tracking + Multi-Agent Study Coach

Intent: `docs/intent/study-coach-agents.md` · Spec: `docs/SPEC-learning-tool.md`
Follows `tasks/plan.md` / `tasks/todo.md`, which cover the original MVP and are
complete.

This record was written at the closeout of Milestone 2. Milestones 1 and 2 were
executed task-by-task with a commit each; this file collects what each task
delivered and the evidence it passed on, so the work is tracked in the repo
rather than only in commit messages.

---

## Milestone 1: Progress tracking (the coaching signal)

The intent doc makes this a hard prerequisite: quiz answers were not recorded
anywhere, so there was no signal to coach from.

### M1-T1: SQLite store for quiz progress ✅ (`d03ad0b`)
**Delivered:** `server/app/services/progress.py` — a `quiz_attempt` table
recording question id, topic, format, chosen answer, correctness, and whether
the judgement came from auto-grading or a self-grade. Topic is denormalised
because the coach groups by it constantly and should not need a Neo4j
round-trip. `weak_topics` ignores topics below a minimum attempt count so one
unlucky answer cannot outrank a genuinely failed topic.

**Evidence:** 8 tests in `server/tests/test_progress.py`. Spec amended in the
same commit (Resolved Decisions: SQLite alongside Neo4j) rather than left
contradicting the original single-datastore decision.

### M1-T2: Progress endpoints with server-side grading ✅ (`95b6c26`)
**Delivered:** `POST /progress/attempts` takes a question id plus either the
chosen option or a self-grade, looks the answer up in Neo4j, and decides
correctness itself. `GET /progress/topics` and `GET /progress/weak` expose the
aggregates.

**Evidence:** 7 tests in `server/tests/test_progress_api.py`, including one
asserting the client cannot assert its own `is_correct` — this history is what
the coach reasons over, so a frontend bug must not be able to poison it.

### M1-T3 to T5: Record answers and show where you stand ✅ (`a14baec`)
**Delivered:** picking a multiple-choice option posts an attempt; short answers
get an explicit self-grade after reveal, so both practice formats feed one
history. The home page ranks topics weakest-first with attempt counts.
Save failures surface instead of silently dropping the answer.

**Evidence:** `web/tests/QuizCard.test.tsx` (7 tests). `ProgressSummary`'s unit
test is deliberately omitted with a note in the commit: the component
demonstrably handles a rejected fetch, but Vitest reports the settled rejection
from a mocked effect call as a stray error regardless.

---

## Milestone 2: LangChain multi-agent study coach

The intent doc makes multi-agent a requirement, not an implementation detail:
an agent per task, each doing tool calling, confirmed after being challenged.

### M2-T1: LangChain reaches the gateway and calls tools ✅ (`0e195a7`)
**Delivered:** `server/app/agents/llm.py` — the vLLM gateway as a LangChain
chat model. Pins `langchain` 1.4.0 and `langchain-openai` 1.6.0, and adds a
`slow` pytest marker so gateway-dependent tests can be deselected.

**Risk this retired:** native tool calling had to survive the reasoning model —
vLLM parses tool calls from content only, not from reasoning output, and tool
support depends on server launch flags this gateway does not expose.

**Evidence:** `server/tests/test_agent_llm.py` (1 slow test) asserts the answer
quotes a topic that exists only in the tool output, so a plausible invention
cannot pass.

### M2-T2: Tool layer over the existing services ✅ (`49200a7`)
**Delivered:** `server/app/agents/tools.py` — six tools wrapping code that
already existed: progress stats from SQLite, vector search and document
listings from Neo4j. No new retrieval logic, just a model-facing surface.

**Evidence:** 7 tests in `server/tests/test_agent_tools.py`; each tool is
invocable directly, so the layer is tested with no model or network in the
loop. One test asserts every tool carries a description — a tool the model
cannot understand is a tool it will never call.

### M2-T3 / M2-T4: Specialist agents and the study coach ✅ (`71d587b`)
**Delivered:** `server/app/agents/specialists.py` — a progress agent over the
SQLite history and a material agent over the course text, both exposed to a
supervising coach (`server/app/agents/coach.py`) as tools. Subagents-as-tools
is what LangChain now recommends over the deprecated supervisor package.

The plan is parsed from the model's JSON rather than requested via
`response_format`: structured output is silently skipped when reasoning content
is present unless the server opts in, and this gateway does not. Malformed
output degrades to an empty plan.

**Evidence:** 8 tests in `server/tests/test_coach.py`. Verified live against
real data: it identified the genuinely weakest topic from recorded attempts,
cited real documents and pages, and noted that three attempts is too small a
sample to draw firm conclusions from.

### M2-T5: Persist study plans and serve them ✅ (`435dff4`)
**Delivered:** `server/app/services/study_plan.py` + `routers/coach.py` —
`POST /coach/plan` generates and stores, `GET /coach/plan/latest` re-reads,
`PATCH /coach/tasks/{id}` ticks a task off. An empty plan is a 502 rather than
a saved blank: it means the coach failed, and storing it would hide that behind
an empty screen.

**Evidence:** 6 tests in `server/tests/test_coach_api.py`, including one
asserting that fetching a plan does not re-run the agent, and that a ticked
task survives a restart.

### M2-T6: Coach page ✅ (`aded8ef`)
**Delivered:** `web/app/coach/page.tsx` + `web/components/StudyPlan.tsx`. A
single explicit action generates the plan, with a pending state that survives
the wait. Tasks show the evidence behind them and the page they point at, and
can be ticked off; a tick that fails to save is rolled back rather than left
showing.

**Evidence:** 4 tests in `web/tests/StudyPlan.test.tsx`.

---

## Checkpoint: Progress tracking + coach

- [x] Full suite green: backend 85 passed (2 slow deselected), frontend 21
      passed, run 2026-09-08 at closeout
- [x] `/coach` loads a persisted plan on a cold start, with a previously
      ticked task still ticked — confirmed in a browser
- [x] Generating a fresh plan from the page shows a pending state and then
      replaces the plan with newly generated tasks
- [x] Spec updated with Success Criteria 9-11 covering progress tracking and
      the coach

## Known limitations recorded at closeout

- **Plan generation is far slower than the UI implies.** The page says "up to a
  minute or so"; an observed cold run took over 12 minutes. The coach is a
  supervisor agent whose two tools are themselves agents, so one plan is many
  sequential reasoning-model round trips, plus a first-call embedding model
  load. There is no step cap or request timeout on the agent loop, so a
  degenerate run has no upper bound. Worth a bounded `recursion_limit`, a
  timeout, and an honest wait message.
- Only one topic has recorded attempts, so the coach's own output says the
  sample is too small to target anything else — the coaching quality bar cannot
  really be judged until more quizzes are taken.
