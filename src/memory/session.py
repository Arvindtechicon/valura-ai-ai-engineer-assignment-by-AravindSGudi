import time
from collections import defaultdict
from typing import Optional
from src.config import settings

class SessionStore:
    def __init__(self):
        self._sessions: dict[str, list[dict]] = defaultdict(list)
        self._last_access: dict[str, float] = {}
    
    def get_history(self, session_id: str) -> list[dict]:
        self._evict_expired()
        self._last_access[session_id] = time.time()
        return self._sessions[session_id].copy()
    
    def add_turn(self, session_id: str, role: str, content: str):
        self._sessions[session_id].append({"role": role, "content": content})
        self._last_access[session_id] = time.time()
        # Keep last 20 turns to manage context window
        if len(self._sessions[session_id]) > 20:
            self._sessions[session_id] = self._sessions[session_id][-20:]
    
    def _evict_expired(self):
        now = time.time()
        expired = [
            sid for sid, t in self._last_access.items()
            if now - t > settings.session_ttl_seconds
        ]
        for sid in expired:
            del self._sessions[sid]
            del self._last_access[sid]
    
    def clear(self, session_id: str):
        self._sessions.pop(session_id, None)
        self._last_access.pop(session_id, None)

session_store = SessionStore()
