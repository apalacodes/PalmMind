from fastapi import FastAPI
from app.api.routes import ingestion
from app.services.vector_store import create_collection

app = FastAPI(
    title="Document Ingestor API",
    version="1.0.0",
    description="API for ingesting documents with different chunking approaches.",
)

@app.on_event("startup")
def startup_event():
    create_collection()


app.include_router(ingestion.router)

@app.get("/health")
def check():
    return {"status": "healthy"}
