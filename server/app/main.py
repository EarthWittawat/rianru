from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import documents, explain
from app.services.neo4j_client import check_connectivity

app = FastAPI(title="Learning Tool API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(explain.router)


@app.get("/health")
def health():
    neo4j_ok = check_connectivity()
    return {"neo4j": "ok" if neo4j_ok else "unreachable"}
