"""In-memory cache for active executions."""

import asyncio
from datetime import datetime, timedelta

from dipeo.models import ExecutionState
from dipeo.models import TokenUsage


class ExecutionCache:
    # In-memory cache for active executions

    def __init__(self, ttl_minutes: int = 60):
        self._cache: dict[str, ExecutionState] = {}
        self._last_access: dict[str, datetime] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._lock = asyncio.Lock()

    async def get(self, execution_id: str) -> ExecutionState | None:
        async with self._lock:
            if execution_id in self._cache:
                self._last_access[execution_id] = datetime.now()
                return self._cache[execution_id]
        return None

    async def set(self, execution_id: str, state: ExecutionState):
        async with self._lock:
            self._cache[execution_id] = state
            self._last_access[execution_id] = datetime.now()

    async def update_token_usage(self, execution_id: str, tokens: TokenUsage):
        async with self._lock:
            if execution_id in self._cache:
                self._cache[execution_id].token_usage = tokens

    async def remove(self, execution_id: str):
        async with self._lock:
            self._cache.pop(execution_id, None)
            self._last_access.pop(execution_id, None)

    async def cleanup_expired(self):
        async with self._lock:
            now = datetime.now()
            expired = [
                eid for eid, last in self._last_access.items() if now - last > self._ttl
            ]
            for eid in expired:
                self._cache.pop(eid, None)
                self._last_access.pop(eid, None)

    async def has(self, execution_id: str) -> bool:
        async with self._lock:
            return execution_id in self._cache

    async def get_all_active(self) -> dict[str, ExecutionState]:
        async with self._lock:
            return dict(self._cache)
