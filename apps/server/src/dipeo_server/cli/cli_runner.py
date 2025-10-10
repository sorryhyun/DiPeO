"""CLI runner that executes commands directly using services."""

import asyncio
import contextlib
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Optional

from dipeo.application.bootstrap import Container
from dipeo.application.execution import ExecuteDiagramUseCase
from dipeo.application.registry.keys import DIAGRAM_PORT, MESSAGE_ROUTER, STATE_STORE
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.domain_models import ExecutionID
from dipeo.diagram_generated.enums import Status
from dipeo_server.cli.diagram_loader import DiagramLoader
from dipeo_server.cli.display import DisplayManager
from dipeo_server.cli.session_manager import SessionManager

logger = get_module_logger(__name__)


class CLIRunner:
    """CLI runner that uses direct service calls instead of HTTP/GraphQL."""

    def __init__(self, container: Container):
        """Initialize CLI runner with dependency container."""
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
    ) -> bool:
        """Execute a diagram using direct service calls."""
        try:
            state_store = self.registry.resolve(STATE_STORE)
            message_router = self.registry.resolve(MESSAGE_ROUTER)
            integrated_service = self.registry.resolve(DIAGRAM_PORT)

            if integrated_service and hasattr(integrated_service, "initialize"):
                await integrated_service.initialize()

            # Load and deserialize diagram
            (
                domain_diagram,
                diagram_data,
                diagram_path,
            ) = await self.diagram_loader.load_and_deserialize(diagram, format_type)

            if not domain_diagram:
                raise ValueError("Failed to load diagram")

            # Create use case
            use_case = ExecuteDiagramUseCase(
                service_registry=self.registry,
                state_store=state_store,
                message_router=message_router,
            )

            # Prepare options
            options = {
                "variables": input_variables or {},
                "debug_mode": debug,
                "max_iterations": 100,
                "timeout_seconds": timeout,
                "diagram_source_path": diagram,
            }

            execution_id = ExecutionID(f"exec_{uuid.uuid4().hex}")

            # Convert domain_diagram to native format for frontend
            native_data = None
            if domain_diagram:
                native_data = {
                    "nodes": [node.model_dump() for node in domain_diagram.nodes],
                    "arrows": [arrow.model_dump() for arrow in domain_diagram.arrows],
                    "handles": [handle.model_dump() for handle in domain_diagram.handles],
                    "persons": [person.model_dump() for person in (domain_diagram.persons or [])],
                }

            # Create and subscribe MetricsObserver if debug or timing enabled
            metrics_observer = None
            event_forwarder = None
            if debug or os.getenv("DIPEO_TIMING_ENABLED") == "true":
                from dipeo.application.execution.observers import MetricsObserver
                from dipeo.application.registry.keys import EVENT_BUS
                from dipeo.domain.events import EventType

                event_bus = self.registry.resolve(EVENT_BUS)
                metrics_observer = MetricsObserver(event_bus=event_bus, state_store=state_store)

                # Subscribe to metrics events
                metrics_events = [
                    EventType.EXECUTION_STARTED,
                    EventType.NODE_STARTED,
                    EventType.NODE_COMPLETED,
                    EventType.NODE_ERROR,
                    EventType.EXECUTION_COMPLETED,
                ]
                await event_bus.subscribe(metrics_events, metrics_observer)

                # Start the metrics observer
                await metrics_observer.start()

                # Create EventForwarder to forward events to background server if available
                if await self.session_manager.is_server_available():
                    from dipeo_server.cli.event_forwarder import EventForwarder

                    event_forwarder = EventForwarder(execution_id=str(execution_id))

                    # Subscribe to node AND execution events
                    forward_events = [
                        EventType.NODE_STARTED,
                        EventType.NODE_COMPLETED,
                        EventType.NODE_ERROR,
                        EventType.EXECUTION_COMPLETED,
                        EventType.EXECUTION_ERROR,
                    ]
                    await event_bus.subscribe(forward_events, event_forwarder)
                    await event_forwarder.start()
                    logger.info(
                        "EventForwarder started - events will be forwarded to background server"
                    )

            # Register CLI session for monitor mode support
            await self.session_manager.register_cli_session(
                execution_id=str(execution_id),
                diagram_name=diagram,
                diagram_format="native",
                diagram_data=native_data or diagram_data,
            )

            # Execute diagram
            success = False

            async def run_execution():
                nonlocal success
                last_update = None
                async for update in use_case.execute_diagram(
                    diagram=domain_diagram,
                    options=options,
                    execution_id=str(execution_id),
                ):
                    last_update = update
                    if not simple:
                        print(".", end="", flush=True)

                if last_update and last_update.get("type") == "execution_complete":
                    success = True
                    await asyncio.sleep(0.1)

                result = await state_store.get_execution(str(execution_id))

                if not success and result:
                    success = result.status == Status.COMPLETED

                if not simple:
                    await self.display.display_rich_results(result, success)
                else:
                    await self.display.display_simple_results(result, success)

            # Run execution
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

                    result = await state_store.get_execution(str(execution_id))
                    if result and result.status == Status.RUNNING:
                        logger.warning(
                            f"Execution {execution_id} still RUNNING after timeout. "
                            f"Executed nodes: {result.executed_nodes}"
                        )
                        event = execution_error(
                            execution_id=str(execution_id),
                            error_message=f"Execution timed out after {timeout} seconds",
                        )
                        await message_router.publish(event)
                except Exception as update_err:
                    logger.error(f"Failed to update execution state after timeout: {update_err}")

                try:
                    await self.container.shutdown()
                    logger.info("Container shutdown complete after timeout")
                except Exception as cleanup_err:
                    logger.error(f"Failed to cleanup container after timeout: {cleanup_err}")

                if not simple:
                    print(f"\n❌ Execution timed out after {timeout} seconds")

                await self.session_manager.unregister_cli_session(str(execution_id))

                return False
            finally:
                # Stop event forwarder if it was created
                if event_forwarder:
                    await event_forwarder.stop()
                    logger.debug("EventForwarder stopped")

                # Stop metrics observer if it was created
                if metrics_observer:
                    await metrics_observer.stop()
                    logger.debug("MetricsObserver stopped")

                await self.session_manager.unregister_cli_session(str(execution_id))

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

    async def convert_diagram(
        self,
        input_path: str,
        output_path: str,
        from_format: str | None = None,
        to_format: str | None = None,
    ) -> bool:
        """Convert between diagram formats."""
        try:
            from dipeo.application.diagram.use_cases.serialize_diagram import (
                SerializeDiagramUseCase,
            )

            input_file = Path(input_path)
            if not input_file.exists():
                print(f"❌ Input file not found: {input_path}")
                return False

            if not from_format:
                from_format = self.diagram_loader.detect_format(input_path)
            if not to_format:
                to_format = self.diagram_loader.detect_format(output_path)

            with open(input_path, encoding="utf-8") as f:
                content = f.read()

            await self.diagram_loader.initialize()
            use_case = SerializeDiagramUseCase(self.diagram_loader.serializer)

            converted_content = use_case.convert_format(content, to_format, from_format)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(converted_content)

            print(f"✅ Converted {input_path} to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Diagram conversion failed: {e}")
            return False

    def _is_main_execution(self, execution_id: str) -> bool:
        """Check if execution ID is a main execution (not lightweight or sub-diagram).

        Filters out:
        - Lightweight executions (starting with "lightweight_")
        - Sub-diagram executions (containing "_sub_")
        """
        exec_id_str = str(execution_id)
        return not (exec_id_str.startswith("lightweight_") or "_sub_" in exec_id_str)

    async def show_metrics(
        self,
        execution_id: str | None = None,
        latest: bool = False,
        diagram_id: str | None = None,
        breakdown: bool = False,
        bottlenecks_only: bool = False,
        optimizations_only: bool = False,
        output_json: bool = False,
    ) -> bool:
        """Display execution metrics from database (no server required)."""
        try:
            state_store = self.registry.resolve(STATE_STORE)

            # Find the target execution
            target_execution_id = None
            if execution_id:
                target_execution_id = execution_id
            elif latest or diagram_id:
                # Fetch more executions to filter out lightweight/sub-diagram ones
                executions = await state_store.list_executions(diagram_id=diagram_id, limit=50)
                # Filter to main executions only
                main_executions = [e for e in executions if self._is_main_execution(e.id)]
                if main_executions:
                    target_execution_id = main_executions[0].id
                else:
                    if diagram_id:
                        print(f"No main executions found for diagram: {diagram_id}")
                    else:
                        print("No main executions found")
                    return False
            else:
                # Fetch more executions to filter out lightweight/sub-diagram ones
                executions = await state_store.list_executions(limit=50)
                # Filter to main executions only
                main_executions = [e for e in executions if self._is_main_execution(e.id)]
                if main_executions:
                    target_execution_id = main_executions[0].id
                else:
                    print("No main executions found")
                    return False

            # Get execution state from database
            execution_state = await state_store.get_execution(str(target_execution_id))
            if not execution_state:
                print(f"❌ Execution {target_execution_id} not found")
                return False

            # Check if metrics are available
            if not execution_state.metrics:
                print(f"❌ No metrics available for execution {target_execution_id}")
                print(
                    "   Metrics are only available for executions run with --timing or --debug flags"
                )
                return False

            # Convert Pydantic metrics to summary dict format
            metrics_data = execution_state.metrics
            total_token_usage = {"input": 0, "output": 0, "total": 0}

            node_breakdown = []
            for node_id, node_metrics in metrics_data.node_metrics.items():
                # Accumulate token usage (llm_usage is a Pydantic model, not a dict)
                if node_metrics.llm_usage:
                    total_token_usage["input"] += node_metrics.llm_usage.input or 0
                    total_token_usage["output"] += node_metrics.llm_usage.output or 0
                    total_token_usage["total"] += node_metrics.llm_usage.total or 0

                # Convert llm_usage Pydantic model to dict
                token_usage_dict = {"input": 0, "output": 0, "total": 0}
                if node_metrics.llm_usage:
                    token_usage_dict = {
                        "input": node_metrics.llm_usage.input or 0,
                        "output": node_metrics.llm_usage.output or 0,
                        "total": node_metrics.llm_usage.total or 0,
                    }

                node_breakdown.append(
                    {
                        "node_id": node_id,
                        "node_type": node_metrics.node_type,
                        "duration_ms": node_metrics.duration_ms,
                        "token_usage": token_usage_dict,
                        "error": node_metrics.error,
                        "module_timings": node_metrics.module_timings or {},
                    }
                )

            bottlenecks = []
            if metrics_data.bottlenecks:
                for bottleneck in metrics_data.bottlenecks[:5]:
                    bottlenecks.append(
                        {
                            "node_id": bottleneck.node_id,
                            "node_type": bottleneck.node_type,
                            "duration_ms": bottleneck.duration_ms,
                        }
                    )

            metrics_summary = {
                "execution_id": str(metrics_data.execution_id),
                "total_duration_ms": metrics_data.total_duration_ms,
                "node_count": len(metrics_data.node_metrics),
                "total_token_usage": total_token_usage,
                "bottlenecks": bottlenecks,
                "critical_path_length": len(metrics_data.critical_path)
                if metrics_data.critical_path
                else 0,
                "parallelizable_groups": len(metrics_data.parallelizable_groups)
                if metrics_data.parallelizable_groups
                else 0,
                "node_breakdown": node_breakdown,
            }

            if output_json:
                print(json.dumps(metrics_summary, indent=2, default=str))
            else:
                await self.display.display_metrics(
                    metrics_summary, breakdown, bottlenecks_only, optimizations_only
                )

            return True

        except Exception as e:
            logger.error(f"Failed to display metrics: {e}", exc_info=True)
            return False

    async def show_stats(self, diagram_path: str) -> bool:
        """Show diagram statistics."""
        try:
            diagram_data, _ = await self.diagram_loader.load_diagram(diagram_path, None)

            node_count = len(diagram_data.get("nodes", []))
            edge_count = len(diagram_data.get("edges", []))

            print(f"\n📊 Diagram Statistics: {diagram_path}")
            print(f"  Nodes: {node_count}")
            print(f"  Edges: {edge_count}")

            node_types = {}
            for node in diagram_data.get("nodes", []):
                node_type = node.get("type", "unknown")
                node_types[node_type] = node_types.get(node_type, 0) + 1

            print("\n  Node Types:")
            for node_type, count in sorted(node_types.items()):
                print(f"    {node_type}: {count}")

            return True

        except Exception as e:
            logger.error(f"Failed to show stats: {e}")
            return False

    async def manage_integrations(self, action: str, **kwargs) -> bool:
        """Manage API integrations."""
        try:
            from dipeo.application.integrations.manager import IntegrationsManager

            manager = IntegrationsManager(self.registry)

            if action == "init":
                path = kwargs.get("path", "./integrations")
                result = await manager.initialize_workspace(path)

            elif action == "validate":
                path = kwargs.get("path", "./integrations")
                provider = kwargs.get("provider")
                result = await manager.validate_providers(path, provider)

            elif action == "openapi-import":
                result = await manager.import_openapi(
                    kwargs["openapi_path"],
                    kwargs["name"],
                    kwargs.get("output"),
                    kwargs.get("base_url"),
                )

            elif action == "test":
                result = await manager.test_provider(
                    kwargs["provider"],
                    kwargs.get("operation"),
                    kwargs.get("config"),
                    kwargs.get("record", False),
                    kwargs.get("replay", False),
                )

            elif action == "claude-code":
                result = await manager.setup_claude_code_sync(
                    kwargs.get("watch_todos", False),
                    kwargs.get("sync_mode", "off"),
                    kwargs.get("output_dir"),
                    kwargs.get("auto_execute", False),
                    kwargs.get("debounce", 2.0),
                    kwargs.get("timeout"),
                )
            else:
                print(f"❌ Unknown action: {action}")
                return False

            return result

        except Exception as e:
            logger.error(f"Integration management failed: {e}")
            return False

    async def manage_claude_code(self, action: str, **kwargs) -> bool:
        """Manage Claude Code session conversion."""
        try:
            from pathlib import Path

            from dipeo.infrastructure.cc_translate import ClaudeCodeManager

            session_dir = None
            if project := kwargs.get("project"):
                session_dir = Path.home() / ".claude" / "projects" / project
                if not session_dir.exists():
                    print(f"❌ Project directory not found: {session_dir}")
                    return False

            manager = ClaudeCodeManager(session_dir=session_dir)

            if action == "list":
                sessions = manager.list_sessions(kwargs.get("limit", 50))
                for session in sessions:
                    print(f"  {session.id}: {session.name} ({session.created_at})")
                return True

            elif action == "convert":
                session_id = kwargs.get("session_id")
                latest = kwargs.get("latest", False)

                if latest:
                    sessions = manager.list_sessions(latest if isinstance(latest, int) else 1)
                    if not sessions:
                        print("No sessions found")
                        return False
                    results = []
                    for session in sessions:
                        result = manager.convert_session(
                            session.id,
                            kwargs.get("output_dir"),
                            kwargs.get("format", "light"),
                        )
                        results.append(result)
                    return all(results)
                elif session_id:
                    return manager.convert_session(
                        session_id,
                        kwargs.get("output_dir"),
                        kwargs.get("format", "light"),
                    )
                else:
                    print("Either session_id or --latest required")
                    return False

            elif action == "watch":
                return await manager.watch_sessions(
                    kwargs.get("interval", 30),
                    kwargs.get("output_dir"),
                    kwargs.get("format", "light"),
                )

            elif action == "stats":
                stats = await manager.get_session_stats(kwargs["session_id"])
                print(json.dumps(stats, indent=2, default=str))
                return True

            else:
                print(f"❌ Unknown action: {action}")
                return False

        except Exception as e:
            logger.error(f"Claude Code management failed: {e}")
            return False
