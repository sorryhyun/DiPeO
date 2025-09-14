from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from dipeo.diagram_generated import NodeID
from dipeo.domain.execution.envelope import Envelope


@dataclass(frozen=True)
class EdgeRef:
    source_node_id: NodeID
    source_output: str | None
    target_node_id: NodeID
    target_input: str | None = None

    def __hash__(self):
        return hash(
            (self.source_node_id, self.source_output, self.target_node_id, self.target_input)
        )


@dataclass(frozen=True)
class Token:
    epoch: int
    seq: int
    content: Envelope
    ts_ns: int = field(default_factory=lambda: time.time_ns())
    meta: dict[str, Any] = field(default_factory=dict)
    token_id: str = field(default_factory=lambda: str(uuid4()))

    def with_meta(self, **kwargs) -> Token:
        new_meta = {**self.meta, **kwargs}
        return Token(
            epoch=self.epoch,
            seq=self.seq,
            content=self.content,
            ts_ns=self.ts_ns,
            meta=new_meta,
            token_id=self.token_id,
        )


@dataclass
class JoinPolicy:
    policy_type: str = "all"
    k: int | None = None

    def is_ready(self, available_edges: set[EdgeRef], new_token_edges: set[EdgeRef]) -> bool:
        if self.policy_type == "all":
            return new_token_edges == available_edges
        elif self.policy_type == "any":
            return len(new_token_edges) > 0
        elif self.policy_type == "k_of_n" and self.k is not None:
            return len(new_token_edges) >= self.k
        return False


@dataclass
class ConcurrencyPolicy:
    mode: str = "singleton"
    max_concurrent: int = 1

    def can_arm(self, current_running: int) -> bool:
        if self.mode == "singleton":
            return current_running == 0
        elif self.mode == "per-token":
            return True
        elif self.mode == "bounded":
            return current_running < self.max_concurrent
        return False
