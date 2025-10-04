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

            # Load diagram
            domain_diagram = None
            diagram_data, diagram_path = await self._load_diagram(diagram, format_type)

            # Convert to domain diagram
            serializer = UnifiedSerializerAdapter()
            await serializer.initialize()

            format_hint = format_type or "native"
            if format_hint in ["light", "readable"]:
                import yaml

                content = yaml.dump(diagram_data, default_flow_style=False, sort_keys=False)
                domain_diagram = serializer.deserialize_from_storage(
                    content, format_hint, diagram_path
                )
            else:
                json_content = json.dumps(diagram_data)
                domain_diagram = serializer.deserialize_from_storage(
                    json_content, "native", diagram_path
                )

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
                # Convert to native format (already in array form from domain_diagram)
                native_data = {
                    "nodes": [node.model_dump() for node in domain_diagram.nodes],
                    "arrows": [arrow.model_dump() for arrow in domain_diagram.arrows],
                    "handles": [handle.model_dump() for handle in domain_diagram.handles],
                    "persons": [person.model_dump() for person in (domain_diagram.persons or [])],
                }

            # Register CLI session for monitor mode support
            await self._register_cli_session(
                execution_id=str(execution_id),
                diagram_name=diagram,
                diagram_format="native",  # Always send native format to frontend
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
                    # Process updates
                    if not simple:
                        print(".", end="", flush=True)

                # Check if execution completed naturally
                if last_update and last_update.get("type") == "execution_complete":
                    success = True
                    # Give async event handlers time to persist state
                    await asyncio.sleep(0.1)

                # Get final result from state store
                result = await state_store.get_execution(str(execution_id))

                # Only check persisted status if execution didn't complete naturally
                # This handles edge cases with nested sub-diagrams that have endpoint nodes
                if not success and result:
                    success = result.status == Status.COMPLETED

                # Display results
                if not simple:
                    await self._display_rich_results(result, success)
                else:
                    await self._display_simple_results(result, success)

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
                    from dipeo.domain.events import execution_error

                    result = await state_store.get_execution(str(execution_id))
                    if result and result.status == Status.RUNNING:
                        logger.warning(
                            f"Execution {execution_id} still RUNNING after timeout. "
                            f"Executed nodes: {result.executed_nodes}"
                        )
                        # Emit EXECUTION_ERROR event to update state
                        event = execution_error(
                            execution_id=str(execution_id),
                            error_message=f"Execution timed out after {timeout} seconds",
                        )
                        await message_router.publish(event)
                except Exception as update_err:
                    logger.error(f"Failed to update execution state after timeout: {update_err}")

                # Cleanup container resources (especially Claude Code sessions)
                try:
                    await self.container.shutdown()
                    logger.info("Container shutdown complete after timeout")
                except Exception as cleanup_err:
                    logger.error(f"Failed to cleanup container after timeout: {cleanup_err}")

                if not simple:
                    print(f"\n❌ Execution timed out after {timeout} seconds")

                # Unregister CLI session
                await self._unregister_cli_session(str(execution_id))

                return False
            finally:
                # Always unregister CLI session when execution completes
                await self._unregister_cli_session(str(execution_id))

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
            # Run the dipeodipeo parallel generator diagram with the user's request
            print("🤖 Generating diagram using DiPeO AI parallel generator...")
            success = await self.run_diagram(
                "projects/dipeodipeo/parallel_generator",
                format_type="light",
                input_variables={"workflow_description": request},
                debug=debug,
                timeout=timeout,
                simple=True,  # Suppress detailed output during generation
            )

            if not success:
                print("❌ Diagram generation failed")
                return False

            # The generated diagram should be in projects/dipeo_ai/generated/
            # TODO: Extract the actual path from execution results
            print("✅ Diagram generated successfully")

            if and_run:
                # TODO: Get the actual generated diagram path and run it
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
            from dipeo.infrastructure.diagram.adapters.serializer_adapter import (
                UnifiedSerializerAdapter,
            )

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

            # Read input file
            with open(input_path, encoding="utf-8") as f:
                content = f.read()

            # Create use case and convert
            serializer = UnifiedSerializerAdapter()
            await serializer.initialize()
            use_case = SerializeDiagramUseCase(serializer)

            converted_content = use_case.convert_format(content, to_format, from_format)

            # Write output file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(converted_content)

            print(f"✅ Converted {input_path} to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Diagram conversion failed: {e}")
            return False

    async def show_metrics(
        self,
        execution_id: str | None = None,
        diagram_id: str | None = None,
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
            diagram_data, _ = await self._load_diagram(diagram_path, None)

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
            from pathlib import Path

            from dipeo.infrastructure.cc_translate import ClaudeCodeManager

            # Resolve project directory if specified
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

    # Helper methods
    async def _is_server_available(self) -> bool:
        """Quick check if server is available."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=0.5) as client:
                await client.get("http://localhost:8000/health")
                return True
        except Exception:
            return False

    async def _register_cli_session(
        self,
        execution_id: str,
        diagram_name: str,
        diagram_format: str,
        diagram_data: dict[str, Any] | None = None,
    ) -> None:
        """Register a CLI session via GraphQL mutation to the running server."""
        try:
            import httpx

            from dipeo.diagram_generated.graphql.inputs import RegisterCliSessionInput
            from dipeo.diagram_generated.graphql.operations import RegisterCliSessionOperation

            # Build input using generated types (use uppercase string for GraphQL enum)
            input_data = RegisterCliSessionInput(
                execution_id=execution_id,
                diagram_name=diagram_name,
                diagram_format=diagram_format.upper(),
                diagram_data=diagram_data,
            )

            # Use generated operation to get query and variables
            variables = RegisterCliSessionOperation.get_variables_dict(input=input_data)
            query = RegisterCliSessionOperation.get_query()

            # Retry logic for server availability (useful when server just started)
            max_retries = 5
            retry_delay = 0.5  # Start with 500ms

            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.post(
                            "http://localhost:8000/graphql",
                            json={"query": query, "variables": variables},
                        )
                        result = response.json()

                        if result.get("data", {}).get("registerCliSession", {}).get("success"):
                            logger.info(f"Registered CLI session for execution {execution_id}")
                            return
                        else:
                            error = (
                                result.get("data", {}).get("registerCliSession", {}).get("error")
                            )
                            logger.warning(f"Failed to register CLI session: {error}")
                            return

                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    if attempt < max_retries - 1:
                        logger.debug(
                            f"Server not ready (attempt {attempt + 1}/{max_retries}), retrying..."
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 1.5, 2.0)  # Exponential backoff up to 2s
                    else:
                        logger.debug(f"Could not connect to server after {max_retries} attempts")
                        return

        except Exception as e:
            logger.debug(f"Could not register CLI session: {e}")

    async def _unregister_cli_session(self, execution_id: str) -> None:
        """Unregister a CLI session via GraphQL mutation to the running server."""
        try:
            # Quick check if server is available
            if not await self._is_server_available():
                return

            import httpx

            from dipeo.diagram_generated.graphql.inputs import UnregisterCliSessionInput
            from dipeo.diagram_generated.graphql.operations import UnregisterCliSessionOperation

            # Build input using generated types
            input_data = UnregisterCliSessionInput(execution_id=execution_id)

            # Use generated operation to get query and variables
            variables = UnregisterCliSessionOperation.get_variables_dict(input=input_data)
            query = UnregisterCliSessionOperation.get_query()

            # Single attempt since we already checked server availability
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.post(
                    "http://localhost:8000/graphql",
                    json={"query": query, "variables": variables},
                )
                result = response.json()

                if result.get("data", {}).get("unregisterCliSession", {}).get("success"):
                    logger.debug(f"Unregistered CLI session for execution {execution_id}")
                else:
                    error = result.get("data", {}).get("unregisterCliSession", {}).get("error")
                    logger.debug(f"Could not unregister CLI session: {error}")

        except Exception as e:
            logger.debug(f"Could not unregister CLI session: {e}")

    async def _load_diagram(
        self, diagram: str, format_type: str | None
    ) -> tuple[dict[str, Any], str]:
        """Load diagram from file.

        Returns:
            Tuple of (diagram_data, diagram_path)
        """
        import json

        import yaml

        # Resolve diagram path
        diagram_path = self._resolve_diagram_path(diagram, format_type)

        # Load diagram directly using yaml/json
        with open(diagram_path, encoding="utf-8") as f:
            if diagram_path.endswith(".json"):
                diagram_data = json.load(f)
            else:
                diagram_data = yaml.safe_load(f)

        return diagram_data, diagram_path

    def _resolve_diagram_path(self, diagram: str, format_type: str | None) -> str:
        """Resolve diagram path based on name and format."""
        diagram_path = Path(diagram)

        # If absolute path and exists, return it
        if diagram_path.is_absolute() and diagram_path.exists():
            return str(diagram_path)

        # Try relative path
        if diagram_path.exists():
            return str(diagram_path.resolve())

        # If no extension, try adding format extension
        if not diagram_path.suffix and format_type:
            extensions = {
                "light": [".light.yml", ".light.yaml"],
                "native": [".json"],
                "readable": [".yaml", ".yml"],
            }

            for ext in extensions.get(format_type, []):
                # Try in various locations
                for base_dir in [
                    Path.cwd(),
                    BASE_DIR / "examples",
                    BASE_DIR / "examples/simple_diagrams",
                    BASE_DIR / "projects",
                    BASE_DIR / "files",
                ]:
                    test_path = base_dir / f"{diagram}{ext}"
                    if test_path.exists():
                        return str(test_path)

        # Try standard locations without format extension
        for base_dir in [
            Path.cwd(),
            BASE_DIR / "examples",
            BASE_DIR / "examples/simple_diagrams",
            BASE_DIR / "projects",
            BASE_DIR / "files",
        ]:
            test_path = base_dir / diagram
            if test_path.exists():
                return str(test_path)

            # Try with common extensions
            for ext in [".json", ".yaml", ".yml", ".light.yml", ".light.yaml"]:
                test_path = base_dir / f"{diagram}{ext}"
                if test_path.exists():
                    return str(test_path)

        # Return original if nothing found
        return diagram

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

    async def _display_rich_results(self, result: Any, success: bool = False) -> None:
        """Display results using rich formatting."""
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table

            console = Console()

            if success or (result and result.status == Status.COMPLETED):
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

    async def _display_simple_results(self, result: Any, success: bool = False) -> None:
        """Display results using simple text formatting."""
        if success or (result and result.status == Status.COMPLETED):
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
