#  Core graph primitives
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Set, Optional


@dataclass(slots=True)
class Node:
    id: str
    type: str
    props: Dict[str, Any]
    in_arrows: List["Arrow"] = field(default_factory=list, repr=False)
    out_arrows: List["Arrow"] = field(default_factory=list, repr=False)

    # One-shot caches to avoid thousands of `dict.get(...)`
    @property
    def max_iter(self) -> int | None: return self.props.get("maxIteration")
    @property
    def is_start (self) -> bool:      return self.type == "start"
    @property
    def is_cond  (self) -> bool:      return self.type == "condition"
    @property
    def is_pj    (self) -> bool:      # PersonJob & friends
        return self.type.lower() in {"personjob","personbatchjob",
                                     "person_job","person_batch_job"}

@dataclass(slots=True)
class Arrow:
    source: str
    target: str
    s_handle: str = ""  # sourceHandle
    t_handle: str = ""  # targetHandle
    label   : str = ""

@dataclass
class Graph:
    nodes: Dict[str, Node]                      # id ↦ Node (fast lookup)
    order: List[str]                            # topo order incl. cycles
    incoming: Dict[str, List[Arrow]]            # id ↦ arrows into node
    outgoing: Dict[str, List[Arrow]]            # id ↦ arrows out of node

@dataclass
class Ctx:
    graph: Graph
    exec_cnt : Dict[str,int] = field(default_factory=lambda:defaultdict(int))
    outputs  : Dict[str,Any] = field(default_factory=dict)
    cond_val : Dict[str,bool]= field(default_factory=dict)
    skipped  : Dict[str,str] = field(default_factory=dict)   # nid → reason
    order    : List[str] = field(default_factory=list)
    
    # Additional properties for compatibility with executors
    persons: Dict[str, Any] = field(default_factory=dict)
    execution_id: Optional[str] = None
    interactive_handler: Optional[Callable] = None

    def skip(self,nid,r): self.skipped[nid]=r