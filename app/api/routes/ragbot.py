# Route for the Custom Rag Bot implementation
#  it handles both regular Q&A based off of the ingested documents and its context and the interview booking flow based on user intent.                               

from fastapi import APIRouter, Form
from pydantic import BaseModel
from app.services.memory import get_history, save_history ,get_booking_state, save_booking_state
from app.services.retriever import retrieve_context
from app.services.custom_rag import get_answer
from app.services.booking import handle_booking_flow , should_handle_booking
from app.db.booking_storage import get_booking_details
import uuid


router = APIRouter(prefix="/rag",
                    tags=["rag"])


class ChatResp(BaseModel):
    session_id:str
    answer: str 
    booking_identifier:bool = False

# before processing , simply checking if message has any keywords signalling interview booking intent of user : 
# if yes -> route to booking flow handler 
# if no -> proceed with normal rag flow of retrieving relevant chunks and generating answer from llm 
# this is done to optimize token usage by only sending booking related messages to llm for processing 


@router.post("/chat" , response_model=ChatResp) 
async def chat(
    message: str = Form(..., description="Your message or question"),
    session_id: str = Form(default="")):
    # NOTE::: Every time you want to have multi-turn queries : you must copy and paste the session_id from response 
    
    # create new session or resume previous
    if not session_id or session_id.strip().lower() in ("", "null", "undefined"):
        session_id = str(uuid.uuid4())

    # start from history load from Redis
    history = get_history(session_id)
    booking_state = get_booking_state(session_id) 

    if should_handle_booking(message, booking_state):
        answer, booking_identifier, history, booking_state = await handle_booking_flow(
            session_id=session_id,
            message=message,
            answer="",
            history=history,
            booking_state=booking_state,
        )
        save_booking_state(session_id, booking_state)
    else:
        context_chunks = retrieve_context(message)
        answer = get_answer(query=message, context_chunks=context_chunks, history=history)
        booking_identifier = False
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": answer})
 
    save_history(session_id, history)
 
    return ChatResp(session_id=session_id, answer=answer, booking_identifier=booking_identifier) 

@router.get("/bookings")
async def list_bookings():
    return await get_booking_details()


@router.get("/history/{session_id}")
def get_chat_history(session_id: str):
    return {"session_id": session_id, "history": get_history(session_id)}


@router.delete("/history/{session_id}")
def clear_chat_history(session_id: str):
    from app.services.memory import clear_history
    clear_history(session_id)
    return {"message": f"History cleared for {session_id}"}


