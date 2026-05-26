# RAG Backend — Document Ingestion & Conversational AI API
 
A production-style FastAPI backend implementing a full Retrieval-Augmented Generation (RAG) pipeline with two REST APIs — document ingestion and a conversational chatbot with interview booking support.
The Ingestor API lets you upload documents (pdf and txt) and chunks them for conversations about them with the RAG API. The later one also has built-in interview booking support.
 
## The two APIs
 
### 1. Document Ingestion — `POST /ingestion/upload`
 
Takes a `.pdf` or `.txt` file and runs it through the full pipeline:
 
- Text is extracted using PyMuPDF (for PDFs) or decoded directly (for `.txt`)
- Split into chunks using two strategies : Semantic and Recursive . Here the recursive strategy is default.
- Each chunk is embedded locally using FastEmbed — no OpenAI embedding costs
- Vectors are stored in Qdrant Cloud for semantic search
- Chunk metadata (text, filename, position) is stored in MongoDB
### 2. Conversational RAG — `POST /rag/chat`
 
A multi-turn chatbot that answers questions about ingested documents:
 
- Loads conversation history from Redis (so it remembers previous messages)
- Embeds the user's question and searches Qdrant for the most relevant chunks
- Passes those chunks as context to a Groq-hosted LLaMA model
- Detects booking intent and routes to a dedicated booking handler
- Saves updated history back to Redis after every turn
---
## Tech stack
 
| Tech | Tool |
|---|---|
| Framework | FastAPI |
| LLM | Groq — LLaMA 3.1 8B Instant (free) |
| Embeddings | FastEmbed — BAAI/bge-small-en-v1.5 (local, free) |
| Vector search | Qdrant Cloud |
| Database | MongoDB via Docker |
| Session memory | Redis via Docker |
| PDF parsing | PyMuPDF |
| Chunking | LangChain Text Splitters |
| Date normalization | python-dateutil |
 
---
 
## Project structure
 
```
├── main.py                      # Entry point — startup, router registration
├── requirement.txt
├── .env
│
└── app/
    ├── api/routes/
    │   ├── ingestion.py         # POST /ingestion/upload
    │   └── ragbot.py            # POST /rag/chat and supporting endpoints
    │
    ├── db/
    │   ├── mongodb.py           # Async MongoDB client + collection references
    │   └── booking_storage.py   # Save, fetch, and clash-check bookings
    │
    └── services/
        ├── extractor.py         # Pull text out of PDFs and txt files
        ├── chunker.py           # Recursive and semantic chunking
        ├── embedder.py          # Generate vectors with FastEmbed
        ├── vector_store.py      # Qdrant collection setup and upsert
        ├── retriever.py         # Query Qdrant at chat time
        ├── custom_rag.py        # Build the prompt and call the LLM
        ├── booking.py           # Detect intent, extract details, check clashes
        ├── memory.py            # Redis — load/save chat and booking state
        └── test_view.py         # Development utilities
```
 
---
 
## Getting started
 
### You'll need
 
- Python 3.10+
- Docker Desktop
- A free [Qdrant Cloud](https://cloud.qdrant.io) account
- A free [Groq](https://console.groq.com) API key
### Steps
 
```bash
# 1. clone
git clone https://github.com/yourusername/rag-backend.git
cd rag-backend
 
# 2. install
pip install -r requirement.txt
 
# 3. start MongoDB and Redis
docker run -d -p 27017:27017 --name mongodb mongo
docker run -d -p 6379:6379 --name redis redis
 
# 4. configure
cp .env.example .env
# fill in your keys
 
# 5. run
uvicorn main:app --reload
```
 
Open `http://localhost:8000/docs` — you'll see the full Swagger UI.
 
A healthy startup looks like:
```
Collection 'text_chunks' already exists.
✓ MongoDB connected
✓ Redis connected
```
 
---
 
## Environment variables
 
```env
QDRANT_API_KEY=your-qdrant-api-key
MONGODB_URI=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379
GROQ_API_KEY=your-groq-api-key
```
 
> The project was initially built against MongoDB Atlas and later moved to a local Docker instance. To switch back to Atlas, replace `MONGODB_URI` with your Atlas connection string.
 
---
 
## API reference
 
### `POST /ingestion/upload`
 
| Field | Type | Default | Notes |
|---|---|---|---|
| `file` | File | required | `.pdf` or `.txt` only |
| `strategy` | String | `recursive` | `recursive` or `semantic` |
 
```json
{
{
  "filename": "JobDescription.pdf",
  "extension": "pdf",
  "strategy": "recursive",
  "msg": "File is ingesting...",
  "char_count": 3812,
  "chunk_count": 5,
  "vector_count": 5,
  "chunks_preview": [
    "This job is about...",
    "The company is based in ...",
    "Expected YOE : +3 ...",
    "strong focus on mathematical foundations. Coding and Programming in Pyth...",
    "competitive salary..."
  ],
  "preview": "We are Hiring! ..."
}
}
```
 
---
 
### `POST /rag/chat`
 
| Field | Type | Default | Notes |
|---|---|---|---|
| `message` | String | required | Your question or message |
| `session_id` | String | `""` | Leave blank to start new — copy from response to continue |
 
```json
{
  "session_id": "b1f5907c-a1d3-4702-a66b-1771bef31aff",
  "answer": "The role requires 3+ years of backend experience...",
  "booking_identifier": false
}
```
 
> To continue a conversation across multiple turns, copy the `session_id` from the response and paste it into the next request. Leave it blank to start fresh.
 
---
 
### `GET /rag/bookings`
Returns all confirmed interview bookings.
 
### `GET /rag/history/{session_id}`
Returns the full conversation history for a session.
 
### `DELETE /rag/history/{session_id}`
Wipes the history for a session — useful for testing.
 
### `GET /health`
Liveness check.
 
---
 
## Chunking strategies
 
**Recursive** splits on `\n\n` first, then `\n`, then sentences on "." , then words on " " basically working down until chunks fit within the size limit. It's fast, requires no API calls, and works well for most documents.
 
**Semantic** embeds every sentence and measures cosine distance between neighbours. Where the distance jumps (meaning the topic has shifted), it makes a split. Its slower, but produces chunks that each cover one coherent idea which is better for long documents with distinct sections.
 
---
 
## How booking works
 
Booking detection runs before the standard RAG flow. If the user's message or their current booking state signals intent, the message is routed to a dedicated handler rather than going through retrieval and generation.
 
```
User:  "I'd like to book an interview"
Bot:   "To book your interview, please share:\n Full name\n Email address\n Preferred date (example: June 23 2026)\n and - Preferred time (example: 5:00 PM)"
 
User:  "Sarah, sarah@gmail.com, Dec 31st 2025, 2pm"
Bot:   "Hey Sarah, your interview is booked for 2025-12-31 at 14:00. Check sarah@gmail.com for updates."
```
 
Under the hood:
 
1. `should_handle_booking()` checks message keywords and existing booking state
2. `handle_booking_flow()` manages the conversation — asking for missing details, confirming when complete
3. Date and time are normalized via `python-dateutil` so `"Feb 3rd 10am"` and `"2025-02-03 10:00"` are treated as the same slot
4. Before saving, the slot is checked against existing bookings in MongoDB
5. If there's a clash, the user is told and asked to pick another time
6. Confirmed bookings land in the `bookings` collection in MongoDB
Booking state is persisted in Redis alongside chat history, so a booking started in one session can be completed in the next.
 
---
 
## Constraints met
 
- No `RetrievalQAChain` or any LangChain chain abstractions
- No FAISS or Chroma
- No frontend — API only
- Custom RAG implementation in `custom_rag.py`
- Redis for multi-turn memory
- Booking clash detection before every save
 
 