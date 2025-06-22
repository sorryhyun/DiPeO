from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from typing import Any, Optional

from dipeo_domain import ExecutionStatus
from dipeo_domain.models import DomainDiagram

from dipeo_server.core import BaseService
from ..services.state_store import state_store
from ..engine import SimplifiedEngine
from ..handlers import get_handlers

log = logging.getLogger(__name__)


class ExecutionService(BaseService):

    def __init__(
        self,
        llm_service,
        api_key_service,
        memory_service,
        file_service,
        diagram_service=None,
        notion_service=None,
        diagram_execution_adapter=None,
    ) -> None:
        super().__init__()
        self.llm_service = llm_service
        self.api_key_service = api_key_service
        self.memory_service = memory_service
        self.file_service = file_service
        self.diagram_service = diagram_service
        self.notion_service = notion_service
        self.diagram_execution_adapter = diagram_execution_adapter

    async def initialize(self) -> None:
        pass

    async def execute_diagram(
        self,
        diagram: dict[str, Any],
        options: dict[str, Any],
        execution_id: str,
        interactive_handler: Callable[[dict[str, Any]], Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        if self.diagram_execution_adapter:
            if isinstance(diagram, str):
                ready_diagram = await self.diagram_execution_adapter.prepare_diagram_for_execution(
                    diagram_id=diagram
                )
            else:
                ready_diagram = await self.diagram_execution_adapter.prepare_diagram_dict_for_execution(
                    diagram_dict=diagram
                )

            diagram_dict = ready_diagram.storage_format
            api_keys = ready_diagram.api_keys
        else:
            if isinstance(diagram, dict):
                diagram_obj = DomainDiagram.model_validate(diagram)
                diagram_dict = diagram
            else:
                diagram_obj = diagram
                diagram_dict = diagram_obj.model_dump()

            api_keys = self._inject_api_keys(diagram_dict)["api_keys"]

        engine = SimplifiedEngine(get_handlers())

        if not isinstance(diagram, dict):
            diagram_obj = diagram
        else:
            diagram_obj = DomainDiagram.model_validate(diagram_dict)

        await state_store.create_execution(execution_id, diagram_obj.id, options.get("variables", {}))

        yield {
            "type": "execution_start",
            "execution_id": execution_id,
        }

        try:
            updates_queue = asyncio.Queue()

            async def stream_callback(update: dict[str, Any]) -> None:
                await updates_queue.put(update)

            engine_task = asyncio.create_task(
                self._execute_with_new_engine(
                    engine, diagram_obj, api_keys, execution_id,
                    interactive_handler, stream_callback
                )
            )

            while True:
                try:
                    update = await asyncio.wait_for(
                        updates_queue.get(),
                        timeout=0.1
                    )
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
            await state_store.update_status(execution_id, ExecutionStatus.FAILED, error=str(e))
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
            memory_service=self.memory_service,
            notion_service=self.notion_service,
            state_store=state_store,
            execution_id=execution_id,
            interactive_handler=interactive_handler,
            stream_callback=stream_callback,
        )

        final_status = "completed"
        for output in ctx.node_outputs.values():
            if output.status == "failed":
                final_status = "failed"
                break

        await stream_callback({
            "type": "execution_complete",
            "execution_id": execution_id,
            "status": final_status,
        })


    def _inject_api_keys(self, diagram: dict[str, Any]) -> dict[str, Any]:
        keys = {
            info["id"]: self.api_key_service.get_api_key(info["id"])["key"]
            for info in self.api_key_service.list_api_keys()
        }
        return {**diagram, "api_keys": keys}

