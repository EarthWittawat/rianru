# Intent: Multi-Agent Study Coach

Confirmed via interview-me on 2026-09-08. Follows on from
`docs/intent/learning-tool.md`, which is now built and verified.

## Outcome

A study coach that decides what the student should work on next, and points
them at the exact source to read. Built as a LangChain multi-agent system:
one agent per task, each with its own tools, rather than a single prompt.

## User

The student, studying CPE393, with a midterm the week of 2026-09-14.

## Why now

The app can already retrieve, explain and quiz, but nothing records how the
student performed, so it cannot tell them where they are weak. Suggestion is
the missing half.

## Success looks like

Opening the app and being told something like "you missed 3 of 5 on TF-IDF —
read L6 pages 19-27, then try these questions", and that being the right call.

Three capabilities the student named:
1. Suggest what to study next.
2. Find the correct source to read for it.
3. Assign concrete tasks, not vague advice.

## Constraints

- **Progress tracking is a prerequisite.** Quiz answers are not recorded
  anywhere today — there is no signal to coach from. This lands before any
  agent work and is far smaller than the agent layer.
- **LangChain multi-agent is a requirement, not an implementation detail.**
  Confirmed explicitly after being challenged: the student wants an agent per
  task, each doing tool calling. Do not collapse it to a single prompt because
  that would be simpler.
- **Progress lives in a separate local SQLite database**, not in Neo4j.
  Attempts, scores and timestamps are tabular time-series data; keeping them
  out of the course-knowledge graph keeps both clean. This amends the spec's
  "Neo4j is the only datastore" decision — `docs/SPEC-learning-tool.md` must be
  updated rather than quietly contradicted.
- Local-only still, as before.

## Out of scope (for now)

- **Embedded JupyterLab and code execution.** Explicitly deferred by the
  student ("jupyter part can be later"). The related complaint — notebook code
  rendering as flat text — was fixed separately and is already shipped.
- CPE401 and CPE494.
- Multi-user, auth, cloud deployment.

## Open question to resolve at spec time

The midterm is the week of 2026-09-14. Building a multi-agent system competes
for time with actually studying for it. Worth deciding whether the prerequisite
(progress tracking + a simple weakness report) ships alone first, with the
agent layer following after the midterm.

## Notes for the build

- LangChain's API changes quickly; verify the current surface against installed
  package docs before writing code rather than relying on recalled APIs.
- The GPU (RTX 5070 Ti, CUDA 12.8 torch) is now available, so local models are
  a live option for anything the agents need.
