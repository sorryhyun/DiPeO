"""Diagram execution functionality for CLI."""

import asyncio
import contextlib
import os
import uuid
from typing import Any

from dipeo.application.bootstrap import Container
from dipeo.application.execution import ExecuteDiagramUseCase
from dipeo.application.registry.keys import DIAGRAM_PORT, MESSAGE_ROUTER, STATE_STORE
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.domain_models import ExecutionID
from dipeo.diagram_generated.enums import Status

from ..diagram_loader import DiagramLoader
from ..display import DisplayManager
from ..interactive_handler import cli_interactive_handler
from ..session_manager import SessionManager

logger = get_module_logger(__name__)


class DiagramExecutor:
    """Handles diagram execution logic."""

    def __init__(self, container: Container):
        self.container = container
        self.registry = container.registry
        self.diagram_loader = DiagramLoader()
        self.display = DisplayManager()
        self.session_manager = SessionManager()

    async def run_diagram(
        self,
        diagram: str,
        debug: bool = False,
        timeout: int = 300,
        format_type: str | None = None,
        input_variables: dict[str, Any] | None = None,
        use_unified: bool = True,
        simple: bool = False,
        interactive: bool = True,
        execution_id: str | None = None,
    ) -> bool:
        """Execute a diagram using direct service calls.

        Args:
            execution_id: Optional custom execution ID (format: exec_[32-char-hex]).
                         If not provided, a new UUID will be generated.
        """
        try:
            state_store = self.registry.resolve(STATE_STORE)
            message_router = self.registry.resolve(MESSAGE_ROUTER)
            integrated_service = self.registry.resolve(DIAGRAM_PORT)

            if integrated_service and hasattr(integrated_service, "initialize"):
                await integrated_service.initialize()

            (
                domain_diagram,
                diagram_data,
                diagram_path,
            ) = await self.diagram_loader.load_and_deserialize(diagram, format_type)

            if not domain_diagram:
                raise ValueError("Failed to load diagram")

            use_case = ExecuteDiagramUseCase(
                service_registry=self.registry,
                state_store=state_store,
                message_router=message_router,
            )

            options = {
                "variables": input_variables or {},
                "debug_mode": debug,
                "max_iterations": 100,
                "timeout_seconds": timeout,
                "diagram_source_path": diagram,
            }

            if execution_id:
                import re

                if not re.match(r"^exec_[0-9a-f]{32}$", execution_id):
                    raise ValueError(
                        f"Invalid execution_id format: {execution_id}. "
                        f"Expected format: exec_[32-char-hex]"
                    )
                exec_id = ExecutionID(execution_id)
            else:
                exec_id = ExecutionID(f"exec_{uuid.uuid4().hex}")

            native_data = None
            if domain_diagram:
                native_data = {
                    "nodes": [node.model_dump() for node in domain_diagram.nodes],
                    "arrows": [arrow.model_dump() for arrow in domain_diagram.arrows],
                    "handles": [handle.model_dump() for handle in domain_diagram.handles],
                    "persons": [person.model_dump() for person in (domain_diagram.persons or [])],
                }

            metrics_observer = None
            result_observer = None
            event_forwarder = None

            from dipeo.application.registry.keys import EVENT_BUS
            from dipeo.domain.events import EventType

            event_bus = self.registry.resolve(EVENT_BUS)

            from dipeo.application.execution.observers import ResultObserver

            result_observer = ResultObserver(state_store=state_store)

            result_events = [
                EventType.EXECUTION_STARTED,
                EventType.EXECUTION_COMPLETED,
                EventType.EXECUTION_ERROR,
            ]
            await event_bus.subscribe(result_events, result_observer)
            await result_observer.start()
            logger.debug("ResultObserver created and subscribed")

            if debug or os.getenv("DIPEO_TIMING_ENABLED") == "true":
                from dipeo.application.execution.observers import MetricsObserver

                metrics_observer = MetricsObserver(event_bus=event_bus, state_store=state_store)

                metrics_events = [
                    EventType.EXECUTION_STARTED,
                    EventType.NODE_STARTED,
                    EventType.NODE_COMPLETED,
                    EventType.NODE_ERROR,
                    EventType.EXECUTION_COMPLETED,
                ]
                await event_bus.subscribe(metrics_events, metrics_observer)

                await metrics_observer.start()

                if await self.session_manager.is_server_available():
                    from cli.event_forwarder import EventForwarder

                    event_forwarder = EventForwarder(execution_id=str(exec_id))

                    forward_events = [
                        EventType.NODE_STARTED,
                        EventType.NODE_COMPLETED,
                        EventType.NODE_ERROR,
                        EventType.EXECUTION_COMPLETED,
                        EventType.EXECUTION_ERROR,
                    ]
                    await event_bus.subscribe(forward_events, event_forwarder)
                    await event_forwarder.start()

            await self.session_manager.register_cli_session(
                execution_id=str(exec_id),
                diagram_name=diagram,
                diagram_format="native",
                diagram_data=native_data or diagram_data,
            )

            success = False

            async def run_execution():
                nonlocal success
                last_update = None
                async for update in use_case.execute_diagram(
                    diagram=domain_diagram,
                    options=options,
                    execution_id=str(exec_id),
                    interactive_handler=cli_interactive_handler if interactive else None,
                ):
                    last_update = update
                    if not simple:
                        print(".", end="", flush=True)

                if last_update and last_update.get("type") == "execution_complete":
                    success = True
                    await asyncio.sleep(0.1)

                result = await state_store.get_execution(str(exec_id))

                if not success and result:
                    success = result.status == Status.COMPLETED

                if not simple:
                    await self.display.display_rich_results(result, success)
                else:
                    await self.display.display_simple_results(result, success)

            task = asyncio.create_task(run_execution())
            try:
                await asyncio.wait_for(task, timeout=timeout)
            except TimeoutError:
                logger.error(f"Execution timed out after {timeout} seconds")
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

                try:
                    from dipeo.domain.events import execution_error

                    result = await state_store.get_execution(str(exec_id))
                    logger.debug(
                        f"Timeout handler: result={result is not None}, status={result.status if result else 'None'}"
                    )
                    if result and result.status in [Status.PENDING, Status.RUNNING]:
                        logger.warning(
                            f"Execution {exec_id} in {result.status} state after timeout. "
                            f"Executed nodes: {result.executed_nodes}"
                        )

                        if event_forwarder:
                            await event_forwarder.stop()
                            event_forwarder = None
                            logger.debug("EventForwarder stopped before timeout error event")

                        event = execution_error(
                            execution_id=str(exec_id),
                            error_message=f"Execution timed out after {timeout} seconds",
                        )
                        await message_router.publish(event)
                        await event_bus.publish(event)

                        await asyncio.sleep(0.5)
                except Exception as update_err:
                    logger.error(f"Failed to update execution state after timeout: {update_err}")

                try:
                    await self.container.shutdown()
                    logger.info("Container shutdown complete after timeout")
                except Exception as cleanup_err:
                    logger.error(f"Failed to cleanup container after timeout: {cleanup_err}")

                if not simple:
                    print(f"\n❌ Execution timed out after {timeout} seconds")

                await self.session_manager.unregister_cli_session(str(exec_id))

                return False
            finally:
                if event_forwarder:
                    await event_forwarder.stop()
                    logger.debug("EventForwarder stopped")

                if metrics_observer:
                    await metrics_observer.stop()
                    logger.debug("MetricsObserver stopped")

                if result_observer:
                    await result_observer.stop()
                    logger.debug("ResultObserver stopped")

                await self.session_manager.unregister_cli_session(str(exec_id))

            return success

        except Exception as e:
            logger.error(f"Diagram execution failed: {e}")
            if debug:
                import traceback

                traceback.print_exc()
            return False

    async def ask_diagram(
        self,
        request: str,
        and_run: bool = False,
        debug: bool = False,
        timeout: int = 90,
        run_timeout: int = 300,
    ) -> bool:
        """Generate a diagram from natural language using the dipeodipeo diagram."""
        try:
            print("🤖 Generating diagram using DiPeO AI parallel generator...")
            success = await self.run_diagram(
                "projects/dipeodipeo/parallel_generator",
                format_type="light",
                input_variables={"workflow_description": request},
                debug=debug,
                timeout=timeout,
                simple=True,
            )

            if not success:
                print("❌ Diagram generation failed")
                return False

            print("✅ Diagram generated successfully")

            if and_run:
                print("⚠️  Auto-run not yet implemented for dipeodipeo generator")
                return False

            return True

        except Exception as e:
            logger.error(f"Diagram generation failed: {e}")
            if debug:
                import traceback

                traceback.print_exc()
            return False
