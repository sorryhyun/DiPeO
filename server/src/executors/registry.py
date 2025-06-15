"""Registry for creating and configuring the unified executor."""

from .unified_executor import UnifiedExecutor
from .types import NodeDefinition
from .schemas import (
    StartNodeProps, PersonJobProps, PersonBatchJobProps, 
    ConditionNodeProps, EndpointNodeProps, UserResponseNodeProps,
    JobNodeProps, DBNodeProps, NotionNodeProps
)
from .handlers import (
    start_handler, person_job_handler, person_batch_job_handler,
    condition_handler, endpoint_handler, user_response_handler,
    job_handler, db_handler, notion_handler
)


def create_executor() -> UnifiedExecutor:
    """Create and configure the unified executor with all node types."""
    executor = UnifiedExecutor()
    
    # Register Start node type
    executor.register(NodeDefinition(
        type="start",
        schema=StartNodeProps,
        handler=start_handler,
        description="Entry point node that provides initial data"
    ))
    
    # Register PersonJob node type
    executor.register(NodeDefinition(
        type="person_job",
        schema=PersonJobProps,
        handler=person_job_handler,
        requires_services=["llm_service"],
        description="Execute LLM task with person context and memory"
    ))
    
    # Register PersonBatchJob node type
    executor.register(NodeDefinition(
        type="person_batch_job",
        schema=PersonBatchJobProps,
        handler=person_batch_job_handler,
        requires_services=["llm_service"],
        description="Execute LLM task in batch mode"
    ))
    
    # Register Condition node type
    executor.register(NodeDefinition(
        type="condition",
        schema=ConditionNodeProps,
        handler=condition_handler,
        description="Conditional branching based on expression evaluation"
    ))
    
    # Register Endpoint node type
    executor.register(NodeDefinition(
        type="endpoint",
        schema=EndpointNodeProps,
        handler=endpoint_handler,
        requires_services=["file_service"],
        description="Terminal node for data output with optional file saving"
    ))
    
    # Register UserResponse node type
    executor.register(NodeDefinition(
        type="user_response",
        schema=UserResponseNodeProps,
        handler=user_response_handler,
        description="Interactive user input node"
    ))
    
    # Register Job node type
    executor.register(NodeDefinition(
        type="job",
        schema=JobNodeProps,
        handler=job_handler,
        description="Execute code in Python, JavaScript, or Bash"
    ))
    
    # Register DB node type
    executor.register(NodeDefinition(
        type="db",
        schema=DBNodeProps,
        handler=db_handler,
        requires_services=["file_service"],
        description="Data source node for file operations and fixed prompts"
    ))
    
    # Register Notion node type
    executor.register(NodeDefinition(
        type="notion",
        schema=NotionNodeProps,
        handler=notion_handler,
        requires_services=["notion_service"],
        description="Notion API operations including page, block, and database management"
    ))
    
    # Add middleware
    from .middleware import LoggingMiddleware, MetricsMiddleware, ErrorHandlingMiddleware
    
    executor.add_middleware(LoggingMiddleware())
    executor.add_middleware(MetricsMiddleware())
    executor.add_middleware(ErrorHandlingMiddleware())
    
    return executor