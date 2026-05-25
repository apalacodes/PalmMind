from fastapi import FastAPI
from app.api.routes import ingestion

app = FastAPI(
    title="Document Ingestor API",
    version="1.0.0",
    description="API for ingesting documents with different chunking approaches.",
)
app.include_router(ingestion.router)

@app.get("/")
def read_root():
    return {"test_message": "check"}
