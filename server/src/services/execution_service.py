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
from .event_store import event_store, ExecutionEvent, EventType

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
        
        # Record execution start event
        start_event = ExecutionEvent(
            execution_id=execution_id,
            sequence=0,  # Will be set by event store
            event_type=EventType.EXECUTION_STARTED,
            node_id=None,
            data={"diagram": diagram, "options": options},
            timestamp=asyncio.get_event_loop().time()
        )
        await event_store.append(start_event)

        # 2️⃣ Enrich with API-keys + merge exec-options
        diagram = self._inject_api_keys(diagram)
        exec_opts = self._merge_options(options, execution_id, interactive_handler)

        # 3️⃣ Build executor registry *only* when needed
        from ..executors import create_executors  # lazy import
        from ..executors.config import executor_config
        
        executors = create_executors(
            llm_service=self.llm_service,
            file_service=self.file_service,
            memory_service=self.memory_service,
            notion_service=self.notion_service,
            use_unified=executor_config.is_unified_enabled()
        )

        # 4️⃣ Instantiate compact engine
        from ..execution_engine import CompactEngine

        engine = CompactEngine(executors, logger=log)

        # 5️⃣ Bridge engine→service via asyncio.Queue
        queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

        async def _send(msg: Dict[str, Any]) -> None:
            msg["execution_id"] = execution_id
            
            # Persist event to store
            await self._persist_event(msg, execution_id)
            
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
        except Exception as e:
            # Record execution failure
            fail_event = ExecutionEvent(
                execution_id=execution_id,
                sequence=0,
                event_type=EventType.EXECUTION_FAILED,
                node_id=None,
                data={"error": str(e)},
                timestamp=asyncio.get_event_loop().time()
            )
            await event_store.append(fail_event)
            raise
        finally:
            # Propagate exceptions if the engine errored out
            await engine_task

    # ----------------------------------------------------------------- helpers
    @staticmethod
    async def _validate_diagram(diagram: Dict[str, Any]) -> None:
        """Cheap structural sanity-check before running the engine."""
        if not isinstance(diagram, dict):
            raise ValidationError("Diagram must be a dictionary")
        nodes = diagram.get("nodes") or {}
        if not isinstance(nodes, dict):
            raise ValidationError("Nodes must be a dictionary with node IDs as keys")
        if not nodes:
            raise ValidationError("Diagram must contain at least one node")
        # Record format - iterate over values
        if not any(
            n.get("type") == "start" or n.get("data", {}).get("type") == "start"
            for n in nodes.values()
        ):
            raise ValidationError("Diagram must contain at least one start node")

    async def _warm_up_models(self, diagram: Dict[str, Any]) -> None:
        """Pre-load each unique (service, model, api_key_id) once to cut latency."""
        seen: Set[str] = set()
        persons = diagram.get("persons", {})
        # Only handle dict (Record format)
        if not isinstance(persons, dict):
            raise ValidationError("Persons must be a dictionary with person IDs as keys")
        for p in persons.values():
            # Handle both camelCase and snake_case
            api_key_id = p.get("apiKeyId") or p.get("api_key_id")
            service = p.get("service")
            model = p.get("model")
            
            key = f'{service}:{model}:{api_key_id}'
            if key in seen or not all([service, model, api_key_id]):
                continue
            seen.add(key)
            try:
                self.llm_service.pre_initialize_model(
                    service=service, model=model, api_key_id=api_key_id
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
    
    async def _persist_event(self, msg: Dict[str, Any], execution_id: str) -> None:
        """Convert engine messages to events and persist them."""
        msg_type = msg.get("type", "")
        node_id = msg.get("node_id")
        timestamp = asyncio.get_event_loop().time()
        
        # Map message types to event types
        event_type_map = {
            "execution_started": EventType.EXECUTION_STARTED,
            "execution_complete": EventType.EXECUTION_COMPLETED,
            "node_start": EventType.NODE_STARTED,
            "node_complete": EventType.NODE_COMPLETED,
            "node_skipped": EventType.NODE_SKIPPED,
            "node_paused": EventType.NODE_PAUSED,
            "node_resumed": EventType.NODE_RESUMED,
            "interactive_prompt": EventType.INTERACTIVE_PROMPT,
            "interactive_response": EventType.INTERACTIVE_RESPONSE,
        }
        
        event_type = event_type_map.get(msg_type)
        if not event_type:
            # Skip unknown message types
            return
            
        # Extract relevant data based on message type
        event_data = {}
        if msg_type == "node_complete":
            event_data["output"] = msg.get("output")
            event_data["metadata"] = msg.get("metadata", {})
            # Track token usage if available
            if "token_count" in msg:
                token_event = ExecutionEvent(
                    execution_id=execution_id,
                    sequence=0,
                    event_type=EventType.TOKEN_USAGE,
                    node_id=node_id,
                    data={"tokens": msg["token_count"]},
                    timestamp=timestamp
                )
                await event_store.append(token_event)
        elif msg_type == "node_skipped":
            event_data["reason"] = msg.get("reason")
        elif msg_type == "execution_complete":
            event_data["outputs"] = msg.get("outputs", {})
            event_data["skipped"] = msg.get("skipped", [])
        elif msg_type == "execution_started":
            event_data["execution_order"] = msg.get("execution_order", [])
            
        # Create and persist the event
        event = ExecutionEvent(
            execution_id=execution_id,
            sequence=0,  # Will be set by event store
            event_type=event_type,
            node_id=node_id,
            data=event_data,
            timestamp=timestamp
        )
        
        await event_store.append(event)
