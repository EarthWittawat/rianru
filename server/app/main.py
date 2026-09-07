from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import documents, explain, highlights
from app.services.neo4j_client import check_connectivity

app = FastAPI(title="Learning Tool API")

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


@app.get("/health")
def health():
    neo4j_ok = check_connectivity()
    return {"neo4j": "ok" if neo4j_ok else "unreachable"}
