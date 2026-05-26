from groq import Groq
from app.db.booking_storage import get_booking_details, normalize_datetime
import os
import json
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_booking(conversation_text: str) -> dict | None:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": f"""Extract booking details from conversation and return json.
If name, email, date, time ALL exist return ONLY this JSON:
{{"name":"...","email":"...","date":"...","time":"..."}}
Else return exactly : NO_BOOKING

Conversation:
{conversation_text}"""}],
        temperature=0,
        max_tokens=80
    )
    result = response.choices[0].message.content.strip()
    if result == "NO_BOOKING":
        return None
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return None


async def check_clash(date: str, time: str) -> bool:
    # Returns True if slot is already taken.
    # Checks existing bookings for same date + time.

    requested_slot = normalize_datetime(date, time)
    existing = await get_booking_details()
    for booking in existing:
        # compare against the normalized slot stored in DB
        if booking.get("normalized_slot") == requested_slot:
            return True
    return False