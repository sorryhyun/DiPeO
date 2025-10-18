"""Base executor for sub-diagram execution with common functionality."""

import uuid
from typing import TYPE_CHECKING, Any

from dipeo.config.base_logger import get_module_logger

if TYPE_CHECKING:
    from dipeo.diagram_generated.unified_nodes.sub_diagram_node import SubDiagramNode

logger = get_module_logger(__name__)


class BaseSubDiagramExecutor:
    """Base class for sub-diagram executors with common functionality."""

    def __init__(self):
        self._state_store = None
        self._message_router = None
        self._diagram_service = None
        self._prepare_use_case = None
        self._load_diagram_use_case = None  # Resolved from registry when available
        self._service_registry = None
        self._event_bus = None

    def set_services(self, **kwargs):
        """Set services for the executor to use.

        Subclasses can override to accept specific services.
        """
        self._state_store = kwargs.get("state_store")
        self._message_router = kwargs.get("message_router")
        self._diagram_service = kwargs.get("diagram_service")
        self._prepare_use_case = kwargs.get("prepare_use_case")
        self._service_registry = kwargs.get("service_registry")
        self._event_bus = kwargs.get("event_bus")

        if self._service_registry and not self._load_diagram_use_case:
            from dipeo.application.registry.keys import LOAD_DIAGRAM_USE_CASE

            try:
                self._load_diagram_use_case = self._service_registry.resolve(LOAD_DIAGRAM_USE_CASE)
            except Exception:
                logger.warning("LoadDiagramUseCase not found in registry, diagram loading may fail")

    def _construct_diagram_path(self, node: "SubDiagramNode") -> str:
        """Construct the file path for a diagram.

        Args:
            node: The SubDiagramNode containing diagram information

        Returns:
            The constructed file path for the diagram
        """
        if not self._load_diagram_use_case:
            format_map = {
                "light": ".light.yaml",
                "native": ".native.json",
                "readable": ".readable.yaml",
            }
            format_suffix = format_map.get(node.diagram_format or "light", ".light.yaml")
            return f"examples/{node.diagram_name}{format_suffix}"

        return self._load_diagram_use_case.construct_diagram_path(
            node.diagram_name, node.diagram_format
        )

    def _process_output_mapping(
        self, node: "SubDiagramNode", execution_results: dict[str, Any]
    ) -> Any:
        """Process output mapping from sub-diagram results.

        Returns the appropriate output based on endpoint nodes or the last output.

        Args:
            node: The SubDiagramNode being executed
            execution_results: The results from the sub-diagram execution

        Returns:
            The processed output value
        """
        endpoint_outputs = self._find_endpoint_outputs(execution_results)

        if endpoint_outputs:
            if len(endpoint_outputs) == 1:
                return next(iter(endpoint_outputs.values()))
            return endpoint_outputs

        if execution_results:
            last_key = max(execution_results.keys())
            return execution_results.get(last_key)

        return None

    def _find_endpoint_outputs(self, execution_results: dict[str, Any]) -> dict[str, Any]:
        """Find endpoint node outputs in execution results.

        Args:
            execution_results: The results from the sub-diagram execution

        Returns:
            A dictionary of endpoint outputs
        """
        return {
            k: v
            for k, v in execution_results.items()
            if k.startswith("endpoint") or k.startswith("end")
        }

    async def _load_diagram(self, node: "SubDiagramNode") -> Any:
        """Load diagram as DomainDiagram.

        Args:
            node: The SubDiagramNode containing diagram information

        Returns:
            The loaded DomainDiagram
        """
        if not self._load_diagram_use_case:
            raise ValueError("LoadDiagramUseCase not available")

        diagram_data = node.diagram_data if node.diagram_data and node.diagram_data != {} else None

        return await self._load_diagram_use_case.load_diagram(
            diagram_name=node.diagram_name if not diagram_data else None,
            diagram_format=node.diagram_format,
            diagram_data=diagram_data,
        )

    def _create_execution_id(self, parent_execution_id: str, suffix: str = "sub") -> str:
        """Create a unique execution ID for sub-diagram.

        Args:
            parent_execution_id: The parent execution ID
            suffix: The suffix to use for the execution ID

        Returns:
            A unique execution ID
        """
        return f"{parent_execution_id}_{suffix}_{uuid.uuid4().hex[:8]}"

    def _format_error_output(
        self, node: "SubDiagramNode", error: Any, **metadata
    ) -> dict[str, Any]:
        """Format an error output response.

        Args:
            node: The SubDiagramNode that failed
            error: The error that occurred
            **metadata: Additional metadata to include

        Returns:
            A formatted error output
        """
        error_data = {"error": str(error)}
        error_data.update(metadata)
        return error_data
