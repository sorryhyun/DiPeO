from __future__ import annotations
import asyncio, logging, time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Set
from .types import Node, Graph, Arrow, Ctx


def build_graph(diagram: Dict[str, Any]) -> Graph:
    ns: Dict[str, Node] = {
        n["id"]: Node(n["id"], n["data"].get("type", n["type"]), n["data"])
        for n in diagram["nodes"]
    }
    inc, out = defaultdict(list), defaultdict(list)
    for a in diagram["arrows"]:
        ar = Arrow(a["source"], a["target"],
                   a.get("sourceHandle",""), a.get("targetHandle",""),
                   a.get("label",""))
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
