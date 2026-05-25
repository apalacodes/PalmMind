from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastembed import TextEmbedding
import numpy as np

import re

embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

def chunk_text(text:str, Strategy:str) -> list[str]: 
    if Strategy == "recursive" :
        return recursive_chunk(text)
    elif Strategy == "semantic":
        return semantic_chunk(text)
    else:
        raise ValueError("Invalid chunking strategy. choose either 'recursive' or 'semantic'.")


def recursive_chunk(text:str) -> list[str]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=250)
    separators = ["\n\n", "\n","." ," ", ""]
    #  Split from paragraph--> to line --> to sentence --> to word 
    chunks = text_splitter.split_text(text)
    return chunks

def semantic_chunk(text:str ,threshold: float = 0.3) -> list[str]:
    # splitting text into sentences , on cosine distance ,
    # if close to 0 : same topic , if close to 1 : different so creating a subtle threshold of 0.3 for now 
    # for distance>threshold : then split point is detected. 
    # This is a naive implementation and can be further optimized for better performance and accuracy.
    sentences = _split_into_sentences(text)

    if len(sentences) == 0:
        return [text]

    # if only one sentence just returning
    if len(sentences) == 1:
        return sentences

    vectors = list(embedding_model.embed(sentences))

    # calculate distance between neighbours
    distances = []
    for i in range(len(vectors) - 1):
        dist = _cosine_distance(vectors[i], vectors[i + 1])
        distances.append(dist)

    # when distance jumps above threshold we split

    split_points = []
    for i, dist in enumerate(distances):
        if dist > threshold:
            split_points.append(i + 1)

    #grouping sentences into chunks
    chunks = _group_sentences(sentences, split_points)

    return chunks

def _split_into_sentences(text: str) -> list[str]:
    raw_sentences = re.split(r'(?<=[.?!])\s+', text)
    cleaned_sentences = []
    for s in raw_sentences:
        stripped = s.strip()
        if stripped:
            cleaned_sentences.append(stripped)

    return cleaned_sentences

def _cosine_distance(vec1, vec2) -> float:
    v1 = np.array(vec1)
    v2 = np.array(vec2)

    dot_product = np.dot(v1, v2)
    magnitude = np.linalg.norm(v1) * np.linalg.norm(v2)

    if magnitude == 0:
        return 1.0  # treating zero vectors as different

    cosine_similarity = dot_product / magnitude
    return 1 - cosine_similarity

def _group_sentences(sentences: list[str], split_points: list[int]) -> list[str]:
    chunks = []
    start = 0
    for point in split_points:
        chunk = " ".join(sentences[start:point])
        chunks.append(chunk)
        start = point
    # add remaining sentences as last chunk
    if start < len(sentences):
        chunk = " ".join(sentences[start:])
        chunks.append(chunk)
    return chunks