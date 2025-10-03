"""CLI runner that executes commands directly using services."""

import asyncio
import contextlib
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Optional

from dipeo.application.bootstrap import Container
from dipeo.application.execution import ExecuteDiagramUseCase
from dipeo.application.registry.keys import DIAGRAM_PORT, MESSAGE_ROUTER, STATE_STORE
from dipeo.config import BASE_DIR
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.domain_models import ExecutionID
from dipeo.diagram_generated.enums import DiagramFormat, Status
from dipeo.diagram_generated.graphql.inputs import ExecuteDiagramInput
from dipeo.infrastructure.diagram.adapters import UnifiedSerializerAdapter

logger = get_module_logger(__name__)


class CLIRunner:
    """CLI runner that uses direct service calls instead of HTTP/GraphQL."""

    def __init__(self, container: Container):
        """Initialize CLI runner with dependency container."""
        self.container = container
        self.registry = container.registry

    async def run_diagram(
        self,
        diagram: str,
        debug: bool = False,
        timeout: int = 300,
        format_type: Optional[str] = None,
        input_variables: Optional[dict[str, Any]] = None,
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

            # Load diagram
            domain_diagram = None
            diagram_data = await self._load_diagram(diagram, format_type)

            # Convert to domain diagram
            serializer = UnifiedSerializerAdapter()
            await serializer.initialize()

            format_hint = format_type or "native"
            if format_hint in ["light", "readable"]:
                import yaml

                content = yaml.dump(diagram_data, default_flow_style=False, sort_keys=False)
                domain_diagram = serializer.deserialize_from_storage(content, format_hint)
            else:
                json_content = json.dumps(diagram_data)
                domain_diagram = serializer.deserialize_from_storage(json_content, "native")

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

            # Execute diagram
            success = False

            async def run_execution():
                nonlocal success
                async for _update in use_case.execute_diagram(
                    diagram=domain_diagram,
                    options=options,
                    execution_id=str(execution_id),
                ):
                    # Process updates
                    if not simple:
                        print(".", end="", flush=True)

                # Get final result
                result = await state_store.get_execution(str(execution_id))
                success = result and result.status == Status.COMPLETED

                # Display results
                if not simple:
                    await self._display_rich_results(result)
                else:
                    await self._display_simple_results(result)

            # Run execution
            task = asyncio.create_task(run_execution())
            try:
                await asyncio.wait_for(task, timeout=timeout)
            except TimeoutError:
                logger.error(f"Execution timed out after {timeout} seconds")
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

                # Try to mark execution as failed in state store
                try:
                    from dipeo.domain.events import EventType, ExecutionEvent

                    result = await state_store.get_execution(str(execution_id))
                    if result and result.status == Status.RUNNING:
                        logger.warning(
                            f"Execution {execution_id} still RUNNING after timeout. "
                            f"Executed nodes: {result.executed_nodes}"
                        )
                        # Emit EXECUTION_ERROR event to update state
                        event = ExecutionEvent(
                            event_type=EventType.EXECUTION_ERROR,
                            execution_id=str(execution_id),
                            timestamp=None,
                            error=f"Execution timed out after {timeout} seconds",
                        )
                        await message_router.publish(event)
                except Exception as update_err:
                    logger.error(f"Failed to update execution state after timeout: {update_err}")

                if not simple:
                    print(f"\n❌ Execution timed out after {timeout} seconds")
                return False

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
        """Generate a diagram from natural language."""
        try:
            from dipeo.application.ai.dipeodipeo import DiPeOAIGenerator

            generator = DiPeOAIGenerator()
            result = await generator.generate_diagram_from_request(
                request=request,
                timeout=timeout,
            )

            if result and result.diagram_path:
                print(f"✅ Generated diagram: {result.diagram_path}")

                if and_run:
                    print("🚀 Running generated diagram...")
                    return await self.run_diagram(
                        str(result.diagram_path),
                        debug=debug,
                        timeout=run_timeout,
                    )

            return bool(result and result.success)

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
        from_format: Optional[str] = None,
        to_format: Optional[str] = None,
    ) -> bool:
        """Convert between diagram formats."""
        try:
            from dipeo.application.diagrams.converters import DiagramConverter

            converter = DiagramConverter()

            # Load input diagram
            input_file = Path(input_path)
            if not input_file.exists():
                print(f"❌ Input file not found: {input_path}")
                return False

            # Detect formats if not specified
            if not from_format:
                from_format = self._detect_format(input_path)
            if not to_format:
                to_format = self._detect_format(output_path)

            # Convert
            result = converter.convert(
                input_path,
                output_path,
                DiagramFormat(from_format),
                DiagramFormat(to_format),
            )

            if result:
                print(f"✅ Converted {input_path} to {output_path}")
                return True
            else:
                print("❌ Conversion failed")
                return False

        except Exception as e:
            logger.error(f"Diagram conversion failed: {e}")
            return False

    async def show_metrics(
        self,
        execution_id: Optional[str] = None,
        diagram_id: Optional[str] = None,
        bottlenecks_only: bool = False,
        optimizations_only: bool = False,
        output_json: bool = False,
    ) -> bool:
        """Display execution metrics."""
        try:
            from dipeo.application.execution.observers import MetricsObserver
            from dipeo.application.registry.keys import ServiceKey

            # Get metrics observer
            metrics_observer_key = ServiceKey[MetricsObserver]("metrics_observer")
            if not self.registry.has(metrics_observer_key):
                print(
                    "❌ Metrics observer not available. Ensure server was started with metrics enabled."
                )
                return False

            metrics_observer = self.registry.resolve(metrics_observer_key)
            state_store = self.registry.resolve(STATE_STORE)

            # Determine which execution to get metrics for
            target_execution_id = None

            if execution_id:
                target_execution_id = execution_id
            elif diagram_id:
                # Get latest execution for diagram
                executions = await state_store.list_executions(diagram_id=diagram_id, limit=1)
                if executions:
                    target_execution_id = executions[0].id
                else:
                    print(f"No executions found for diagram: {diagram_id}")
                    return False
            else:
                # Get the most recent execution
                executions = await state_store.list_executions(limit=1)
                if executions:
                    target_execution_id = executions[0].id
                else:
                    print("No executions found")
                    return False

            # Get metrics from the observer
            metrics = metrics_observer.get_metrics_summary(str(target_execution_id))

            if not metrics:
                print("No metrics available")
                return False

            # Display metrics
            if output_json:
                print(json.dumps(metrics, indent=2, default=str))
            else:
                await self._display_metrics(metrics, bottlenecks_only, optimizations_only)

            return True

        except Exception as e:
            logger.error(f"Failed to display metrics: {e}")
            return False

    async def show_stats(self, diagram_path: str) -> bool:
        """Show diagram statistics."""
        try:
            diagram_data = await self._load_diagram(diagram_path, None)

            # Calculate stats
            node_count = len(diagram_data.get("nodes", []))
            edge_count = len(diagram_data.get("edges", []))

            print(f"\n📊 Diagram Statistics: {diagram_path}")
            print(f"  Nodes: {node_count}")
            print(f"  Edges: {edge_count}")

            # Show node types
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
            from dipeo.infrastructure.cc_translate import ClaudeCodeManager

            manager = ClaudeCodeManager()

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
                        result = await manager.convert_session(
                            session.id,
                            kwargs.get("output_dir"),
                            kwargs.get("format", "light"),
                        )
                        results.append(result)
                    return all(results)
                elif session_id:
                    return await manager.convert_session(
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

    # Helper methods
    async def _load_diagram(self, diagram: str, format_type: Optional[str]) -> dict[str, Any]:
        """Load diagram from file."""
        from dipeo.application.diagrams.loaders import DiagramLoader

        loader = DiagramLoader()
        diagram_path = loader.resolve_diagram_path(diagram, format_type)
        return loader.load_diagram(diagram_path)

    def _detect_format(self, file_path: str) -> str:
        """Detect diagram format from file extension."""
        path = Path(file_path)
        if path.suffix in [".yml", ".yaml"]:
            # Check if it's light format by looking for specific markers
            with open(path) as f:
                content = f.read()
                if "nodes:" in content and "edges:" in content:
                    return "light"
                else:
                    return "readable"
        elif path.suffix == ".json":
            return "native"
        else:
            return "native"  # Default

    async def _display_rich_results(self, result: Any) -> None:
        """Display results using rich formatting."""
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table

            console = Console()

            if result and result.status == Status.COMPLETED:
                console.print(Panel.fit("✅ Execution Successful", style="green bold"))
            else:
                console.print(Panel.fit("❌ Execution Failed", style="red bold"))

            # Display outputs
            if hasattr(result, "node_outputs") and result.node_outputs:
                table = Table(title="Outputs")
                table.add_column("Node", style="cyan")
                table.add_column("Output", style="white")

                for node_id, output in result.node_outputs.items():
                    table.add_row(node_id, str(output)[:100])

                console.print(table)

        except ImportError:
            # Fallback to simple display if rich is not available
            await self._display_simple_results(result)

    async def _display_simple_results(self, result: Any) -> None:
        """Display results using simple text formatting."""
        if result and result.status == Status.COMPLETED:
            print("✅ Execution Successful")
        else:
            print("❌ Execution Failed")

        if hasattr(result, "node_outputs") and result.node_outputs:
            print("\nOutputs:")
            for node_id, output in result.node_outputs.items():
                print(f"  {node_id}: {str(output)[:100]}")

    async def _display_metrics(
        self,
        metrics: dict[str, Any],
        bottlenecks_only: bool,
        optimizations_only: bool,
    ) -> None:
        """Display metrics in human-readable format."""
        print("\n📊 Execution Metrics")
        print(f"  Execution ID: {metrics.get('execution_id')}")
        print(f"  Total Duration: {metrics.get('total_duration_ms', 0):.2f}ms")
        print(f"  Nodes Executed: {metrics.get('nodes_executed', 0)}")

        if bottlenecks_only or not optimizations_only:
            bottlenecks = metrics.get("bottlenecks", [])
            if bottlenecks:
                print("\n⚠️ Bottlenecks:")
                for bottleneck in bottlenecks:
                    print(f"  - {bottleneck}")

        if optimizations_only or not bottlenecks_only:
            optimizations = metrics.get("optimization_suggestions", [])
            if optimizations:
                print("\n💡 Optimization Suggestions:")
                for suggestion in optimizations:
                    print(f"  - {suggestion}")
