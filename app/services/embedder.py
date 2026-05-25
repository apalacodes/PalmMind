# as we are using Qdrant -- will be using the Fastembed library
# Here we create the embeddings for the text chunks and store them in the Qdrant vector database.

from fastembed import TextEmbedding

embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", device="cpu")

def get_embedding(chunks:list[str]) -> list[list[float]]:
    embeddings= list(embedding_model.embed(chunks))
    
    # every item is an array of floats. will convert to list for later storage in Qdrant 
    vector_vals = [embedding.tolist() for embedding in embeddings]
    return vector_vals
