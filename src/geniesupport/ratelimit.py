"""Cap requests per session per minute to prevent abuse / runaway cost."""
import time
from collections import defaultdict, deque

_hits = defaultdict(deque)
LIMIT = 10          # max requests
WINDOW = 60         # seconds

def allow(session_id: str) -> bool:
    now = time.time()
    dq = _hits[session_id]
    while dq and now - dq[0] > WINDOW:   # drop timestamps older than the window
        dq.popleft()
    if len(dq) >= LIMIT:
        return False
    dq.append(now)
    return True