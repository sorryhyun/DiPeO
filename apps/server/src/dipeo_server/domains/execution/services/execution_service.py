from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from typing import Any

from dipeo_core import BaseService, SupportsExecution, get_global_registry
from dipeo_domain import ExecutionStatus
from dipeo_domain.models import DomainDiagram

from dipeo_server.domains.execution.engine import ViewBasedEngine
from dipeo_server.domains.llm.token_usage_service import TokenUsageService
from dipeo_server.infrastructure.persistence import state_store

log = logging.getLogger(__name__)


class ExecutionService(BaseService, SupportsExecution):
    def __init__(
        self,
        llm_service,
        api_key_service,
        conversation_service,
        file_service,
        diagram_service=None,
        notion_service=None,
        execution_preparation_service=None,
        event_bus=None,
    ) -> None:
        super().__init__()
        self.llm_service = llm_service
        self.api_key_service = api_key_service
        self.conversation_service = conversation_service
        self.file_service = file_service
        self.diagram_service = diagram_service
        self.notion_service = notion_service
        self.execution_preparation_service = execution_preparation_service
        self.event_bus = event_bus

    async def initialize(self) -> None:
        pass

    async def execute_diagram(
        self,
        diagram: dict[str, Any] | str,
        options: dict[str, Any],
        execution_id: str,
        interactive_handler: Callable[[dict[str, Any]], Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        log.info(
            f"ExecutionService.execute_diagram called with execution_id: {execution_id}"
        )
        if self.execution_preparation_service:
            # Use the unified preparation service
            ready_diagram = (
                await self.execution_preparation_service.prepare_for_execution(
                    diagram=diagram, validate=True
                )
            )

            diagram_dict = ready_diagram.backend_format
            api_keys = ready_diagram.api_keys
            diagram_obj = ready_diagram.domain_model
        else:
            # Fallback for compatibility
            if isinstance(diagram, dict):
                diagram_obj = DomainDiagram.model_validate(diagram)
                diagram_dict = diagram
            else:
                diagram_obj = diagram
                diagram_dict = diagram_obj.model_dump()

            api_keys = self._inject_api_keys(diagram_dict)["api_keys"]

        # Import node_handlers to ensure handlers are registered
        from .. import node_handlers  # noqa: F401
        
        # Get the global registry which has all registered handlers
        registry = get_global_registry()
        log.info(f"Registry has {len(registry.list_types())} registered handlers: {registry.list_types()}")
        engine = ViewBasedEngine(registry)

        diagram_id = diagram_obj.metadata.id if diagram_obj.metadata else None
        # Create execution in cache only for active executions
        await state_store.create_execution_in_cache(
            execution_id, diagram_id, options.get("variables", {})
        )

        log.info(f"Starting execution {execution_id}")
        yield {
            "type": "execution_start",
            "execution_id": execution_id,
        }

        try:
            updates_queue = asyncio.Queue()

            async def stream_callback(update: dict[str, Any]) -> None:
                await updates_queue.put(update)

                # Also publish to EventBus for WebSocket subscribers
                if self.event_bus:
                    channel = f"execution:{execution_id}"
                    await self.event_bus.publish(channel, update)

            engine_task = asyncio.create_task(
                self._execute_with_new_engine(
                    engine,
                    diagram_obj,
                    api_keys,
                    execution_id,
                    interactive_handler,
                    stream_callback,
                )
            )

            while True:
                try:
                    update = await asyncio.wait_for(updates_queue.get(), timeout=0.1)
                    yield update

                    if update.get("type") == "execution_complete":
                        break

                except asyncio.TimeoutError:
                    if engine_task.done():
                        try:
                            await engine_task
                        except Exception as e:
                            yield {
                                "type": "execution_complete",
                                "execution_id": execution_id,
                                "status": "failed",
                                "error": str(e),
                            }
                        break

        except Exception as e:
            log.error(f"Execution failed for {execution_id}: {e}")
            await state_store.update_status(
                execution_id, ExecutionStatus.FAILED, error=str(e)
            )
            yield {
                "type": "execution_complete",
                "execution_id": execution_id,
                "status": "failed",
                "error": str(e),
            }
            raise

    async def _execute_with_new_engine(
        self,
        engine,
        diagram,
        api_keys,
        execution_id,
        interactive_handler,
        stream_callback,
    ):
        ctx = await engine.execute_diagram(
            diagram=diagram,
            api_keys=api_keys,
            llm_service=self.llm_service,
            file_service=self.file_service,
            conversation_service=self.conversation_service,
            notion_service=self.notion_service,
            api_key_service=self.api_key_service,
            state_store=state_store,
            execution_id=execution_id,
            interactive_handler=interactive_handler,
            stream_callback=stream_callback,
        )

        final_status = "completed"

        # Check for failures
        for output in ctx.node_outputs.values():
            if output.metadata and output.metadata.get("status") == "failed":
                final_status = "failed"
                break

        # Aggregate token usage from all node outputs
        total_token_usage = TokenUsageService.aggregate_node_token_usage(
            ctx.node_outputs
        )

        # Use accumulated token usage from context if available
        if hasattr(ctx, "get_total_token_usage"):
            ctx_token_usage = ctx.get_total_token_usage()
            if ctx_token_usage:
                total_token_usage = ctx_token_usage

        # Get the final state from cache
        final_state = await state_store.get_state_from_cache(execution_id)
        if final_state:
            # Update final state with status and token usage
            if final_status == "completed":
                final_state.status = ExecutionStatus.COMPLETED
            elif final_status == "failed":
                final_state.status = ExecutionStatus.FAILED

            if total_token_usage:
                final_state.token_usage = total_token_usage

            # Persist final state to database
            await state_store.persist_final_state(final_state)

            # Persist conversation history if conversation service has pending data
            if hasattr(self.conversation_service, "persist_execution_conversations"):
                await self.conversation_service.persist_execution_conversations(
                    execution_id
                )
        else:
            # Fallback to old behavior if state not in cache
            if total_token_usage:
                await state_store.update_token_usage(execution_id, total_token_usage)

            if final_status == "completed":
                await state_store.update_status(execution_id, ExecutionStatus.COMPLETED)
            elif final_status == "failed":
                await state_store.update_status(execution_id, ExecutionStatus.FAILED)

        # Build final state snapshot
        from dipeo_domain import NodeExecutionStatus

        node_states = {}
        for node_id, output in ctx.node_outputs.items():
            status = NodeExecutionStatus.COMPLETED
            if output.metadata and output.metadata.get("status") == "failed":
                status = NodeExecutionStatus.FAILED
            node_states[node_id] = {
                "status": status.value,
                "started_at": None,  # Would need to track
                "ended_at": None,  # Would need to track
            }

        final_state_snapshot = {
            "execution_id": execution_id,
            "status": final_status,
            "node_states": node_states,
            "token_usage": total_token_usage.model_dump()
            if total_token_usage
            else None,
        }

        await stream_callback(
            {
                "type": "execution_complete",
                "execution_id": execution_id,
                "status": final_status,
                "state_snapshot": final_state_snapshot,
            }
        )

    def _inject_api_keys(self, diagram: dict[str, Any]) -> dict[str, Any]:
        keys = {
            info["id"]: self.api_key_service.get_api_key(info["id"])["key"]
            for info in self.api_key_service.list_api_keys()
        }
        return {**diagram, "api_keys": keys}
