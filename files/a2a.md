Below “A2A” means “Agent-to-Agent” (or Diagram-to-Diagram) communication: allowing one running diagram to call—or be embedded inside—another
diagram as if it were a first-class node.

────────────────────────────────────────

    1. Conceptual model
       ────────────────────────────────────────
       • A diagram can be compiled into an **Agent Service** that exposes:
         – one or more **input ports** (typed JSON schemas)
         – one **result port** (or multiple named outputs).
       • A caller diagram uses a new node type `sub_diagram` (or `agent_call`) whose only job is “invoke agent X with payload Y, wait for
result”.
       • Communication can be **local** (same worker) or **remote** (another process / host).

────────────────────────────────────────
2. Contract definition  ➜ “Interface Diagram”
────────────────────────────────────────

    1. Small YAML adjacent to the diagram file:

    # marketing_leads.interface.yaml
    id: marketing_leads_v1
    inputs:
      customer_name: str
      rough_requirements: str
    outputs:
      proposal_markdown: str
      estimated_price: float
    timeout: 600s

    1. Generated automatically from “start” node handles if user doesn’t hand-write it.
    2. Stored in a registry (DB table or `files/registry/*.yaml`) so autocomplete can show available agents.

────────────────────────────────────────
3. Execution paths
────────────────────────────────────────
A. In-Process
 • If callee diagram lives in same Python process and has no conflicting resource limits → load sub-graph into CompactEngine recursively and run
 like a function.
 • Propagate execution_id as parent_execution_id:child_n for observability.

B. Cross-Process (same machine)
 • Use asyncio/anyio with nng or Unix sockets.
 • Simple request/stream-response protocol (JSON-lines framed with length prefix).
 • Good for isolating heavy GPU/LLM load or different Python deps.

C. Remote micro-service
 • Expose Agent Service as FastAPI endpoint /agents/<id>/invoke or as gRPC Invoke(AgentRequest) returns (stream AgentEvent).
 • Client node picks gRPC first for streaming, falls back to HTTP/WS.

────────────────────────────────────────
4. Message envelope (streaming friendly)
────────────────────────────────────────

    {
      "cid": "123e...",            // correlation id
      "seq": 7,                    // monotonic seq
      "type": "stdout" | "token" | "log" | "end" | "error",
      "payload": { /* type-specific */ },
      "ts": "2025-06-13T08:21:09Z"
    }

• Same envelope is used inside existing WebSocket -> re-use client code.

────────────────────────────────────────
5. Orchestrator additions
────────────────────────────────────────
• Add SubEngineRunner implementing BaseExecutor; it decides which of the three execution paths to take based on agent.deploy_mode.

    class SubEngineExecutor(BaseExecutor):
        async def execute(self, node, ctx):
            agent_ref = node["data"]["agent_id"]
            mode      = registry.resolve(agent_ref).deploy_mode
            if mode == "inprocess":
                return await self._run_inproc(agent_ref, node["data"]["input"], ctx)
            if mode == "local_rpc":
                return await self._rpc_local(agent_ref, ...)
            return await self._rpc_remote(agent_ref, ...)

• Failure bubbles up like any other node; retries handled either by caller or underlying transport (Temporal etc. if adopted).

────────────────────────────────────────
6. UI / DX
────────────────────────────────────────

    1. **Palette panel “Agent Registry”**
       – drag “marketing_leads_v1” onto canvas, it becomes a `sub_diagram` node.
       – input/output handles autogenerate based on `interface.yaml`.
    2. **Connector syntax**
       – When selecting a remote diagram, arrow labels show `<diagram>::<handle>` so the user can visually see crossing boundaries.
    3. **Versioning**
       – Registry keeps `id` + `version` (semver).
       – On engine start, it validates that a requested version exists; if not → build-time failure rather than runtime.

────────────────────────────────────────
7. Security / Auth
────────────────────────────────────────
• Enforce JWT-based auth on remote calls; token contains caller_agent_id and scopes.
• Callee can inspect token and short-circuit if over quota or not allowed.
• Rate limit per-caller at reverse proxy (e.g., Envoy + Redis token-bucket).

────────────────────────────────────────
8. Implementation Roadmap (overlay on existing plans)
────────────────────────────────────────
Phase 1 (interface & registry)

    1. Pydantic `AgentInterface` model + table `agent_registry`.
    2. CLI command `dipeo agent publish diagram.json --as marketing_leads_v1`.

Phase 2 (in-process executor)
  3. SubEngineExecutor that loads diagram JSON from registry and runs nested CompactEngine.
  4. Add circular-dependency detection.

Phase 3 (local RPC)
  5. Spin each published agent with hypercorn apps.server.agent:app --port <dynamic>.
  6. Registry tracks pid, port, health. Use anyio.create_task_group() to auto-spawn / kill.

Phase 4 (remote SaaS)
  7. HTTPS/gRPC façade + token auth.
  8. Terraform module for autoscaling agent pods under Kubernetes.

Phase 5 (tooling)
  9. VS-Code extension: right-click diagram → “Publish as Agent”.
 10. Web UI: dependency graph view across diagrams/agents.

────────────────────────────────────────
Benefit snapshot
────────────────────────────────────────
• Diagrams become re-usable micro-services.
• Teams can mix-and-match “agents” without importing raw flow logic.
• Streaming envelope keeps UX consistent; monitoring/metrics “just work”.
• Gradual path: in-proc ↔ local RPC ↔ remote SaaS depending on scale.

This design slots naturally on top of the existing CompactEngine and the phased refactor already in progress, giving DiPeO an extensible A2A
foundation without a full re-write.