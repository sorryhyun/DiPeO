"""
Compact execution engine for AgentDiagram.

This module contains:
- Core data types (Node, Arrow, Graph, Ctx)
- Graph building and topology sorting
- Loop management and skip logic
- The main CompactEngine that orchestrates execution
"""
from __future__ import annotations
import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Set, Optional

# Core Types

@dataclass(slots=True)
class Node:
    id: str
    type: str
    props: Dict[str, Any]
    in_arrows: List["Arrow"] = field(default_factory=list, repr=False)
    out_arrows: List["Arrow"] = field(default_factory=list, repr=False)

    # One-shot caches to avoid thousands of `dict.get(...)`
    @property
    def max_iter(self) -> int | None: 
        return self.props.get("maxIteration")
    
    @property
    def is_start(self) -> bool:
        return self.type == "start"
    
    @property
    def is_cond(self) -> bool:
        return self.type == "condition"
    
    @property
    def is_pj(self) -> bool:  # PersonJob & friends
        return self.type in {"person_job", "person_batch_job"}


@dataclass(slots=True)
class Arrow:
    source: str
    target: str
    source_handle: str = ""
    target_handle: str = ""
    label: str = ""


@dataclass
class Graph:
    nodes: Dict[str, Node]            # id ↦ Node (fast lookup)
    order: List[str]                  # topo order incl. cycles
    incoming: Dict[str, List[Arrow]]  # id ↦ arrows into node
    outgoing: Dict[str, List[Arrow]]  # id ↦ arrows out of node


@dataclass
class Ctx:
    graph: Graph
    exec_cnt: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    outputs: Dict[str, Any] = field(default_factory=dict)
    cond_val: Dict[str, bool] = field(default_factory=dict)
    skipped: Dict[str, str] = field(default_factory=dict)  # nid → reason
    order: List[str] = field(default_factory=list)
    
    # Additional properties for compatibility with executors
    persons: Dict[str, Any] = field(default_factory=dict)
    execution_id: Optional[str] = None
    interactive_handler: Optional[Callable] = None

    def skip(self, nid, r):
        self.skipped[nid] = r

# Graph Building and Controllers

def build_graph(diagram: Dict[str, Any]) -> Graph:
    """Build a Graph from a diagram in Record format."""
    # Only handle Record format (dict)
    nodes = diagram.get("nodes", {})
    # Record format - nodes is a dict with IDs as keys
    ns: Dict[str, Node] = {
        node_id: Node(node_id, n["data"].get("type", n.get("type")), n["data"])
        for node_id, n in nodes.items()
    }
    
    inc, out = defaultdict(list), defaultdict(list)
    
    # Only handle Record format (dict) for arrows
    arrows = diagram.get("arrows", {})
    for a in arrows.values():
        # Modern format uses separate source/sourceHandle and target/targetHandle fields
        src_node = a["source"]
        source_handle = a.get("sourceHandle", "")
        tgt_node = a["target"]
        target_handle = a.get("targetHandle", "")

        ar = Arrow(
            src_node,
            tgt_node,
            source_handle,
            target_handle,
            a.get("label", ""),
        )
        inc[ar.target].append(ar)
        out[ar.source].append(ar)
    
    for nid, node in ns.items():
        node.in_arrows = inc[nid]
        node.out_arrows = out[nid]
    
    # Kahn topo sort; nodes left over form cycles and are appended afterwards
    deg = {nid: len(inc[nid]) for nid in ns}
    Q = [nid for nid, d in deg.items() if deg[nid] == 0]
    topo: List[str] = []
    while Q:
        cur = Q.pop()
        topo.append(cur)
        for ar in out[cur]:
            deg[ar.target] -= 1
            if deg[ar.target] == 0: 
                Q.append(ar.target)
    # if cycles exist just append remaining nodes — engine resolves at runtime
    topo.extend([nid for nid, d in deg.items() if d > 0 and nid not in topo])
    return Graph(ns, topo, inc, out)


class LoopBook:
    """Tracks per-node iterations and first-prompt consumption."""
    
    def __init__(self, global_max=100):
        self.iter: Dict[str, int] = defaultdict(int)
        self.first_used: Set[str] = set()
        self.global_max = global_max
    
    def bump(self, nid: str, lim: int | None) -> bool:
        """Increment and return *True* if another round is allowed."""
        self.iter[nid] += 1
        return self.iter[nid] < (lim or self.global_max)


def should_skip(node: Node, ctx: Ctx, lp: LoopBook) -> bool:
    """Determine if a node should be skipped."""
    nid = node.id
    if nid in ctx.skipped:
        return True
    if node.max_iter and ctx.exec_cnt[nid] >= node.max_iter:
        ctx.skip(nid, "max_iterations")
        return True
    if (node.is_pj and 
        node.props.get("firstOnlyPrompt") and 
        nid in lp.first_used and 
        not node.props.get("defaultPrompt")):
        ctx.skip(nid, "first_only_consumed")
        return True
    return False

# Main Engine

class CompactEngine:
    """Compact execution engine for AgentDiagram diagrams."""
    
    def __init__(self, executors: Dict[str, Any], *, logger=None):
        self.execs = executors
        self.log = logger or logging.getLogger(__name__)
        self.lock = asyncio.Lock()

    async def run(
        self, 
        diagram: Dict[str, Any], 
        *,
        send: Callable[[dict], None] | None = None,
        execution_id: str | None = None,
        interactive_handler: Callable | None = None
    ):
        """Execute a diagram, sending progress updates via the send callback."""
        async with self.lock:
            g = build_graph(diagram)
            ctx = Ctx(g)
            ctx.execution_id = execution_id
            ctx.interactive_handler = interactive_handler
            ctx.persons = diagram.get("persons", {})
            loops = LoopBook()
            
            # Make send async-aware
            if send is None:
                async def _send(msg):
                    pass  # No-op for None send
            elif asyncio.iscoroutinefunction(send):
                _send = send
            else:
                # Wrap sync send in async
                async def _send(msg):
                    send(msg)
            
            await _send({"type": "execution_started", "order": g.order})

            pending: Set[str] = set(g.order)
            while pending:
                ready = [nid for nid in list(pending)
                         if self._deps_met(g.nodes[nid], ctx)]
                if not ready:
                    raise RuntimeError(f"Dead-lock, remaining: {pending}")
                
                # Start events
                for nid in ready: 
                    await _send({"type": "node_start", "node_id": nid})

                # Run in parallel
                results = await asyncio.gather(
                    *[self._do(nid, g.nodes[nid], ctx, loops, _send) 
                      for nid in ready]
                )
                pending.difference_update(ready)
                
                # Handle loop re-queues (false condition → run again)
                for nid, r in zip(ready, results):
                    if g.nodes[nid].is_cond and ctx.cond_val.get(nid) is False:
                        # Re-queue the whole strongly-connected loop members
                        pend = self._loop_members(nid, g)
                        pending.update(pend)
            
            await _send({
                "type": "execution_complete",
                "order": ctx.order, 
                "outputs": ctx.outputs, 
                "skipped": ctx.skipped
            })

    def _deps_met(self, node: Node, ctx: Ctx) -> bool:
        """Check if all dependencies are satisfied for a node."""
        if node.is_start: 
            return True
        for ar in node.in_arrows:
            sid = ar.source
            if sid in ctx.skipped and sid not in ctx.outputs: 
                return False
            if sid not in ctx.outputs:
                return False
            if self._branch_mismatch(ar, ctx.cond_val.get(sid)): 
                return False
        return True

    @staticmethod
    def _branch_mismatch(ar: Arrow, cond_val: bool | None) -> bool:
        """Check if arrow label matches condition value."""
        if cond_val is None:
            return False
        if ar.label.lower() in {"true", "yes", "1"}:
            return cond_val is not True
        if ar.label.lower() in {"false", "no", "0"}:
            return cond_val is not False
        return False  # unlabeled ⇒ always OK

    async def _do(
        self, 
        nid: str, 
        node: Node, 
        ctx: Ctx,
        loops: LoopBook, 
        send: Callable[[dict], None]
    ):
        """Execute a single node."""
        if should_skip(node, ctx, loops):
            await send({
                "type": "node_skipped", 
                "node_id": nid, 
                "reason": ctx.skipped[nid]
            })
            return None

        ex = self.execs.get(node.type)
        if not ex: 
            raise RuntimeError(f"No executor for {node.type}")

        # Run the executor (validate inside executor if needed)
        # Convert Node object to dict format expected by executors
        node_dict = {
            "id": node.id,
            "type": node.type,
            "properties": node.props,  # Executors expect "properties", not "props"
            "data": node.props  # Some executors might use "data"
        }
        result = await ex.execute(node_dict, ctx)
        ctx.outputs[nid] = result.output
        ctx.exec_cnt[nid] += 1
        ctx.order.append(nid)

        if node.is_cond:
            ctx.cond_val[nid] = result.metadata.get(
                "conditionResult", bool(result.output)
            )
        
        # Loop accounting
        if node.is_pj and node.props.get("firstOnlyPrompt"):
            loops.first_used.add(nid)
        if node.max_iter:
            if not loops.bump(nid, node.max_iter):
                ctx.skip(nid, "max_iterations")

        await send({
            "type": "node_complete", 
            "node_id": nid,
            "output": result.output, 
            "meta": result.metadata
        })
        return result

    def _loop_members(self, cid: str, g: Graph) -> Set[str]:
        """Get (very) cheap strongly-connected set containing nid."""
        fwd, rev = set(), set()
        
        def walk(start, edges, acc):
            todo = [start]
            while todo:
                cur = todo.pop()
                acc.add(cur)
                todo.extend([e.target for e in edges[cur] 
                            if e.target not in acc])
        
        walk(cid, g.outgoing, fwd)
        walk(cid, g.incoming, rev)
        return fwd & rev