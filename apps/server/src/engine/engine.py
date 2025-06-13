from __future__ import annotations
import asyncio, logging, time
from typing import Any, Callable, Dict, Iterable, List, Set
from .types import Node, Graph, Arrow, Ctx
from .controllers import build_graph, LoopBook, should_skip



class CompactEngine:
    def __init__(self, executors:Dict[str,Any], *, logger=None):
        self.execs, self.log = executors, logger or logging.getLogger(__name__)
        self.lock = asyncio.Lock()

    async def run(self, diagram:Dict[str,Any], *,
                  send:Callable[[dict],None]|None=None,
                  execution_id:str|None=None,
                  interactive_handler:Callable|None=None):

        async with self.lock:
            g   = build_graph(diagram)
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
            
            await _send({"type":"execution_started","order":g.order})

            pending: Set[str] = set(g.order)
            while pending:
                ready = [nid for nid in list(pending)
                         if self._deps_met(g.nodes[nid], ctx)]
                if not ready:
                    raise RuntimeError(f"Dead-lock, remaining: {pending}")
                #  start events
                for nid in ready: 
                    await _send({"type":"node_start","node_id":nid})

                #  run in parallel
                results = await asyncio.gather(
                    *[self._do(nid,g.nodes[nid],ctx,loops,_send) for nid in ready]
                )
                pending.difference_update(ready)
                #  handle loop re-queues (false condition → run again)
                for nid,r in zip(ready,results):
                    if g.nodes[nid].is_cond and ctx.cond_val.get(nid) is False:
                        # re-queue the whole strongly-connected loop members
                        pend = self._loop_members(nid,g)
                        pending.update(pend)
            await _send({"type":"execution_complete",
                  "order":ctx.order,"outputs":ctx.outputs,"skipped":ctx.skipped})

    # ------------------------------------------------------------------ helpers
    def _deps_met(self, node:Node, ctx:Ctx)->bool:
        if node.is_start: return True
        for ar in node.in_arrows:
            sid = ar.source
            if sid in ctx.skipped and sid not in ctx.outputs: return False
            if sid not in ctx.outputs:                        return False
            if self._branch_mismatch(ar, ctx.cond_val.get(sid)): return False
        return True

    @staticmethod
    def _branch_mismatch(ar:Arrow, cond_val:bool|None)->bool:
        if cond_val is None:            return False
        if ar.label.lower() in {"true","yes","1"}:  return cond_val is not True
        if ar.label.lower() in {"false","no","0"}:  return cond_val is not False
        return False                         # unlabeled ⇒ always OK

    async def _do(self, nid:str, node:Node, ctx:Ctx,
                  loops:LoopBook, send:Callable[[dict],None]):
        if should_skip(node,ctx,loops):
            await send({"type":"node_skipped","node_id":nid,"reason":ctx.skipped[nid]})
            return None

        ex = self.execs.get(node.type)
        if not ex: raise RuntimeError(f"No executor for {node.type}")

        #  run the executor (validate inside executor if needed)
        # Convert Node object to dict format expected by executors
        node_dict = {
            "id": node.id,
            "type": node.type,
            "properties": node.props,  # Executors expect "properties", not "props"
            "data": node.props  # Some executors might use "data"
        }
        result = await ex.execute(node_dict, ctx)                  # your API
        ctx.outputs[nid] = result.output
        ctx.exec_cnt [nid]+=1
        ctx.order.append(nid)

        if node.is_cond:
            ctx.cond_val[nid]=result.metadata.get("conditionResult",
                                                  bool(result.output))
        # loop accounting
        if node.is_pj and node.props.get("firstOnlyPrompt"):
            loops.first_used.add(nid)
        if node.max_iter:
            if not loops.bump(nid,node.max_iter):
                ctx.skip(nid,"max_iterations")

        await send({"type":"node_complete","node_id":nid,
              "output":result.output,"meta":result.metadata})
        return result

    # get (very) cheap strongly-connected set containing nid
    def _loop_members(self, cid:str, g:Graph)->Set[str]:
        fwd, rev=set(),set()
        def walk(start,edges,acc):
            todo=[start]
            while todo:
                cur=todo.pop()
                acc.add(cur)
                todo.extend([e.target for e in edges[cur] if e.target not in acc])
        walk(cid,g.outgoing,fwd); walk(cid,g.incoming,rev)
        return fwd&rev
