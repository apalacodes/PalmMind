from qdrant_client import QdrantClient
from qdrant_client.models import QueryRequest
from fastembed import TextEmbedding
import os
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(url="https://0089f3c8-0c95-45af-b713-889d2a75db79.eu-west-2-0.aws.cloud.qdrant.io",api_key=os.getenv("QDRANT_API_KEY"))

embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", device="cpu")
collection_name = "text_chunks"
vector_size = 384   

def retrieve_context(query: str, top_k: int = 4) -> list[str]:
    query_vector = list(embedding_model.embed([query]))[0].tolist()

    results = client.query_points(collection_name=collection_name,query=query_vector,limit=top_k,with_payload=True)
    chunks = [hit.payload["text"] for hit in results.points if hit.payload]
    return chunks
