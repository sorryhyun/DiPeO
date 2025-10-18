"""Base executor for sub-diagram execution with common functionality."""

import uuid
from typing import TYPE_CHECKING, Any

from dipeo.config.base_logger import get_module_logger

if TYPE_CHECKING:
    from dipeo.diagram_generated.unified_nodes.sub_diagram_node import SubDiagramNode

logger = get_module_logger(__name__)


class BaseSubDiagramExecutor:
    def __init__(self):
        self._state_store = None
        self._message_router = None
        self._diagram_service = None
        self._prepare_use_case = None
        self._load_diagram_use_case = None
        self._service_registry = None
        self._event_bus = None

    def set_services(self, **kwargs):
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
        """Returns endpoint node outputs if available, otherwise the last execution result."""
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
        return {
            k: v
            for k, v in execution_results.items()
            if k.startswith("endpoint") or k.startswith("end")
        }

    async def _load_diagram(self, node: "SubDiagramNode") -> Any:
        if not self._load_diagram_use_case:
            raise ValueError("LoadDiagramUseCase not available")

        diagram_data = node.diagram_data if node.diagram_data and node.diagram_data != {} else None

        return await self._load_diagram_use_case.load_diagram(
            diagram_name=node.diagram_name if not diagram_data else None,
            diagram_format=node.diagram_format,
            diagram_data=diagram_data,
        )

    def _create_execution_id(self, parent_execution_id: str, suffix: str = "sub") -> str:
        return f"{parent_execution_id}_{suffix}_{uuid.uuid4().hex[:8]}"

    def _format_error_output(
        self, node: "SubDiagramNode", error: Any, **metadata
    ) -> dict[str, Any]:
        error_data = {"error": str(error)}
        error_data.update(metadata)
        return error_data
