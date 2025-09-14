"""
Strawberry GraphQL types for DiPeO nodes.
Generated automatically from node specifications.

Generated at: 2025-09-14T13:40:21.486217
"""

import strawberry
from typing import *
from strawberry.types import *
from strawberry.scalars import JSON as JSONScalar
from .strawberry_domain import TemplatePreprocessorType, ToolConfigType
from .domain_types import Vec2Type

# Import Pydantic models

from ..domain_models import *
from ..unified_nodes.api_job_node import ApiJobNode
from ..unified_nodes.code_job_node import CodeJobNode
from ..unified_nodes.condition_node import ConditionNode
from ..unified_nodes.db_node import DbNode
from ..unified_nodes.endpoint_node import EndpointNode
from ..unified_nodes.hook_node import HookNode
from ..unified_nodes.integrated_api_node import IntegratedApiNode
from ..unified_nodes.json_schema_validator_node import JsonSchemaValidatorNode
from ..unified_nodes.person_job_node import PersonJobNode
from ..unified_nodes.start_node import StartNode
from ..unified_nodes.sub_diagram_node import SubDiagramNode
from ..unified_nodes.template_job_node import TemplateJobNode
from ..unified_nodes.typescript_ast_node import TypescriptAstNode
from ..unified_nodes.user_response_node import UserResponseNode

# Import Pydantic models

from ..domain_models import *


# Import generated scalars
from dipeo.diagram_generated.graphql.scalars import *


# Generate Strawberry types for node data

@strawberry.type
class ApiJobDataType:
    """Make HTTP API requests - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    
    url: str  # API endpoint URL
    
    
    
    
    
    method: str  # HTTP method
    
    
    
    
    headers: Optional[JSONScalar] = None  # HTTP headers
    
    
    
    params: Optional[JSONScalar] = None  # Query parameters
    
    
    
    body: Optional[JSONScalar] = None  # Request body
    
    
    
    
    timeout: Optional[str] = None  # Request timeout in seconds
    
    
    
    
    
    auth_type: Optional[str] = None  # Authentication type
    
    
    
    
    auth_config: Optional[JSONScalar] = None  # Authentication configuration
    
    

    @classmethod
    def from_pydantic(cls, node: ApiJobNode) -> "ApiJobDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with Dict conversion
        field_values = {}
        
        
        field_values["url"] = getattr(node, "url", None)
        
        
        
        field_values["method"] = getattr(node, "method", None)
        
        
        
        field_values["headers"] = getattr(node, "headers", None)
        
        
        
        field_values["params"] = getattr(node, "params", None)
        
        
        
        field_values["body"] = getattr(node, "body", None)
        
        
        
        field_values["timeout"] = getattr(node, "timeout", None)
        
        
        
        field_values["auth_type"] = getattr(node, "auth_type", None)
        
        
        
        field_values["auth_config"] = getattr(node, "auth_config", None)
        
        

        return cls(
            id=node.id,
            position=Vec2Type(x=node.position.x, y=node.position.y),
            type=node.type,
            label=node.label,
            flipped=node.flipped,
            metadata=metadata,
            **field_values
        )


@strawberry.type
class CodeJobDataType:
    """Execute custom code functions - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    
    language: str  # Programming language
    
    
    
    
    
    filePath: Optional[str] = None  # Path to code file
    
    
    
    
    
    code: Optional[str] = None  # Inline code to execute (alternative to filePath)
    
    
    
    
    
    functionName: Optional[str] = None  # Function to execute
    
    
    
    
    
    timeout: Optional[str] = None  # Execution timeout in seconds
    
    
    

    @classmethod
    def from_pydantic(cls, node: CodeJobNode) -> "CodeJobDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with Dict conversion
        field_values = {}
        
        
        field_values["language"] = getattr(node, "language", None)
        
        
        
        field_values["filePath"] = getattr(node, "filePath", None)
        
        
        
        field_values["code"] = getattr(node, "code", None)
        
        
        
        field_values["functionName"] = getattr(node, "functionName", None)
        
        
        
        field_values["timeout"] = getattr(node, "timeout", None)
        
        

        return cls(
            id=node.id,
            position=Vec2Type(x=node.position.x, y=node.position.y),
            type=node.type,
            label=node.label,
            flipped=node.flipped,
            metadata=metadata,
            **field_values
        )


@strawberry.type
class ConditionDataType:
    """Conditional branching based on expressions - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    
    condition_type: Optional[str] = None  # Type of condition to evaluate
    
    
    
    
    
    expression: Optional[str] = None  # Boolean expression to evaluate
    
    
    
    
    
    node_indices: Optional[str] = None  # Node indices for detect_max_iteration condition
    
    
    
    
    
    person: Optional[str] = None  # AI agent to use for decision making
    
    
    
    
    
    judge_by: Optional[str] = None  # Prompt for LLM to make a judgment
    
    
    
    
    
    judge_by_file: Optional[str] = None  # External prompt file path
    
    
    
    
    
    memorize_to: Optional[str] = None  # Memory control strategy (e.g., GOLDFISH for fresh evaluation)
    
    
    
    
    
    at_most: Optional[str] = None  # Maximum messages to keep in memory
    
    
    
    
    
    expose_index_as: Optional[str] = None  # Variable name to expose the condition node's execution count (0-based index) to downstream nodes
    
    
    
    
    
    skippable: Optional[str] = None  # When true, downstream nodes can execute even if this condition hasn't been evaluated yet
    
    
    

    @classmethod
    def from_pydantic(cls, node: ConditionNode) -> "ConditionDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with Dict conversion
        field_values = {}
        
        
        field_values["condition_type"] = getattr(node, "condition_type", None)
        
        
        
        field_values["expression"] = getattr(node, "expression", None)
        
        
        
        field_values["node_indices"] = getattr(node, "node_indices", None)
        
        
        
        field_values["person"] = getattr(node, "person", None)
        
        
        
        field_values["judge_by"] = getattr(node, "judge_by", None)
        
        
        
        field_values["judge_by_file"] = getattr(node, "judge_by_file", None)
        
        
        
        field_values["memorize_to"] = getattr(node, "memorize_to", None)
        
        
        
        field_values["at_most"] = getattr(node, "at_most", None)
        
        
        
        field_values["expose_index_as"] = getattr(node, "expose_index_as", None)
        
        
        
        field_values["skippable"] = getattr(node, "skippable", None)
        
        

        return cls(
            id=node.id,
            position=Vec2Type(x=node.position.x, y=node.position.y),
            type=node.type,
            label=node.label,
            flipped=node.flipped,
            metadata=metadata,
            **field_values
        )


@strawberry.type
class DbDataType:
    """Database operations - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    
    file: Optional[str] = None  # File path or array of file paths
    
    
    
    
    
    collection: Optional[str] = None  # Database collection name
    
    
    
    
    
    sub_type: str  # Database operation type
    
    
    
    
    
    operation: str  # Operation configuration
    
    
    
    
    
    query: Optional[str] = None  # Query configuration
    
    
    
    
    data: Optional[JSONScalar] = None  # Data configuration
    
    
    
    
    serialize_json: Optional[str] = None  # Serialize structured data to JSON string (for backward compatibility)
    
    
    
    
    
    format: Optional[str] = None  # Data format (json, yaml, csv, text, etc.)
    
    
    

    @classmethod
    def from_pydantic(cls, node: DbNode) -> "DbDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with Dict conversion
        field_values = {}
        
        
        field_values["file"] = getattr(node, "file", None)
        
        
        
        field_values["collection"] = getattr(node, "collection", None)
        
        
        
        field_values["sub_type"] = getattr(node, "sub_type", None)
        
        
        
        field_values["operation"] = getattr(node, "operation", None)
        
        
        
        field_values["query"] = getattr(node, "query", None)
        
        
        
        field_values["data"] = getattr(node, "data", None)
        
        
        
        field_values["serialize_json"] = getattr(node, "serialize_json", None)
        
        
        
        field_values["format"] = getattr(node, "format", None)
        
        

        return cls(
            id=node.id,
            position=Vec2Type(x=node.position.x, y=node.position.y),
            type=node.type,
            label=node.label,
            flipped=node.flipped,
            metadata=metadata,
            **field_values
        )


@strawberry.type
class EndpointDataType:
    """Exit point for diagram execution - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    
    save_to_file: str  # Save results to file
    
    
    
    
    
    file_name: Optional[str] = None  # Output filename
    
    
    

    @classmethod
    def from_pydantic(cls, node: EndpointNode) -> "EndpointDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with Dict conversion
        field_values = {}
        
        
        field_values["save_to_file"] = getattr(node, "save_to_file", None)
        
        
        
        field_values["file_name"] = getattr(node, "file_name", None)
        
        

        return cls(
            id=node.id,
            position=Vec2Type(x=node.position.x, y=node.position.y),
            type=node.type,
            label=node.label,
            flipped=node.flipped,
            metadata=metadata,
            **field_values
        )


@strawberry.type
class HookDataType:
    """Executes hooks at specific points in the diagram execution - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    
    hook_type: str  # Type of hook to execute
    
    
    
    
    
    command: Optional[str] = None  # Shell command to run (for shell hooks)
    
    
    
    
    
    url: Optional[str] = None  # Webhook URL (for HTTP hooks)
    
    
    
    
    
    timeout: Optional[str] = None  # Execution timeout in seconds
    
    
    
    
    
    retry_count: Optional[str] = None  # Number of retries on failure
    
    
    

    @classmethod
    def from_pydantic(cls, node: HookNode) -> "HookDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with Dict conversion
        field_values = {}
        
        
        field_values["hook_type"] = getattr(node, "hook_type", None)
        
        
        
        field_values["command"] = getattr(node, "command", None)
        
        
        
        field_values["url"] = getattr(node, "url", None)
        
        
        
        field_values["timeout"] = getattr(node, "timeout", None)
        
        
        
        field_values["retry_count"] = getattr(node, "retry_count", None)
        
        

        return cls(
            id=node.id,
            position=Vec2Type(x=node.position.x, y=node.position.y),
            type=node.type,
            label=node.label,
            flipped=node.flipped,
            metadata=metadata,
            **field_values
        )


@strawberry.type
class IntegratedApiDataType:
    """Connect to external APIs like Notion, Slack, GitHub, and more - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    
    provider: str  # API provider to connect to
    
    
    
    
    
    operation: str  # Operation to perform (provider-specific)
    
    
    
    
    
    resource_id: Optional[str] = None  # Resource identifier (e.g., page ID, channel ID)
    
    
    
    
    config: Optional[JSONScalar] = None  # Provider-specific configuration
    
    
    
    
    timeout: Optional[str] = None  # Request timeout in seconds
    
    
    
    
    
    max_retries: Optional[str] = None  # Maximum retry attempts
    
    
    

    @classmethod
    def from_pydantic(cls, node: IntegratedApiNode) -> "IntegratedApiDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with Dict conversion
        field_values = {}
        
        
        field_values["provider"] = getattr(node, "provider", None)
        
        
        
        field_values["operation"] = getattr(node, "operation", None)
        
        
        
        field_values["resource_id"] = getattr(node, "resource_id", None)
        
        
        
        field_values["config"] = getattr(node, "config", None)
        
        
        
        field_values["timeout"] = getattr(node, "timeout", None)
        
        
        
        field_values["max_retries"] = getattr(node, "max_retries", None)
        
        

        return cls(
            id=node.id,
            position=Vec2Type(x=node.position.x, y=node.position.y),
            type=node.type,
            label=node.label,
            flipped=node.flipped,
            metadata=metadata,
            **field_values
        )


@strawberry.type
class JsonSchemaValidatorDataType:
    """Validate data against JSON schema - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    
    schema_path: Optional[str] = None  # Path to JSON schema file
    
    
    
    
    schema: Optional[JSONScalar] = None  # Inline JSON schema
    
    
    
    
    data_path: Optional[str] = None  # Data Path configuration
    
    
    
    
    
    strict_mode: Optional[str] = None  # Strict Mode configuration
    
    
    
    
    
    error_on_extra: Optional[str] = None  # Error On Extra configuration
    
    
    

    @classmethod
    def from_pydantic(cls, node: JsonSchemaValidatorNode) -> "JsonSchemaValidatorDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with Dict conversion
        field_values = {}
        
        
        field_values["schema_path"] = getattr(node, "schema_path", None)
        
        
        
        field_values["schema"] = getattr(node, "schema", None)
        
        
        
        field_values["data_path"] = getattr(node, "data_path", None)
        
        
        
        field_values["strict_mode"] = getattr(node, "strict_mode", None)
        
        
        
        field_values["error_on_extra"] = getattr(node, "error_on_extra", None)
        
        

        return cls(
            id=node.id,
            position=Vec2Type(x=node.position.x, y=node.position.y),
            type=node.type,
            label=node.label,
            flipped=node.flipped,
            metadata=metadata,
            **field_values
        )


@strawberry.type
class PersonJobDataType:
    """Execute tasks using AI language models - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    
    person: Optional[str] = None  # AI person to use
    
    
    
    
    
    first_only_prompt: str  # Prompt used only on first execution
    
    
    
    
    
    first_prompt_file: Optional[str] = None  # External prompt file for first iteration only
    
    
    
    
    
    default_prompt: Optional[str] = None  # Default prompt template
    
    
    
    
    
    prompt_file: Optional[str] = None  # Path to prompt file in /files/prompts/
    
    
    
    
    
    max_iteration: str  # Maximum execution iterations
    
    
    
    
    
    memorize_to: Optional[str] = None  # Criteria used to select helpful messages for this task. Empty = memorize all. Special: 'GOLDFISH' for goldfish mode. Comma-separated for multiple criteria.
    
    
    
    
    
    at_most: Optional[str] = None  # Select at most N messages to keep (system messages may be preserved in addition).
    
    
    
    
    
    ignore_person: Optional[str] = None  # Comma-separated list of person IDs whose messages should be excluded from memory selection.
    
    
    
    
    
    tools: Optional[str] = None  # Tools available to the AI agent
    
    
    
    
    
    text_format: Optional[str] = None  # JSON schema or response format for structured outputs
    
    
    
    
    
    text_format_file: Optional[str] = None  # Path to Python file containing Pydantic models for structured outputs
    
    
    
    
    
    resolved_prompt: Optional[str] = None  # Pre-resolved prompt content from compile-time
    
    
    
    
    
    resolved_first_prompt: Optional[str] = None  # Pre-resolved first prompt content from compile-time
    
    
    
    
    
    batch: Optional[str] = None  # Enable batch mode for processing multiple items
    
    
    
    
    
    batch_input_key: Optional[str] = None  # Key containing the array to iterate over in batch mode
    
    
    
    
    
    batch_parallel: Optional[str] = None  # Execute batch items in parallel
    
    
    
    
    
    max_concurrent: Optional[str] = None  # Maximum concurrent executions in batch mode
    
    
    

    @classmethod
    def from_pydantic(cls, node: PersonJobNode) -> "PersonJobDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with Dict conversion
        field_values = {}
        
        
        field_values["person"] = getattr(node, "person", None)
        
        
        
        field_values["first_only_prompt"] = getattr(node, "first_only_prompt", None)
        
        
        
        field_values["first_prompt_file"] = getattr(node, "first_prompt_file", None)
        
        
        
        field_values["default_prompt"] = getattr(node, "default_prompt", None)
        
        
        
        field_values["prompt_file"] = getattr(node, "prompt_file", None)
        
        
        
        field_values["max_iteration"] = getattr(node, "max_iteration", None)
        
        
        
        field_values["memorize_to"] = getattr(node, "memorize_to", None)
        
        
        
        field_values["at_most"] = getattr(node, "at_most", None)
        
        
        
        field_values["ignore_person"] = getattr(node, "ignore_person", None)
        
        
        
        field_values["tools"] = getattr(node, "tools", None)
        
        
        
        field_values["text_format"] = getattr(node, "text_format", None)
        
        
        
        field_values["text_format_file"] = getattr(node, "text_format_file", None)
        
        
        
        field_values["resolved_prompt"] = getattr(node, "resolved_prompt", None)
        
        
        
        field_values["resolved_first_prompt"] = getattr(node, "resolved_first_prompt", None)
        
        
        
        field_values["batch"] = getattr(node, "batch", None)
        
        
        
        field_values["batch_input_key"] = getattr(node, "batch_input_key", None)
        
        
        
        field_values["batch_parallel"] = getattr(node, "batch_parallel", None)
        
        
        
        field_values["max_concurrent"] = getattr(node, "max_concurrent", None)
        
        

        return cls(
            id=node.id,
            position=Vec2Type(x=node.position.x, y=node.position.y),
            type=node.type,
            label=node.label,
            flipped=node.flipped,
            metadata=metadata,
            **field_values
        )


@strawberry.type
class StartDataType:
    """Entry point for diagram execution - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    
    trigger_mode: Optional[str] = None  # How this start node is triggered
    
    
    
    
    
    custom_data: Optional[str] = None  # Custom data to pass when manually triggered
    
    
    
    
    output_data_structure: Optional[JSONScalar] = None  # Expected output data structure
    
    
    
    
    hook_event: Optional[str] = None  # Event name to listen for
    
    
    
    
    hook_filters: Optional[JSONScalar] = None  # Filters to apply to incoming events
    
    

    @classmethod
    def from_pydantic(cls, node: StartNode) -> "StartDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with Dict conversion
        field_values = {}
        
        
        field_values["trigger_mode"] = getattr(node, "trigger_mode", None)
        
        
        
        field_values["custom_data"] = getattr(node, "custom_data", None)
        
        
        
        field_values["output_data_structure"] = getattr(node, "output_data_structure", None)
        
        
        
        field_values["hook_event"] = getattr(node, "hook_event", None)
        
        
        
        field_values["hook_filters"] = getattr(node, "hook_filters", None)
        
        

        return cls(
            id=node.id,
            position=Vec2Type(x=node.position.x, y=node.position.y),
            type=node.type,
            label=node.label,
            flipped=node.flipped,
            metadata=metadata,
            **field_values
        )


@strawberry.type
class SubDiagramDataType:
    """Execute another diagram as a node within the current diagram - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    
    diagram_name: Optional[str] = None  # Name of the diagram to execute (e.g., 'workflow/process')
    
    
    
    
    diagram_data: Optional[JSONScalar] = None  # Inline diagram data (alternative to diagram_name)
    
    
    
    input_mapping: Optional[JSONScalar] = None  # Map node inputs to sub-diagram variables
    
    
    
    output_mapping: Optional[JSONScalar] = None  # Map sub-diagram outputs to node outputs
    
    
    
    
    timeout: Optional[str] = None  # Execution timeout in seconds
    
    
    
    
    
    wait_for_completion: Optional[str] = None  # Whether to wait for sub-diagram completion
    
    
    
    
    
    isolate_conversation: Optional[str] = None  # Create isolated conversation context for sub-diagram
    
    
    
    
    
    ignoreIfSub: Optional[str] = None  # Skip execution if this diagram is being run as a sub-diagram
    
    
    
    
    
    diagram_format: Optional[str] = None  # Format of the diagram file (yaml, json, or light)
    
    
    
    
    
    batch: Optional[str] = None  # Execute sub-diagram in batch mode for multiple inputs
    
    
    
    
    
    batch_input_key: Optional[str] = None  # Key in inputs containing the array of items for batch processing
    
    
    
    
    
    batch_parallel: Optional[str] = None  # Execute batch items in parallel
    
    
    

    @classmethod
    def from_pydantic(cls, node: SubDiagramNode) -> "SubDiagramDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with Dict conversion
        field_values = {}
        
        
        field_values["diagram_name"] = getattr(node, "diagram_name", None)
        
        
        
        field_values["diagram_data"] = getattr(node, "diagram_data", None)
        
        
        
        field_values["input_mapping"] = getattr(node, "input_mapping", None)
        
        
        
        field_values["output_mapping"] = getattr(node, "output_mapping", None)
        
        
        
        field_values["timeout"] = getattr(node, "timeout", None)
        
        
        
        field_values["wait_for_completion"] = getattr(node, "wait_for_completion", None)
        
        
        
        field_values["isolate_conversation"] = getattr(node, "isolate_conversation", None)
        
        
        
        field_values["ignoreIfSub"] = getattr(node, "ignoreIfSub", None)
        
        
        
        field_values["diagram_format"] = getattr(node, "diagram_format", None)
        
        
        
        field_values["batch"] = getattr(node, "batch", None)
        
        
        
        field_values["batch_input_key"] = getattr(node, "batch_input_key", None)
        
        
        
        field_values["batch_parallel"] = getattr(node, "batch_parallel", None)
        
        

        return cls(
            id=node.id,
            position=Vec2Type(x=node.position.x, y=node.position.y),
            type=node.type,
            label=node.label,
            flipped=node.flipped,
            metadata=metadata,
            **field_values
        )


@strawberry.type
class TemplateJobDataType:
    """Process templates with data - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    
    template_path: Optional[str] = None  # Path to template file
    
    
    
    
    
    template_content: Optional[str] = None  # Inline template content
    
    
    
    
    
    output_path: Optional[str] = None  # Output file path
    
    
    
    
    variables: Optional[JSONScalar] = None  # Variables configuration
    
    
    
    
    engine: Optional[str] = None  # Template engine to use
    
    
    
    
    
    preprocessor: Optional[str] = None  # Preprocessor function to apply before templating
    
    
    

    @classmethod
    def from_pydantic(cls, node: TemplateJobNode) -> "TemplateJobDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with Dict conversion
        field_values = {}
        
        
        field_values["template_path"] = getattr(node, "template_path", None)
        
        
        
        field_values["template_content"] = getattr(node, "template_content", None)
        
        
        
        field_values["output_path"] = getattr(node, "output_path", None)
        
        
        
        field_values["variables"] = getattr(node, "variables", None)
        
        
        
        field_values["engine"] = getattr(node, "engine", None)
        
        
        
        field_values["preprocessor"] = getattr(node, "preprocessor", None)
        
        

        return cls(
            id=node.id,
            position=Vec2Type(x=node.position.x, y=node.position.y),
            type=node.type,
            label=node.label,
            flipped=node.flipped,
            metadata=metadata,
            **field_values
        )


@strawberry.type
class TypescriptAstDataType:
    """Parses TypeScript source code and extracts AST, interfaces, types, and enums - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    
    source: str  # TypeScript source code to parse
    
    
    
    
    
    extractPatterns: Optional[str] = None  # Patterns to extract from the AST
    
    
    
    
    
    includeJSDoc: Optional[str] = None  # Include JSDoc comments in the extracted data
    
    
    
    
    
    parseMode: Optional[str] = None  # TypeScript parsing mode
    
    
    
    
    
    transformEnums: Optional[str] = None  # Transform enum definitions to a simpler format
    
    
    
    
    
    flattenOutput: Optional[str] = None  # Flatten the output structure for easier consumption
    
    
    
    
    
    outputFormat: Optional[str] = None  # Output format for the parsed data
    
    
    
    
    
    batch: Optional[str] = None  # Enable batch processing mode
    
    
    
    
    
    batchInputKey: Optional[str] = None  # Key to extract batch items from input
    
    
    

    @classmethod
    def from_pydantic(cls, node: TypescriptAstNode) -> "TypescriptAstDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with Dict conversion
        field_values = {}
        
        
        field_values["source"] = getattr(node, "source", None)
        
        
        
        field_values["extractPatterns"] = getattr(node, "extractPatterns", None)
        
        
        
        field_values["includeJSDoc"] = getattr(node, "includeJSDoc", None)
        
        
        
        field_values["parseMode"] = getattr(node, "parseMode", None)
        
        
        
        field_values["transformEnums"] = getattr(node, "transformEnums", None)
        
        
        
        field_values["flattenOutput"] = getattr(node, "flattenOutput", None)
        
        
        
        field_values["outputFormat"] = getattr(node, "outputFormat", None)
        
        
        
        field_values["batch"] = getattr(node, "batch", None)
        
        
        
        field_values["batchInputKey"] = getattr(node, "batchInputKey", None)
        
        

        return cls(
            id=node.id,
            position=Vec2Type(x=node.position.x, y=node.position.y),
            type=node.type,
            label=node.label,
            flipped=node.flipped,
            metadata=metadata,
            **field_values
        )


@strawberry.type
class UserResponseDataType:
    """Collect user input - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    
    prompt: str  # Question to ask the user
    
    
    
    
    
    timeout: Optional[str] = None  # Response timeout in seconds
    
    
    

    @classmethod
    def from_pydantic(cls, node: UserResponseNode) -> "UserResponseDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with Dict conversion
        field_values = {}
        
        
        field_values["prompt"] = getattr(node, "prompt", None)
        
        
        
        field_values["timeout"] = getattr(node, "timeout", None)
        
        

        return cls(
            id=node.id,
            position=Vec2Type(x=node.position.x, y=node.position.y),
            type=node.type,
            label=node.label,
            flipped=node.flipped,
            metadata=metadata,
            **field_values
        )




# Create union type for all node data types
NodeDataUnion = strawberry.union(
    "NodeDataUnion",
    (

        ApiJobDataType,

        CodeJobDataType,

        ConditionDataType,

        DbDataType,

        EndpointDataType,

        HookDataType,

        IntegratedApiDataType,

        JsonSchemaValidatorDataType,

        PersonJobDataType,

        StartDataType,

        SubDiagramDataType,

        TemplateJobDataType,

        TypescriptAstDataType,

        UserResponseDataType,

    )
)



# Export all types
__all__ = [
    'NodeDataUnion',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

    'DataType',

]