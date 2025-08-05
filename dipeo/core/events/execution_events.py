from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class EventType(Enum):
    EXECUTION_STARTED = "execution_started"
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    EXECUTION_COMPLETED = "execution_completed"
    METRICS_COLLECTED = "metrics_collected"
    OPTIMIZATION_SUGGESTED = "optimization_suggested"


@dataclass
class ExecutionEvent:
    type: EventType
    execution_id: str
    timestamp: float
    data: dict[str, Any]


class EventEmitter(Protocol):
    async def emit(self, event: ExecutionEvent) -> None: ...


class EventConsumer(Protocol):
    async def consume(self, event: ExecutionEvent) -> None: ...