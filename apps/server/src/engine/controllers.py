from __future__ import annotations
import asyncio, logging, time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Set
from .types import Node, Graph, Arrow, Ctx


def build_graph(diagram: Dict[str, Any]) -> Graph:
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
        # ------------------------------------------------------------------
        # Arrow source / target may come in two different shapes depending on
        # who created the diagram:
        #   1.  Modern format  →  {
        #         "source": "node_id",
        #         "sourceHandle": "default",
        #         ...
        #       }
        #   2.  Legacy / compact → "source": "node_id:default"  (same for
        #      target).  The backend engine historically expected the *node*
        #      identifier only, with the handle stored separately.  If we get
        #      the compact variant we therefore need to split it so that the
        #      rest of the engine sees consistent data irrespective of the
        #      client that produced the diagram.
        # ------------------------------------------------------------------

        def _split_handle(field: str, handle: str | None) -> tuple[str, str]:
            """Return (node_id, handle_label) taking legacy `node:handle` into
            account.  *handle* has priority because that means the caller
            already provided a clean separation.
            """
            if handle:  # already explicit -> nothing to do
                return field, handle
            if ":" in field:
                node_id, h = field.split(":", 1)
                return node_id, h
            return field, ""

        src_node, s_handle = _split_handle(
            a["source"], a.get("sourceHandle")
        )
        tgt_node, t_handle = _split_handle(
            a["target"], a.get("targetHandle")
        )

        ar = Arrow(
            src_node,
            tgt_node,
            s_handle,
            t_handle,
            a.get("label", ""),
        )
        inc[ar.target].append(ar);  out[ar.source].append(ar)
    for nid, node in ns.items():
        node.in_arrows  = inc[nid]
        node.out_arrows = out[nid]
    # Kahn topo sort; nodes left over form cycles and are appended afterwards
    deg = {nid: len(inc[nid]) for nid in ns}
    Q   = [nid for nid,d in deg.items() if deg[nid]==0]
    topo: List[str] = []
    while Q:
        cur = Q.pop()
        topo.append(cur)
        for ar in out[cur]:
            deg[ar.target]-=1
            if deg[ar.target]==0: Q.append(ar.target)
    # if cycles exist just append remaining nodes -— engine resolves at runtime
    topo.extend([nid for nid,d in deg.items() if d>0 and nid not in topo])
    return Graph(ns, topo, inc, out)

#  Loop & skip managers (single-file, minimal)

class LoopBook:
    """Tracks per-node iterations and first-prompt consumption."""
    def __init__(self, global_max=100):
        self.iter: Dict[str,int] = defaultdict(int)
        self.first_used: Set[str] = set()
        self.global_max = global_max
    def bump(self, nid:str, lim:int|None) -> bool:
        """Increment and return *True* if another round is allowed."""
        self.iter[nid]+=1
        return self.iter[nid] < (lim or self.global_max)

def should_skip(node:Node, ctx:"Ctx", lp:LoopBook) -> bool:
    nid=node.id
    if nid in ctx.skipped:                 return True
    if node.max_iter and ctx.exec_cnt[nid] >= node.max_iter:
        ctx.skip(nid,"max_iterations");    return True
    if node.is_pj and node.props.get("firstOnlyPrompt") \
       and nid in lp.first_used \
       and not node.props.get("defaultPrompt"):
        ctx.skip(nid,"first_only_consumed"); return True
    return False
