"""
Executors for different node types in the unified execution engine.
"""

from typing import Any, Dict

from .executor_utils import (
    get_downstream_nodes,
    get_input_values,
    get_upstream_nodes,
    has_incoming_connection,
    has_outgoing_connection,
    substitute_variables,
)
from .validator import (
    ValidationResult,
    check_api_keys,
    merge_validation_results,
    validate_enum_field,
    validate_file_path,
    validate_positive_integer,
    validate_property_types,
    validate_required_fields,
    validate_required_properties,
)


def create_executors(
    llm_service=None, file_service=None, memory_service=None, notion_service=None
) -> Dict[str, Any]:
    """
    Create executor instances based on available services.

    Args:
        llm_service: LLMService instance for LLM-based executors
        file_service: FileService instance for file operations
        memory_service: MemoryService instance for conversation history
        notion_service: NotionService instance for Notion API operations

    Returns:
        Dictionary mapping node types to executor instances
    """
    from .registry import create_executor

    # Prepare services dictionary
    services = {
        "llm_service": llm_service,
        "file_service": file_service,
        "memory_service": memory_service,
        "notion_service": notion_service,
    }

    # Create unified executor with services
    unified_executor = create_executor(services)

    # Create context adapter that provides services to unified executor
    class ContextAdapter:
        def __init__(self, original_ctx, services, current_node_id=None):
            self._original = original_ctx
            self._services = services
            self._current_node_id = current_node_id

        def __getattr__(self, name):
            # First check if it's a service
            if name in self._services:
                return self._services[name]
            # Otherwise delegate to original context
            return getattr(self._original, name)

        @property
        def edges(self):
            # Convert arrow format for unified executor
            if hasattr(self._original, "graph"):
                edges = []
                # Iterate through all arrows in both incoming and outgoing
                all_arrows = set()
                for arrow_list in self._original.graph.incoming.values():
                    all_arrows.update(arrow_list)
                for arrow_list in self._original.graph.outgoing.values():
                    all_arrows.update(arrow_list)

                for arrow in all_arrows:
                    edges.append(
                        {
                            "source": arrow.source,
                            "target": arrow.target,
                            "sourceHandle": arrow.s_handle or "output",
                            "targetHandle": arrow.t_handle or "input",
                        }
                    )
                return edges
            return []

        @property
        def results(self):
            # Convert outputs to results format
            outputs = getattr(self._original, "outputs", {})
            return {node_id: {"output": output} for node_id, output in outputs.items()}

        @property
        def current_node_id(self):
            return self._current_node_id

        def get_node_execution_count(self, node_id: str) -> int:
            """Get execution count for a specific node."""
            if hasattr(self._original, "exec_cnt"):
                return self._original.exec_cnt.get(node_id, 0)
            return 0

        def increment_node_execution_count(self, node_id: str) -> None:
            """Increment execution count for a specific node."""
            if hasattr(self._original, "exec_cnt"):
                self._original.exec_cnt[node_id] = (
                    self._original.exec_cnt.get(node_id, 0) + 1
                )

    # Create wrapper executors for each node type
    executors = {}
    services = {
        "llm_service": llm_service,
        "file_service": file_service,
        "memory_service": memory_service,
        "notion_service": notion_service,
        "api_keys": {},  # This should be populated from context
    }

    for node_type in unified_executor.get_supported_types():
        # Create a wrapper that adapts the context
        class UnifiedWrapper:
            def __init__(self, executor, node_type, services):
                self.unified_executor = executor
                self.node_type = node_type
                self.services = services

            async def execute(self, node, context):
                # Get current node ID
                node_id = node.get("id", "unknown")

                # Adapt context to include services
                adapted_context = ContextAdapter(context, self.services, node_id)

                # Get API keys from original context if available
                if hasattr(context, "api_keys"):
                    self.services["api_keys"] = context.api_keys
                elif hasattr(context, "persons"):
                    # Extract API keys from persons if needed
                    self.services["api_keys"] = {}

                # Execute using unified executor
                result = await self.unified_executor.execute(node, adapted_context)

                # Return result directly
                return result

        executors[node_type] = UnifiedWrapper(unified_executor, node_type, services)

    return executors


__all__ = [
    "ValidationResult",
    "create_executors",
    # Utility functions
    "get_input_values",
    "substitute_variables",
    "validate_required_properties",
    "validate_property_types",
    "has_incoming_connection",
    "has_outgoing_connection",
    "get_upstream_nodes",
    "get_downstream_nodes",
    "check_api_keys",
    "validate_required_fields",
    "validate_enum_field",
    "validate_positive_integer",
    "validate_file_path",
    "merge_validation_results",
]
