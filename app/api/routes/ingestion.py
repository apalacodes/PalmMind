from fastapi import APIRouter, HTTPException, UploadFile , File 
from app.services.extractor import extract_text 

router = APIRouter(
    prefix='/ingestion',
    tags=['ingestion'],
)

# taking only pdf and txt files 
valid_extensions = ['.pdf', '.txt']

@router.post("/upload")
async def upload_doc (file:UploadFile = File(...)):

    # check if file extension is valid
    if not any(file.filename.endswith(ext) for ext in valid_extensions):
        raise HTTPException(status_code=400, detail="Invalid file type. Pls upload a txt or pdf file.")
    
    content= await file.read()


    # check if file is empty
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty. Nothing to Ingest!")
    
    # if file exists and is valid then extract text
    try:
        text = extract_text(file.filename, content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # if all coditions meet then display file metadate
    return {"filename": file.filename,
            "extension": file.filename.split('.')[-1],
            "msg": "File is ingesting...",
            "char_count": len(text),
            "preview": text[:100] + "..." if len(text) > 100 else text}


