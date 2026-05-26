from fastapi import APIRouter, Form
from pydantic import BaseModel
from app.services.memory import get_history, save_history
from app.services.retriever import retrieve_context
from app.services.llm import get_answer
from app.services.booking import extract_booking, check_clash
from app.db.booking_storage import save_booking , get_booking_details
import uuid


router = APIRouter(prefix="/rag",
                    tags=["rag"])

# @router.get("/ping")
# def ping():
#     return {"message": "RAG router is alive"}

class ChatResp(BaseModel):
    session_id:str
    answer: str 
    booking_identifier:bool = False



@router.post("/chat" , response_model=ChatResp) 
async def chat(
    message: str = Form(..., description="Your message or question"),
    session_id: str = Form(default="", description="Leave blank to start a new session")
):
    if not session_id:
        session_id = str(uuid.uuid4())    
    # 1. load history from Redis
    history = get_history(session_id)

    # 2. retrieve relevant chunks from Qdrant
    context_chunks = retrieve_context(message)

    # 3. get answer from LLM
    answer = get_answer(
        query=message,
        context_chunks=context_chunks,
        history=history
    )

    # 4. update history
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": answer})

    # 5. check for booking in full conversation
    conversation_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in history
    )
    booking = extract_booking(conversation_text)
    booking_detected = False

    if booking:
        clash = await check_clash(booking["date"], booking["time"])

        if clash:
            answer = f"Sorry, {booking['date']} at {booking['time']} is already booked. Please choose another slot."
            history.append({"role": "assistant", "content": answer})
        else:
            await save_booking(session_id, booking)
            booking_detected = True

    # 6. save updated history to Redis
    save_history(session_id, history)

    return ChatResp(
        session_id=session_id,
        answer=answer,
        booking_detected=booking_detected
    )

@router.get("/bookings")
async def list_bookings():
    return await get_booking_details()


@router.get("/history/{session_id}")
def get_chat_history(session_id: str):
    return {
        "session_id": session_id,
        "history": get_history(session_id)
    }


@router.delete("/history/{session_id}")
def clear_chat_history(session_id: str):
    from app.services.memory import clear_history
    clear_history(session_id)
    return {"message": f"History cleared for {session_id}"}

# @router.get("/check-mongo")
# async def check_mongo():
#     from app.db.mongodb import metadata_collection
#     count = await metadata_collection.count_documents({})
#     # gets the 3 most recently inserted documents
#     cursor = metadata_collection.find(
#         {}, 
#         {"_id": 0}
#     ).sort("_id", -1).limit(3)  # -1 = descending = newest first
    
#     recent_docs = await cursor.to_list(length=3)
#     return {
#"total_documents": count,"most_recent": recent_docs
#     }