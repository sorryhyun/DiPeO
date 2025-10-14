"""CLI runner that executes commands directly using services."""

import asyncio
import contextlib
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
from dipeo_server.cli.commands import ClaudeCodeCommandManager, IntegrationCommandManager
from dipeo_server.cli.core import DiagramLoader, SessionManager
from dipeo_server.cli.display import DisplayManager, MetricsManager
from dipeo_server.cli.handlers import cli_interactive_handler

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

        # Initialize specialized managers
        self.metrics_manager = MetricsManager(container)
        self.integration_manager = IntegrationCommandManager(container)
        self.claude_code_manager = ClaudeCodeCommandManager(container)

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
                    from dipeo_server.cli.handlers import EventForwarder

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
                    interactive_handler=cli_interactive_handler if interactive else None,
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
        """Display execution metrics from database (no server required).

        Delegates to MetricsManager for implementation.
        """
        return await self.metrics_manager.show_metrics(
            execution_id=execution_id,
            latest=latest,
            diagram_id=diagram_id,
            breakdown=breakdown,
            bottlenecks_only=bottlenecks_only,
            optimizations_only=optimizations_only,
            output_json=output_json,
        )

    async def show_stats(self, diagram_path: str) -> bool:
        """Show diagram statistics.

        Delegates to MetricsManager for implementation.
        """
        return await self.metrics_manager.show_stats(diagram_path)

    async def manage_integrations(self, action: str, **kwargs) -> bool:
        """Manage API integrations.

        Delegates to IntegrationCommandManager for implementation.
        """
        return await self.integration_manager.manage_integrations(action, **kwargs)

    async def manage_claude_code(self, action: str, **kwargs) -> bool:
        """Manage Claude Code session conversion.

        Delegates to ClaudeCodeCommandManager for implementation.
        """
        return await self.claude_code_manager.manage_claude_code(action, **kwargs)

    async def export_diagram(
        self,
        diagram_path: str,
        output_path: str,
        format_type: str | None = None,
    ) -> bool:
        """Export diagram to Python script."""
        try:
            from dipeo.domain.diagram.compilation import PythonDiagramCompiler

            # Load diagram
            (
                domain_diagram,
                diagram_data,
                diagram_file_path,
            ) = await self.diagram_loader.load_and_deserialize(diagram_path, format_type)

            if not domain_diagram:
                print(f"❌ Failed to load diagram: {diagram_path}")
                return False

            # Export to Python
            compiler = PythonDiagramCompiler()
            return compiler.export(domain_diagram, output_path)

        except Exception as e:
            logger.error(f"Diagram export failed: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def compile_diagram(
        self,
        diagram_path: str,
        format_type: str | None = None,
        check_only: bool = False,
        output_json: bool = False,
    ) -> bool:
        """Compile and validate diagram without executing it."""
        try:
            from dipeo.domain.diagram.compilation import DomainDiagramCompiler

            # Load diagram
            (
                domain_diagram,
                diagram_data,
                diagram_file_path,
            ) = await self.diagram_loader.load_and_deserialize(diagram_path, format_type)

            if not domain_diagram:
                print(f"❌ Failed to load diagram: {diagram_path}")
                return False

            # Compile with diagnostics
            compiler = DomainDiagramCompiler()
            result = compiler.compile_with_diagnostics(domain_diagram)

            # Output results
            if output_json:
                import json

                output = {
                    "valid": result.is_valid,
                    "errors": [
                        {
                            "phase": e.phase.name,
                            "message": e.message,
                            "severity": e.severity,
                            "node_id": str(e.node_id) if e.node_id else None,
                        }
                        for e in result.errors
                    ],
                    "warnings": [
                        {
                            "phase": w.phase.name,
                            "message": w.message,
                            "severity": w.severity,
                            "node_id": str(w.node_id) if w.node_id else None,
                        }
                        for w in result.warnings
                    ],
                }
                if result.diagram:
                    output["node_count"] = len(result.diagram.nodes)
                    output["edge_count"] = len(result.diagram.edges)
                print(json.dumps(output, indent=2))
            else:
                # Human-readable output
                if result.is_valid:
                    print(f"✅ Diagram compiled successfully: {diagram_path}")
                    if result.diagram:
                        print(f"   Nodes: {len(result.diagram.nodes)}")
                        print(f"   Edges: {len(result.diagram.edges)}")
                else:
                    print(f"❌ Compilation failed: {diagram_path}")

                if result.warnings:
                    print(f"\n⚠️  Warnings ({len(result.warnings)}):")
                    for w in result.warnings:
                        print(f"   [{w.phase.name}] {w.message}")

                if result.errors:
                    print(f"\n❌ Errors ({len(result.errors)}):")
                    for e in result.errors:
                        print(f"   [{e.phase.name}] {e.message}")

            return result.is_valid

        except Exception as e:
            logger.error(f"Diagram compilation failed: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def list_diagrams(
        self, output_json: bool = False, format_filter: str | None = None
    ) -> bool:
        """List available diagrams in projects/ and examples/simple_diagrams/."""
        try:
            from dipeo.config import BASE_DIR

            diagrams = []

            # Scan projects/ and examples/simple_diagrams/
            scan_dirs = [
                BASE_DIR / "projects",
                BASE_DIR / "examples" / "simple_diagrams",
            ]

            for base_dir in scan_dirs:
                if not base_dir.exists():
                    continue

                # Find all diagram files
                for ext in [".light.yaml", ".light.yml", ".yaml", ".yml", ".json"]:
                    for diagram_file in base_dir.rglob(f"*{ext}"):
                        # Detect format
                        if ".light." in diagram_file.name:
                            detected_format = "light"
                        elif diagram_file.suffix == ".json":
                            detected_format = "native"
                        else:
                            detected_format = "readable"

                        # Apply format filter
                        if format_filter and detected_format != format_filter:
                            continue

                        # Try to load and get node count
                        node_count = None
                        description = None
                        try:
                            import json

                            import yaml

                            with open(diagram_file, encoding="utf-8") as f:
                                if diagram_file.suffix == ".json":
                                    data = json.load(f)
                                else:
                                    data = yaml.safe_load(f)

                                if isinstance(data, dict):
                                    # Count nodes
                                    if "nodes" in data:
                                        node_count = len(data["nodes"])

                                    # Get description from metadata
                                    if "metadata" in data and isinstance(data["metadata"], dict):
                                        description = data["metadata"].get("description")
                        except Exception:
                            pass

                        diagrams.append(
                            {
                                "name": diagram_file.stem,
                                "path": str(diagram_file.relative_to(BASE_DIR)),
                                "format": detected_format,
                                "nodes": node_count,
                                "description": description,
                            }
                        )

            # Sort by path
            diagrams.sort(key=lambda d: d["path"])

            # Output results
            if output_json:
                import json

                print(json.dumps({"diagrams": diagrams}, indent=2))
            else:
                if not diagrams:
                    print("No diagrams found in projects/ or examples/simple_diagrams/")
                    return True

                print(f"Found {len(diagrams)} diagram(s):\n")
                for d in diagrams:
                    print(f"  {d['name']}")
                    print(f"    Path:   {d['path']}")
                    print(f"    Format: {d['format']}")
                    if d["nodes"] is not None:
                        print(f"    Nodes:  {d['nodes']}")
                    if d["description"]:
                        print(f"    Desc:   {d['description']}")
                    print()

            return True

        except Exception as e:
            logger.error(f"Failed to list diagrams: {e}")
            import traceback

            traceback.print_exc()
            return False
