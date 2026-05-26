from datetime import datetime, timezone
from app.db.mongodb import bookings_collection
from dateutil import parser as dateparser 
import logging
 
logger = logging.getLogger(__name__)

def normalize_datetime(date_str: str, time_str: str) -> str:
    try:
        combined = f"{date_str} {time_str}"
        dt = dateparser.parse(combined)
        if dt is None:
            logger.warning(f"[normalize_datetime] Could not parse: {combined!r}")
            return None
        
            # parser couldn't understand the format — store as-is : ask user to rephrase in proper format : send to llm message 
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception as e:
        logger.error(f"[normalize_datetime] Exception parsing {date_str!r} {time_str!r}: {e}")
        return None



async def save_booking(session_id: str, booking: dict) -> None:
    normalized = normalize_datetime(booking["date"], booking["time"])
    if normalized is None:
        logger.error(f"[save_booking] Skipping save — bad date/time: {booking['date']} {booking['time']}")
        return False
    
    await bookings_collection.insert_one({
        "session_id": session_id,
        "name": booking["name"],
        "email": booking["email"],
        "date": booking["date"],          # keep original for display
        "time": booking["time"],
        "normalized_slot": normalized,    # used for clash detection
        "created_at": datetime.now(timezone.utc)
    })
    logger.info(f"[save_booking] Saved: {booking['name']} at {normalized}")
    print(f"Booking saved: {booking['name']} at {normalized}")


async def get_booking_details() -> list[dict]:
    cursor = bookings_collection.find({}, {"_id": 0}).sort("normalized_slot", 1)
    return await cursor.to_list(length=100)

async def check_slot_exists(normalized_slot: str) -> bool:
    if normalized_slot is None:
        return False
    result = await bookings_collection.find_one({"normalized_slot": normalized_slot})
    return result is not None


