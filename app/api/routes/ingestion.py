from fastapi import APIRouter, Form, HTTPException, UploadFile , File 
from app.services.extractor import extract_text 
from app.services.chunker import chunk_text
from app.services.embedder import get_embedding
from app.services.vector_store import store_vectors

router = APIRouter(
    prefix='/ingestion',
    tags=['ingestion'],
)

# taking only pdf and txt files 
valid_extensions = ['.pdf', '.txt']
valid_strategies = ['recursive', 'semantic']

@router.post("/upload")
async def upload_doc (file:UploadFile = File(...), strategy:str=Form(default="recursive")):
   
    # check if file extension is valid
    if not any(file.filename.endswith(ext) for ext in valid_extensions):
        raise HTTPException(status_code=400, detail="Invalid file type. Pls upload a txt or pdf file.")
    content= await file.read()

    # check if file is empty
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty. Nothing to Ingest!")
    
    # check if strategy is valid 
    if strategy not in valid_strategies:
        raise HTTPException(status_code=400, detail="Invalid chunking strategy. choose either 'recursive' or 'semantic'.")


    # EXTRACT TEXT 
    # if file exists and is valid then extract text
    try:
        text = extract_text(file.filename, content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # CHUNK TEXT 
    try:
        chunks = chunk_text(text, strategy)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # EMBED TEXT
    try:
        vectors = get_embedding(chunks)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # STORE VECTORS (QDRANT) 
    try:
        vector_count = await store_vectors(chunks, vectors, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # if all conditions meet then display file metadata
    return {"filename": file.filename,
            "extension": file.filename.split('.')[-1],
            "strategy": strategy,
            "msg": "File is ingesting...",
            "char_count": len(text),
            "chunk_count": len(chunks),
            "vector_count": vector_count,
            "chunks_preview": [chunk[:100] + "..." if len(chunk) > 100 else chunk for chunk in chunks[:5]],
            "preview": text[:100] + "..." if len(text) > 100 else text}


#     return {
#     "chunk_count": len(chunks),
#     "vector_count": len(vectors),
#     "first_vector_length": len(vectors[0]),  # should be 384
#     "first_vector_preview": vectors[0][:5]
# }




















