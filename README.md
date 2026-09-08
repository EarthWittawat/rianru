<a id="readme-top"></a>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![CI][ci-shield]][ci-url]

<div align="center">
  <h3 align="center">rianru</h3>
  <p align="center">
    เรียนรู้ — "to learn." A local study tool that turns a semester of course PDFs and notebooks into an active study loop.
    <br />
    <a href="https://github.com/EarthWittawat/rianru/tree/main/docs"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/EarthWittawat/rianru/issues/new?labels=bug">Report Bug</a>
    &middot;
    <a href="https://github.com/EarthWittawat/rianru/issues/new?labels=enhancement">Request Feature</a>
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

## About The Project

Course material arrives as a folder of PDFs and notebooks, and that is where it
stays. rianru ingests that folder into a knowledge graph and a vector index, so
the same material can be read, questioned, practised against, and used to decide
what to revise next.

Everything runs on the machine it is installed on. The material never leaves it,
and the only outside call is to an LLM endpoint the user controls.

What it does:

- **Read.** Lecture PDFs render with a real text layer. Select any passage and
  get an explanation grounded in the surrounding chunk of the actual slide, not
  in the model's general knowledge. Notebooks render markdown and code cells with
  syntax highlighting.
- **Highlight.** Save an explanation as a node linked to the chunk it came from
  and to any concepts it mentions. Highlights survive re-ingesting their document.
- **Map.** A force-directed knowledge graph of documents, extracted concepts and
  your own highlights, filterable by topic.
- **Ask.** A tutor that answers from retrieved chunks and cites the document and
  page it used.
- **Practise.** Multiple-choice and short-answer questions generated from a
  topic's own chunks, graded server-side so the browser cannot assert its own
  correctness.
- **Be coached.** A LangChain multi-agent coach reads the recorded attempt
  history and the material, then issues concrete tasks: what to study, which
  document and page covers it, and why it was chosen.

Two stores, deliberately. Neo4j is the single source of truth for the course
material — documents, chunks, concepts, highlights, generated questions, and the
vector index used for retrieval. Personal progress is tabular time-series data
and lives in a local SQLite file, so study history never mixes into the course
graph.

The coach is a supervisor agent whose two tools are themselves agents: a progress
agent over the SQLite history and a material agent over the course text. That
structure is a deliberate requirement, recorded in
[`docs/intent/study-coach-agents.md`](docs/intent/study-coach-agents.md).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

[![Next][Next.js]][Next-url]
[![React][React.js]][React-url]
[![TypeScript][TypeScript]][TypeScript-url]
[![Tailwind][Tailwind]][Tailwind-url]
[![Python][Python]][Python-url]
[![FastAPI][FastAPI]][FastAPI-url]
[![Neo4j][Neo4j]][Neo4j-url]
[![LangChain][LangChain]][LangChain-url]
[![Docker][Docker]][Docker-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

### Prerequisites

- Docker, for Neo4j 5.15
- Python 3.11 or newer
- Node.js 20 or newer
- An OpenAI-compatible chat completions endpoint (a vLLM gateway, or anything
  speaking the same API)

A GPU is optional. Embeddings run on CPU by default; with an NVIDIA card, install
a matching CUDA build of torch and `sentence-transformers` picks it up on its own
— see the note in [`server/requirements.txt`](server/requirements.txt).

### Installation

1. Clone the repository.

   ```sh
   git clone https://github.com/EarthWittawat/rianru.git
   cd rianru
   ```

2. Create `.env` at the repository root from the template and fill it in.

   ```sh
   cp .env.example .env
   ```

   | Variable | What it is |
   |---|---|
   | `VLLM_URL` | Base URL of the chat completions API, e.g. `https://host/v1` |
   | `VLLM_MODEL` | Model name the gateway serves |
   | `VLLM_API_KEY` | Key for that gateway |
   | `NEO4J_URI` | `bolt://localhost:7687` |
   | `NEO4J_USER` | `neo4j` |
   | `NEO4J_PASSWORD` | Password for the local database — required, no default |

3. Start Neo4j. Ports bind to `127.0.0.1` only; the browser UI is at
   <http://localhost:7474>.

   ```sh
   docker compose up -d neo4j
   ```

4. Install and run the backend.

   ```sh
   cd server
   python -m venv .venv
   .venv/Scripts/activate          # Windows; source .venv/bin/activate elsewhere
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

   `GET /health` returns `{"neo4j": "ok"}` once the database is reachable.

5. Install and run the frontend. It serves on <http://localhost:3000>, or the
   next free port; the backend accepts any localhost origin.

   ```sh
   cd web
   npm install
   npm run dev
   ```

6. Describe your course material in `manifest.json` at the repository root. That
   file is not committed — it lists your own enrolled classes and assignments —
   so you write your own.

   ```json
   {
     "root": "/absolute/path/to/repo",
     "classes": {
       "class-1": {
         "code": "ABC123",
         "name": "Example Course Name",
         "folder": "ABC123 - Example Course",
         "assessment_activities": {
           "lab-1": {
             "title": "Lab 1: Example Lab",
             "type": "activity",
             "folder": "Assessment Activity/Lab 1",
             "files": ["lab1.ipynb", "description.md"]
           }
         },
         "learning_activities": {
           "lecture-1": {
             "title": "Example Lecture Topic",
             "type": "material",
             "folder": "Learning Activity/L1",
             "files": ["L1 - Slides.pdf"]
           }
         }
       }
     }
   }
   ```

   The keys under `classes`, `assessment_activities` and `learning_activities`
   are arbitrary; any unique string works. Each activity's `title` becomes the
   topic used for quizzes, graph filtering and coaching. Files are read from
   `<class folder>/<activity folder>/<file>`. `.pdf`, `.ipynb` and `.md` are
   ingested; anything else listed in `files` is skipped.

7. Ingest. This parses and chunks every listed file, embeds each chunk, writes
   the document and chunk nodes plus the vector index, then extracts concepts and
   relations chunk by chunk through the LLM.

   ```sh
   cd server
   python scripts/ingest.py --class ABC123
   ```

   | Flag | Effect |
   |---|---|
   | `--skip-entities` | Chunk and embed only. Much faster; the graph gets documents but no concepts |
   | `--workers N` | Parallel extraction calls, default 3. Raise only if the gateway allows more concurrency |

   Re-running is safe: a document's chunks are replaced, and saved highlights are
   re-attached rather than orphaned. As a scale reference, a 19-file course
   produced 504 chunks and 715 distinct concepts.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

| Page | What it is for |
|---|---|
| `/viewer` | Pick a document, read it, select text to explain, save highlights |
| `/graph` | The knowledge graph, filterable by topic |
| `/chat` | Ask a question, get an answer cited to document and page |
| `/quiz` | Generate questions for a topic; every answer is recorded |
| `/coach` | Generate a study plan from recorded results |

The coach only has something to say once some quiz questions have been answered:
that history is the signal it reasons over. With no attempts recorded it says so
rather than inventing a weakness.

Development commands:

```sh
# Backend, from server/
pytest                          # full suite
pytest -m "not slow"            # skip tests that call the LLM gateway
ruff check .

# Frontend, from web/
npm test
npm run lint
npm run build
```

Tests that read the course files, or that expect an ingested corpus, skip
themselves when neither is present — which is what happens on CI. With the
material present the full suite runs.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Roadmap

- [x] Ingestion pipeline: chunking, embeddings, concept extraction, vector index
- [x] PDF and notebook reader with grounded explanations and saved highlights
- [x] Knowledge graph
- [x] RAG tutor with citations
- [x] Generated quizzes with server-side grading
- [x] Recorded progress and weakest-topic ranking
- [x] Multi-agent study coach
- [x] CI on every push and pull request
- [ ] Bound the coach's agent loop — a cold plan has taken over ten minutes, with
      no step cap or timeout
- [ ] Retrieval over figures, tables and slide layout, which is text-only today
- [ ] Interface redesign, in progress
- [ ] Embedded notebook execution, deferred on purpose
- [ ] More than one course verified end to end

See the [open issues](https://github.com/EarthWittawat/rianru/issues) for the
current list.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contributing

Contributions are welcome.

1. Fork the project
2. Create your branch (`git checkout -b feature/thing`)
3. Commit your changes (`git commit -m 'Add thing'`)
4. Push the branch (`git push origin feature/thing`)
5. Open a pull request

`main` is protected: changes land through a pull request, and the `backend` and
`web` jobs must pass. Run `pytest -m "not slow"`, `ruff check .`, `npm test` and
`npm run lint` before pushing and CI will hold no surprises.

Course material and personal data stay out of the repository. `manifest.json`,
`.env`, the course folders and the progress database are all gitignored; please
keep it that way in any contribution.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License

No license has been chosen yet, so default copyright applies and no reuse rights
are granted. If you want to use any of this, open an issue and ask.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contact

[@EarthWittawat](https://github.com/EarthWittawat)

Project link: [https://github.com/EarthWittawat/rianru](https://github.com/EarthWittawat/rianru)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Acknowledgments

- [Best-README-Template](https://github.com/othneildrew/Best-README-Template)
- [Neo4j vector indexes](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/)
- [sentence-transformers](https://www.sbert.net/)
- [LangChain](https://docs.langchain.com/)
- [react-pdf](https://github.com/wojtekmaj/react-pdf) and [pdf.js](https://mozilla.github.io/pdf.js/)
- [pdfplumber](https://github.com/jsvine/pdfplumber)
- [react-force-graph](https://github.com/vasturiano/react-force-graph)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

[contributors-shield]: https://img.shields.io/github/contributors/EarthWittawat/rianru.svg?style=for-the-badge
[contributors-url]: https://github.com/EarthWittawat/rianru/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/EarthWittawat/rianru.svg?style=for-the-badge
[forks-url]: https://github.com/EarthWittawat/rianru/network/members
[stars-shield]: https://img.shields.io/github/stars/EarthWittawat/rianru.svg?style=for-the-badge
[stars-url]: https://github.com/EarthWittawat/rianru/stargazers
[issues-shield]: https://img.shields.io/github/issues/EarthWittawat/rianru.svg?style=for-the-badge
[issues-url]: https://github.com/EarthWittawat/rianru/issues
[ci-shield]: https://img.shields.io/github/actions/workflow/status/EarthWittawat/rianru/ci.yml?branch=main&style=for-the-badge&label=CI
[ci-url]: https://github.com/EarthWittawat/rianru/actions/workflows/ci.yml
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://react.dev/
[TypeScript]: https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white
[TypeScript-url]: https://www.typescriptlang.org/
[Tailwind]: https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white
[Tailwind-url]: https://tailwindcss.com/
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[FastAPI]: https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white
[FastAPI-url]: https://fastapi.tiangolo.com/
[Neo4j]: https://img.shields.io/badge/Neo4j-4581C3?style=for-the-badge&logo=neo4j&logoColor=white
[Neo4j-url]: https://neo4j.com/
[LangChain]: https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white
[LangChain-url]: https://www.langchain.com/
[Docker]: https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white
[Docker-url]: https://www.docker.com/
