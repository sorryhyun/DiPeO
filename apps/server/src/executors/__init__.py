"""
Executors for different node types in the unified execution engine.
"""
from typing import Dict, Optional

from .base_executor import BaseExecutor, ValidationResult, ExecutorResult
from .start_executor import StartExecutor
from .condition_executor import ConditionExecutor
from .job_executor import JobExecutor
from .endpoint_executor import EndpointExecutor
from .person_job_executor import PersonJobExecutor, PersonBatchJobExecutor
from .db_executor import DBExecutor
from .user_response_executor import UserResponseExecutor
from .notion_executor import NotionExecutor
from .executor_utils import (
    get_input_values,
    substitute_variables,
    has_incoming_connection,
    has_outgoing_connection,
    get_upstream_nodes,
    get_downstream_nodes,
)
from .validator import (
    validate_required_properties,
    validate_property_types,
    check_api_keys,
    validate_required_fields,
    validate_enum_field,
    validate_positive_integer,
    validate_file_path,
    validate_either_required,
    validate_json_field,
    validate_dangerous_code,
    merge_validation_results,
)


def create_executors(llm_service=None, file_service=None, memory_service=None, notion_service=None, use_unified: bool = False) -> Dict[str, BaseExecutor]:
    """
    Create executor instances based on available services.
    
    Args:
        llm_service: LLMService instance for LLM-based executors
        file_service: FileService instance for file operations
        memory_service: MemoryService instance for conversation history
        notion_service: NotionService instance for Notion API operations
        use_unified: If True, use the unified executor system (default: False for compatibility)
        
    Returns:
        Dictionary mapping node types to executor instances
    """
    # Use unified executor if requested
    if use_unified:
        from .registry import create_executor
        from .compatibility import LegacyExecutorWrapper
        from .types import ExecutionContext
        
        # Create unified executor
        unified_executor = create_executor()
        
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
                if hasattr(self._original, 'graph'):
                    edges = []
                    # Iterate through all arrows in both incoming and outgoing
                    all_arrows = set()
                    for arrow_list in self._original.graph.incoming.values():
                        all_arrows.update(arrow_list)
                    for arrow_list in self._original.graph.outgoing.values():
                        all_arrows.update(arrow_list)
                    
                    for arrow in all_arrows:
                        edges.append({
                            "source": arrow.source,
                            "target": arrow.target,
                            "sourceHandle": arrow.s_handle or "output",
                            "targetHandle": arrow.t_handle or "input"
                        })
                    return edges
                return []
            
            @property
            def results(self):
                # Convert outputs to results format
                outputs = getattr(self._original, 'outputs', {})
                return {node_id: {"output": output} for node_id, output in outputs.items()}
            
            @property
            def current_node_id(self):
                return self._current_node_id
            
            def get_node_execution_count(self, node_id: str) -> int:
                """Get execution count for a specific node."""
                if hasattr(self._original, 'exec_cnt'):
                    return self._original.exec_cnt.get(node_id, 0)
                return 0
            
            def increment_node_execution_count(self, node_id: str) -> None:
                """Increment execution count for a specific node."""
                if hasattr(self._original, 'exec_cnt'):
                    self._original.exec_cnt[node_id] = self._original.exec_cnt.get(node_id, 0) + 1
        
        # Create wrapper executors for each node type
        executors = {}
        services = {
            "llm_service": llm_service,
            "file_service": file_service,
            "memory_service": memory_service,
            "notion_service": notion_service,
            "api_keys": {}  # This should be populated from context
        }
        
        for node_type in unified_executor.get_supported_types():
            # Create a wrapper that adapts the context
            class UnifiedWrapper(BaseExecutor):
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
                    if hasattr(context, 'api_keys'):
                        self.services['api_keys'] = context.api_keys
                    elif hasattr(context, 'persons'):
                        # Extract API keys from persons if needed
                        self.services['api_keys'] = {}
                    
                    # Execute using unified executor
                    result = await self.unified_executor.execute(node, adapted_context)
                    
                    # Convert ExecutorResult to legacy format
                    from .base_executor import ExecutorResult as LegacyResult
                    return LegacyResult(
                        output=result.output,
                        error=result.error,
                        metadata=result.metadata,
                        execution_time=result.execution_time,
                        token_usage=result.token_usage
                    )
            
            executors[node_type] = UnifiedWrapper(unified_executor, node_type, services)
        
        # Add variations for person job
        if "person_job" in executors:
            executors["personjob"] = executors["person_job"]
        if "person_batch_job" in executors:
            executors["personbatchjob"] = executors["person_batch_job"]
        
        return executors
    
    # Original legacy executor creation
    executors = {
        "start": StartExecutor(),
        "condition": ConditionExecutor(),
        "job": JobExecutor(),
        "endpoint": EndpointExecutor(file_service),
        "user_response": UserResponseExecutor(),
    }
    
    # Add LLM-based executors if service is available
    if llm_service:
        person_job_executor = PersonJobExecutor(llm_service)
        person_batch_job_executor = PersonBatchJobExecutor(llm_service)
        
        executors.update({
            "personjob": person_job_executor,
            "person_job": person_job_executor,
            "personbatchjob": person_batch_job_executor,
            "person_batch_job": person_batch_job_executor,
        })
    
    # Add file-based executors if service is available
    if file_service:
        executors["db"] = DBExecutor(file_service)
    
    # Add Notion executor if service is available
    if notion_service:
        executors["notion"] = NotionExecutor(notion_service)
    
    return executors


__all__ = [
    "BaseExecutor",
    "ValidationResult",
    "ExecutorResult",
    "StartExecutor",
    "ConditionExecutor",
    "JobExecutor",
    "EndpointExecutor",
    "PersonJobExecutor",
    "PersonBatchJobExecutor",
    "DBExecutor",
    "UserResponseExecutor",
    "NotionExecutor",
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
    "validate_either_required",
    "validate_json_field",
    "validate_dangerous_code",
    "merge_validation_results",
]