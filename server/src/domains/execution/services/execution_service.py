# services/execution_service.py
"""Service for running a diagram through the CompactEngine and
streaming execution updates to the caller."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from typing import Any, Dict, Optional, Set

from src.shared.utils.base_service import BaseService
from src.shared.utils.diagram_validator import DiagramValidator
from src.shared.exceptions.exceptions import ValidationError
from ..services.simple_state_store import state_store

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
        self.validator = DiagramValidator(api_key_service)

    # ------------------------------------------------ public entry-point
    async def execute_diagram(
        self,
        diagram: Dict[str, Any],
        options: Dict[str, Any],
        execution_id: str,
        interactive_handler: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Validate → warm-up → enrich → run the CompactEngine.
        Yields node / engine updates as they happen.
        """
        # 1️⃣ Validate + warm-up
        await self._validate_diagram(diagram)
        await self._warm_up_models(diagram)
        
        # Create execution state
        await state_store.create_execution(execution_id, diagram, options)

        # 2️⃣ Enrich with API-keys + merge exec-options
        diagram = self._inject_api_keys(diagram)
        exec_opts = self._merge_options(options, execution_id, interactive_handler)

        # 3️⃣ Build executor registry *only* when needed
        from ..executors import create_executors  # lazy import
        
        executors = create_executors(
            llm_service=self.llm_service,
            file_service=self.file_service,
            memory_service=self.memory_service,
            notion_service=self.notion_service
        )

        # 4️⃣ Instantiate compact engine
        from ..engine.engine import CompactEngine

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
            await state_store.update_status(execution_id, "failed", error=str(e))
            raise
        finally:
            # Propagate exceptions if the engine errored out
            await engine_task

    # ----------------------------------------------------------------- helpers
    async def _validate_diagram(self, diagram: Dict[str, Any]) -> None:
        """Validate diagram structure for execution."""
        self.validator.validate_or_raise(diagram, context="execution")

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
        """Update execution state based on engine messages."""
        msg_type = msg.get("type", "")
        node_id = msg.get("node_id")
        
        # Handle different message types
        if msg_type == "execution_complete":
            await state_store.update_status(execution_id, "completed")
        elif msg_type == "node_start":
            await state_store.update_node_status(execution_id, node_id, "started")
        elif msg_type == "node_complete":
            output = msg.get("output")
            await state_store.update_node_status(execution_id, node_id, "completed", output)
            # Track token usage if available
            if "token_count" in msg:
                await state_store.update_token_usage(execution_id, msg["token_count"])
        elif msg_type == "node_skipped":
            await state_store.update_node_status(execution_id, node_id, "skipped")
        elif msg_type == "node_paused":
            await state_store.update_node_status(execution_id, node_id, "paused")
        elif msg_type == "node_resumed":
            await state_store.update_node_status(execution_id, node_id, "resumed")
        elif msg_type == "interactive_prompt":
            prompt = msg.get("prompt", "")
            await state_store.set_interactive_prompt(execution_id, node_id, prompt)
        elif msg_type == "interactive_response":
            await state_store.clear_interactive_prompt(execution_id)
