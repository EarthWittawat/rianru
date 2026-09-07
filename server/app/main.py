from fastapi import FastAPI

from app.services.neo4j_client import check_connectivity

app = FastAPI(title="Learning Tool API")


@app.get("/health")
def health():
    neo4j_ok = check_connectivity()
    return {"neo4j": "ok" if neo4j_ok else "unreachable"}
