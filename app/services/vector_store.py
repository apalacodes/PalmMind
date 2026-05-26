from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
from dotenv import load_dotenv
import os
from app.db.mongodb import metadata_collection 

load_dotenv()  # This loads the variables from .env

# Access them using os.getenv
api_key = os.getenv("QDRANT_API_KEY")
# Connect to local Qdrant
client = QdrantClient(url="https://0089f3c8-0c95-45af-b713-889d2a75db79.eu-west-2-0.aws.cloud.qdrant.io",
                      api_key=api_key)
collection_name = "text_chunks"
vector_size = 384  # BGE-small-en-v1.5 : fastembed size 

# creating a collection if it doesnt exist : a collection is a table in Qdrant that holds vectors 
def create_collection():
    if not client.collection_exists(collection_name=collection_name):
        try:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                # using cosine similarity for text similarity map 
            )
            print(f"Collection '{collection_name}' created.")
        except Exception as e:
            # for catching unexpected race conditions during hot-reloads
            if "already exists" in str(e).lower():
                print(f"Collection '{collection_name}' was created simultaneously by another thread.")
            else:
                raise e
    else:
        print(f"Collection '{collection_name}' already exists.")

async def store_vectors(chunks:list[str], vectors:list[list[float]],filename:str) -> int :
    # storing every chunk with its corresponding vector in Qdrant 

    points = []
    mongo_docs = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        point_id = str(uuid.uuid4())  # generate a unique ID for each point
        
        # MongoDb Doc for metadata : ------
        mongo_doc = {
            "_id": point_id, "filename": filename,
            "chunk_id": i,"text": chunk
        }
        mongo_docs.append(mongo_doc)

        # Qdrant point 
        point_value= PointStruct( id=point_id , vector =vector,
                                 payload={ "filename": filename,
                                          "text": chunk})

        points.append(point_value)

    # Insert metadata into MongoDB
    if mongo_docs:
        result = await metadata_collection.insert_many(mongo_docs)
        print(f"MongoDB inserted IDs: {result.inserted_ids}")

    client.upsert(collection_name=collection_name, points=points)
    # print(f"Stored {len(points)} vectors in collection '{collection_name}'.")
    return len(points)