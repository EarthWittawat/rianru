# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Undergraduate students revising their own university course material. Primary
situation confirmed 2026-09-08: at a desk on a large screen, in long sessions
of an hour or more, with the source document open and readable beside the
interface rather than glanced at.

The product is being taken beyond its author: it started as a personal tool for
one student and one course, and the confirmed direction is a real product other
students use seriously. That raises first-run, empty-state and comprehension
requirements that a single-user tool never had — someone must be able to open it
without the author sitting next to them.

## Product Purpose

Turn a semester of course files — lecture PDFs, Jupyter notebooks, lab and quiz
descriptions — into an active study loop rather than a folder to scroll through.
The student reads the real source, gets any passage explained in the context of
the surrounding material, saves what mattered, sees how concepts connect, asks
questions answered from the documents, practises against generated questions,
and is told what to revise next based on what they actually got wrong.

Success is a student opening it during revision and being told something true
and specific about where they stand, pointed at the exact pages that fix it.

## Positioning

Answers are grounded in the student's own uploaded course material, not in a
general model's knowledge, and every explanation, tutor answer and study task
names the document and page it came from. The coach reasons over a real record
of that student's quiz attempts, so its advice is derived from evidence rather
than from a prompt describing a hypothetical learner.

The material is ingested into a knowledge graph, so concepts, documents and the
student's own saved highlights are connected objects rather than search results.

## Operating Context

- Everything runs locally: Neo4j in Docker, a FastAPI backend, a Next.js
  frontend, and an OpenAI-compatible LLM endpoint the user controls.
- Course files are read-only source material. They are never modified, and they
  are not part of the repository.
- Ingestion is a manual CLI run, not a web request. It takes minutes and is done
  before study, not during it.
- Retrieval is text-only today. Figures, tables and slide layout are not
  searchable.
- The study coach takes a long time to produce a plan — a cold run has exceeded
  ten minutes — because it is an agent whose tools are themselves agents. Any
  interface around it must treat waiting as a designed state, not an edge case.

## Capabilities and Constraints

Shipped and verified:

- Read a lecture PDF or notebook with a real text layer; notebooks render
  markdown and code cells.
- Select a passage and get an explanation grounded in the surrounding chunk.
- Save an explanation as a highlight linked to its source chunk and to any
  concepts it mentions.
- A force-directed knowledge graph of documents, concepts and highlights,
  filterable by topic.
- A tutor answering from retrieved chunks, citing document and page.
- Generated multiple-choice and short-answer questions per topic, graded
  server-side.
- A recorded attempt history and a weakest-topic ranking.
- A multi-agent coach producing concrete study tasks with sources and reasons.

Constraints and undecided facts:

- Single user, no authentication, localhost only. Multi-user and accounts are
  implied by the product direction but are not decided or built.
- One course is ingested and verified at a time; the ingest CLI takes a course
  code but nothing else has been exercised against a second course.
- Embedded notebook execution and JupyterLab were explicitly deferred.
- No deployment target has been chosen.

## Brand Commitments

The product is named **rianru** (เรียนรู้, "to learn"). No logo, wordmark,
palette or typeface has been committed; none exist yet.

## Evidence on Hand

- Real ingested corpus for one course: 19 documents, 504 chunks, 715 distinct
  concepts.
- A real recorded attempt history and real generated study plans, which the
  coach demonstrably reasoned over.
- No testimonials, user research, usage numbers, pricing or third-party proof of
  any kind exists. None may be fabricated in any surface.

## Product Principles

1. **Cite or say nothing.** Every explanation, answer and study task names the
   document and page it came from. An ungrounded claim is a defect.
2. **Evidence over encouragement.** The product tells the student what the
   record shows, including that the sample is too small to conclude anything.
   It does not motivate with invented praise.
3. **The source material is the hero.** The student came to read their own
   documents; the interface exists to get them into and through the material.
4. **Waiting is a designed state.** Ingestion and coaching are slow by nature.
   The interface must be honest and useful during them, never blank or lying.
5. **A new person can start.** Empty states and first-run must explain what to
   do next without the author present.

## Accessibility & Inclusion

No specific standard has been established. The confirmed usage scene — long
desk sessions on a large screen — makes sustained reading comfort, real text
contrast, and keyboard-reachable controls the practical floor.
