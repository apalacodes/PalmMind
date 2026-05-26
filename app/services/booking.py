# this module will handle the interview booking once detected in the user query/conversation
# it will extract relevant details using LLM, check for slot availability and save the booking if all parameters are valid
from groq import Groq
from app.db.booking_storage import check_slot_exists,normalize_datetime, save_booking
import re
import os
import json

from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

BOOKING_INTENT_KEYWORDS = [ "book", "schedule", "arrange", "set up", "appointment",
    "book a slot", "book an interview", "interview",  "reserve", "slot" , "booking" , "scheduling",                                                               
    "i want to book", "i'd like to book",]

def has_booking_intent(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in BOOKING_INTENT_KEYWORDS)

# Check if session is already in an active booking flow
def is_booking_flow_active(booking_state: dict | None) -> bool:
    if booking_state is None:
        return False
    return not all(booking_state.get(f) for f in ["name", "email", "date", "time"])

def should_handle_booking(message: str, booking_state: dict | None) -> bool:
    return has_booking_intent(message) or is_booking_flow_active(booking_state)

def extract_booking(conversation_text: str) -> dict | None:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system",
    "content":( "Extract booking details from conversation and return json.\n"
    "- Date must be a real calendar date (e.g. '2025-06-10' or 'June 10 2025')- Accept DD/MM/YYYY and normalize to YYYY-MM-DD.Reject Vague words like 'tomorrow', 'next week' \n"
    "- Time must be a real clock time (e.g. '10:00 AM', '14:30', '5 PM' or anything : reformat it properly.Reject vague times like:morning, afternoon, evening\n"
    "- Email must look like a real email address.\n"
    "- Set a field to null ONLY if it is genuinely absent from the conversation.\n"
    'Return ONLY JSON in this exact format: {"name":null,"email":null,"date":null,"time":null} . Replace null with values when found.\n')
                },
            {"role": "user","content": conversation_text}  
            ],

        temperature=0,
        max_tokens=120
    )
    result = response.choices[0].message.content.strip()
    cleaned = re.sub(r"```json|```", "", result).strip()
    # Pull out the first block in case the model added any surrounding text
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    try:
        booking = json.loads(cleaned)
        extracted = {
            "name": booking.get("name"),
            "email": booking.get("email"),
            "date": booking.get("date"),
            "time": booking.get("time")
        }
        return extracted

    except Exception as e:
        return {
            "name": None,
            "email": None,
            "date": None,
            "time": None
        }
# Booking state update
def update_booking_state(
    existing: dict,
    extracted: dict)-> dict:

    for field in existing:

        if extracted.get(field):
            existing[field] = extracted[field]

    return existing    

async def check_clash(date: str, time: str) -> bool:
    # Returns True if slot is already taken.
    # Checks existing bookings for same date + time.
    slot = normalize_datetime(date, time)
    return await check_slot_exists(slot)


async def handle_booking_flow(session_id: str, message: str, answer: str, history: list, booking_state=None, llm_signalled_ready: bool = False,):
    booking_identified = False
    if booking_state is None:
        booking_state = {
            "name": None,
            "email": None,
            "date": None,
            "time": None
        }
    # SAVE USER MESSAGE TO HISTORY BEFORE PROCESSING FOR BETTER CONTEXT IN LLM
    history.append({
        "role": "user",
        "content": message
    })

     # Token optimization for only reviewing recent history : specifically from user 
    recent_chat = "\n".join(f"{m['role']}: {m['content']}" for m in history[-10:] if m["role"] == "user")
    booking = extract_booking(recent_chat)
    booking_state = update_booking_state( booking_state, booking)

    # checking missing fields out of the mandatory , required fields 
    required = ["name","email","date","time"]
    missing = [field for field in required
        if not booking_state.get(field)
    ]
    if missing:
        field_labels = {
            "name": "full name",
            "email": "email address",
            "date": "date (example: June 23 2026)",
            "time": "time (example: 5:00 PM)"
        }

        # Tell user what we already have so they don't have to repeat everything again
        captured = {k: v for k, v in booking_state.items() if v}
        if not captured:
            # First ask when nothing iscollected yet
            answer = (
                "To book your interview, please share:\n Full name\n Email address\n Preferred date (example: June 23 2026)\n and - Preferred time (example: 5:00 PM)"
            )
        else:
        # Follow-up — show what has been recieved/valid and what's still missing in the system
            
            captured_lines = "\n".join(f" {field_labels.get(k, k)}: {v}" for k, v in captured.items())
            missing_text = "\n".join(f"  - {field_labels[m]}" for m in missing)
            answer = f"Got so far:\n{captured_lines}\n\nStill need:\n{missing_text}"
 
        history.append({"role": "assistant", "content": answer})
        return (answer, booking_identified, history, booking_state)

    # checking for booking slot clashes 
    normalized_slot = normalize_datetime(booking["date"], booking["time"])
    clash = await check_slot_exists(normalized_slot)
 
    if clash:
        answer = (
            f"Sorry, {booking['date']} at {booking['time']} is already booked. Please pick a different slot."
        )
    else:
        await save_booking( session_id, booking)
        booking_identified = True
        answer = ( f"Hey {booking['name']}, your interview is booked for {booking['date']} at {booking['time']}. Check {booking['email']} for updates." )

    history.append({
        "role": "assistant",
        "content": answer
    })

    return (answer, booking_identified, history, booking_state)