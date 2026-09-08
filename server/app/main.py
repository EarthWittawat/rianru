from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    chat,
    coach,
    concepts,
    documents,
    explain,
    graph,
    highlights,
    path,
    progress,
    quiz,
)
from app.services.neo4j_client import check_connectivity
from app.services.progress import init_db
from app.services.study_plan import init_db as init_study_plan_db

app = FastAPI(title="Learning Tool API")
init_db()
init_study_plan_db()

app.add_middleware(
    CORSMiddleware,
    # Next picks the next free port when 3000 is taken, so match any localhost port.
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(explain.router)
app.include_router(highlights.router)
app.include_router(graph.router)
app.include_router(chat.router)
app.include_router(quiz.router)
app.include_router(progress.router)
app.include_router(coach.router)
app.include_router(path.router)
app.include_router(concepts.router)


@app.get("/health")
def health():
    neo4j_ok = check_connectivity()
    return {"neo4j": "ok" if neo4j_ok else "unreachable"}
