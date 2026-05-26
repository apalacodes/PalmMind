from datetime import datetime, timezone
from app.db.mongodb import bookings_collection
from dateutil import parser as dateparser 



def normalize_datetime(date_str: str, time_str: str) -> str:
    try:
        combined = f"{date_str} {time_str}"
        dt = dateparser.parse(combined)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        # if parsing fails, fall back to raw string
        return f"{date_str} {time_str}".lower().strip()



async def save_booking(session_id: str, booking: dict) -> None:
    normalized = normalize_datetime(booking["date"], booking["time"])
    
    await bookings_collection.insert_one({
        "session_id": session_id,
        "name": booking["name"],
        "email": booking["email"],
        "date": booking["date"],          # keep original for display
        "time": booking["time"],
        "normalized_slot": normalized,    # used for clash detection
        "created_at": datetime.now(timezone.utc)
    })
    print(f"Booking saved: {booking['name']} at {normalized}")



async def get_booking_details() -> list[dict]:
    cursor = bookings_collection.find({}, {"_id": 0})
    return await cursor.to_list(length=100)