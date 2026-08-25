from collections import defaultdict, deque
from src.geniesupport.config import MAX_HISTORY_TURNS

# session_id -> recent turns. In production this would be Redis, not a dict.
_store = defaultdict(lambda: deque(maxlen=MAX_HISTORY_TURNS))

def add_turn(session_id: str, role: str, content: str):
    _store[session_id].append({"role": role, "content": content})

def format_history(session_id: str) -> str:
    turns = list(_store[session_id])
    if not turns:
        return "(no prior messages)"
    return "\n".join(f"{t['role']}: {t['content']}" for t in turns)