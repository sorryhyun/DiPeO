"""Registry for creating and configuring the unified executor."""

from .unified_executor import UnifiedExecutor
from .types import NodeDefinition
from .simple_nodes import SIMPLE_NODE_DEFINITIONS
from .schemas import (
    PersonJobProps, PersonBatchJobProps, 
    ConditionNodeProps, EndpointNodeProps,
    JobNodeProps, DBNodeProps, NotionNodeProps
)
from .handlers import (
    person_job_handler, person_batch_job_handler,
    condition_handler, endpoint_handler,
    job_handler, db_handler, notion_handler
)


def create_executor() -> UnifiedExecutor:
    """Create and configure the unified executor with all node types."""
    executor = UnifiedExecutor()
    
    # Register simple node types (start, user_response)
    for node_def in SIMPLE_NODE_DEFINITIONS:
        executor.register(NodeDefinition(**node_def))
    
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
    
    # Middleware removed for simplification
    
    return executor