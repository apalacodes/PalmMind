import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

client = QdrantClient(
    url="https://0089f3c8-0c95-45af-b713-889d2a75db79.eu-west-2-0.aws.cloud.qdrant.io",
    api_key=os.getenv("QDRANT_API_KEY")
)

# Fetch points with vectors explicitly enabled
response, _ = client.scroll(
    collection_name="text_chunks",
    limit=3,
    with_vectors=True,  # Crucial: Tells Qdrant to return the numerical arrays
    with_payload=True
)

print(f"--- Found {len(response)} points in Qdrant --- \n")
for point in response:
    print(f"Qdrant Point ID: {point.id}")
    print(f" Payload Metadata: {point.payload}")
    
    # We slice [:5] so it doesn't flood your screen with all 384 dimensions
    print(f"Vector Representation (First 5 dimensions): {point.vector[:5]}...")

