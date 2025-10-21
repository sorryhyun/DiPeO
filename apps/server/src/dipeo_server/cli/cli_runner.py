"""CLI runner that executes commands directly using services."""

from typing import Any

from dipeo.application.bootstrap import Container
from dipeo_server.cli.commands import ClaudeCodeCommandManager, IntegrationCommandManager

from .compilation import DiagramCompiler
from .conversion import DiagramConverter
from .core import DiagramLoader
from .display import MetricsManager
from .execution import DiagramExecutor
from .query import DiagramQuery


class CLIRunner:
    """CLI runner that delegates to specialized handlers."""

    def __init__(self, container: Container):
        self.container = container
        self.registry = container.registry
        self.diagram_loader = DiagramLoader()

        self.executor = DiagramExecutor(container)
        self.converter = DiagramConverter(container)
        self.compiler = DiagramCompiler(container)
        self.query = DiagramQuery(container)
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
        execution_id: str | None = None,
    ) -> bool:
        """Execute a diagram using direct service calls."""
        return await self.executor.run_diagram(
            diagram=diagram,
            debug=debug,
            timeout=timeout,
            format_type=format_type,
            input_variables=input_variables,
            use_unified=use_unified,
            simple=simple,
            interactive=interactive,
            execution_id=execution_id,
        )

    async def ask_diagram(
        self,
        request: str,
        and_run: bool = False,
        debug: bool = False,
        timeout: int = 90,
        run_timeout: int = 300,
    ) -> bool:
        """Generate a diagram from natural language."""
        return await self.executor.ask_diagram(
            request=request,
            and_run=and_run,
            debug=debug,
            timeout=timeout,
            run_timeout=run_timeout,
        )

    async def convert_diagram(
        self,
        input_path: str,
        output_path: str,
        from_format: str | None = None,
        to_format: str | None = None,
    ) -> bool:
        """Convert between diagram formats."""
        return await self.converter.convert_diagram(
            input_path=input_path,
            output_path=output_path,
            from_format=from_format,
            to_format=to_format,
        )

    async def export_diagram(
        self,
        diagram_path: str,
        output_path: str,
        format_type: str | None = None,
    ) -> bool:
        """Export diagram to Python script."""
        return await self.converter.export_diagram(
            diagram_path=diagram_path,
            output_path=output_path,
            format_type=format_type,
        )

    async def compile_diagram(
        self,
        diagram_path: str | None,
        format_type: str | None = None,
        check_only: bool = False,
        output_json: bool = False,
        use_stdin: bool = False,
        push_as: str | None = None,
        target_dir: str | None = None,
    ) -> bool:
        """Compile and validate diagram without executing it."""
        return await self.compiler.compile_diagram(
            diagram_path=diagram_path,
            format_type=format_type,
            check_only=check_only,
            output_json=output_json,
            use_stdin=use_stdin,
            push_as=push_as,
            target_dir=target_dir,
        )

    async def show_results(self, session_id: str, verbose: bool = False) -> bool:
        """Query execution status and results by session_id."""
        return await self.query.show_results(session_id=session_id, verbose=verbose)

    async def list_diagrams(
        self, output_json: bool = False, format_filter: str | None = None
    ) -> bool:
        """List available diagrams."""
        return await self.query.list_diagrams(
            output_json=output_json,
            format_filter=format_filter,
        )

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
        """Display execution metrics from database."""
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
        """Show diagram statistics."""
        return await self.metrics_manager.show_stats(diagram_path)

    async def manage_integrations(self, action: str, **kwargs) -> bool:
        """Manage API integrations."""
        return await self.integration_manager.manage_integrations(action, **kwargs)

    async def manage_claude_code(self, action: str, **kwargs) -> bool:
        """Manage Claude Code session conversion."""
        return await self.claude_code_manager.manage_claude_code(action, **kwargs)
