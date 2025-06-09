# services/execution_service.py
"""Service for running a diagram through the CompactEngine and
streaming execution updates to the caller (e.g. a WebSocket)."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from typing import Any, Dict, Optional, Set, TYPE_CHECKING

from ..utils.base_service import BaseService
from ..exceptions import ValidationError

if TYPE_CHECKING:  # Only for static checkers, never at runtime
    from ..state.websocket_state import WebSocketState  # noqa: F401

log = logging.getLogger(__name__)


class ExecutionService(BaseService):
    """Run a diagram and stream node-level updates back to the client."""

    # --------------------------------------------------------------------- init
    def __init__(
        self,
        llm_service,
        api_key_service,
        memory_service,
        file_service,
        diagram_service,
        notion_service=None,
    ) -> None:
        super().__init__()
        self.llm_service = llm_service
        self.api_key_service = api_key_service
        self.memory_service = memory_service
        self.file_service = file_service
        self.diagram_service = diagram_service
        self.notion_service = notion_service

    # ------------------------------------------------ public entry-point
    async def execute_diagram(
        self,
        diagram: Dict[str, Any],
        options: Dict[str, Any],
        execution_id: str,
        interactive_handler: Optional[Callable[[Dict[str, Any]], Any]] = None,
        state_manager: "Optional[WebSocketState]" = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Validate → warm-up → enrich → run the CompactEngine.
        Yields node / engine updates as they happen.
        """
        # 1️⃣ Validate + warm-up
        await self._validate_diagram(diagram)
        await self._warm_up_models(diagram)

        # 2️⃣ Enrich with API-keys + merge exec-options
        diagram = self._inject_api_keys(diagram)
        exec_opts = self._merge_options(options, execution_id, interactive_handler)

        # 3️⃣ Build executor registry *only* when needed
        from ..engine.executors import create_executors  # lazy import
        executors = create_executors(
            llm_service=self.llm_service,
            file_service=self.file_service,
            memory_service=self.memory_service,
            notion_service=self.notion_service,
        )

        # 4️⃣ Instantiate compact engine
        from ..engine.engine import CompactEngine

        engine = CompactEngine(executors, logger=log)

        # 5️⃣ Bridge engine→service via asyncio.Queue
        queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

        async def _send(msg: Dict[str, Any]) -> None:
            msg["execution_id"] = execution_id
            await queue.put(msg)

        # Kick-off engine in background
        engine_task = asyncio.create_task(
            engine.run(diagram, send=_send, execution_id=execution_id, 
                      interactive_handler=interactive_handler)
        )

        # 6️⃣ Stream updates until the engine finishes
        try:
            while True:
                update = await queue.get()
                yield update
                if update.get("type") == "execution_complete":
                    break
        finally:
            # Propagate exceptions if the engine errored out
            await engine_task

    # ----------------------------------------------------------------- helpers
    @staticmethod
    async def _validate_diagram(diagram: Dict[str, Any]) -> None:
        """Cheap structural sanity-check before running the engine."""
        if not isinstance(diagram, dict):
            raise ValidationError("Diagram must be a dictionary")
        nodes = diagram.get("nodes") or []
        if not nodes:
            raise ValidationError("Diagram must contain at least one node")
        if not any(
            n.get("type") == "start" or n.get("data", {}).get("type") == "start"
            for n in nodes
        ):
            raise ValidationError("Diagram must contain at least one start node")

    async def _warm_up_models(self, diagram: Dict[str, Any]) -> None:
        """Pre-load each unique (service, model, api_key_id) once to cut latency."""
        seen: Set[str] = set()
        for p in diagram.get("persons", []):
            key = f'{p.get("service")}:{p.get("model")}:{p.get("apiKeyId")}'
            if key in seen or not all(key.split(":")):
                continue
            seen.add(key)
            try:
                self.llm_service.pre_initialize_model(
                    service=p["service"], model=p["model"], api_key_id=p["apiKeyId"]
                )
            except Exception as exc:  # pragma: no-cover
                log.warning("Warm-up failed for %s – %s", key, exc)

    def _inject_api_keys(self, diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Attach full API-key strings into the diagram (look-up is once)."""
        keys = {
            info["id"]: self.api_key_service.get_api_key(info["id"])["key"]
            for info in self.api_key_service.list_api_keys()
        }
        return {**diagram, "api_keys": keys}

    @staticmethod
    def _merge_options(
        opts: Dict[str, Any],
        execution_id: str,
        interactive_handler: Optional[Callable],
    ) -> Dict[str, Any]:
        """Flatten CamelCase → snake_case and inject defaults."""
        merged = {
            "continue_on_error": opts.get("continueOnError", False),
            "allow_partial": opts.get("allowPartial", False),
            "debug_mode": opts.get("debugMode", False),
            "execution_id": execution_id,
            **opts,
        }
        if interactive_handler:
            merged["interactive_handler"] = interactive_handler
        return merged
