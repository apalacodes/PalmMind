import json
import redis
import os
from dotenv import load_dotenv

load_dotenv()

r = redis.from_url("redis://localhost:6379")
MAX_HISTORY = 10
def get_history(session_id: str) -> list[dict]:
    raw = r.get(f"session:{session_id}")
    if raw is None:
        return []
    return json.loads(raw)


def save_history(session_id: str, history: list[dict]) -> None:
    trimmed = history[-MAX_HISTORY:]
    r.set(
        f"session:{session_id}",
        json.dumps(trimmed),
        ex=3600
    )


def clear_history(session_id: str) -> None:
    r.delete(f"session:{session_id}")