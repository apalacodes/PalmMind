from fastapi import FastAPI
from app.api.routes import ingestion
from app.api.routes import ragbot
from app.services.vector_store import create_collection
from app.db.mongodb import client 
from app.services.memory import r 

app = FastAPI(
    title="Document Ingestor & RagChatBot API",
    version="1.0.0",
    description="API for ingesting documents with different chunking approaches and a RAG-based chatbot.",
)

@app.on_event("startup")
async def startup_event():
    create_collection()

    await client.admin.command("ping")
    print("MongoDB(docker version) connected")

    r.ping()                               
    print("Redis(docker version) connected")


app.include_router(ingestion.router)
app.include_router(ragbot.router)

@app.get("/health")
def check():
    return {"status": "healthy"}


