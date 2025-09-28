"""
Strawberry GraphQL types for DiPeO nodes.
Generated automatically from node specifications.

Generated at: 2025-09-28T14:23:21.976913
"""

import strawberry
from typing import Optional, Dict, Any, List, Union, Literal
from strawberry.types import *
from strawberry.scalars import JSON as JSONScalar
from .strawberry_domain import TemplatePreprocessorType, ToolConfigType
from .domain_types import Vec2Type

# Import Pydantic models

from ..domain_models import *
from ..unified_nodes import *

# Import generated scalars
from .scalars import *


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
    
    
    
    # Enum field: HTTP method (Values: GET, POST, PUT, DELETE, PATCH)
    method: str
    
    
    
    headers: Optional[JSONScalar] = None  # HTTP headers
    
    
    
    params: Optional[JSONScalar] = None  # Query parameters
    
    
    
    body: Optional[JSONScalar] = None  # Request body
    
    
    
    timeout: Optional[int] = None  # Request timeout in seconds
    
    
    
    # Enum field: Authentication type (Values: none, bearer, basic, api_key)
    auth_type: Optional[str] = None
    
    
    
    auth_config: Optional[JSONScalar] = None  # Authentication configuration
    
    

    @classmethod
    def from_pydantic(cls, node: ApiJobNode) -> "ApiJobDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "url", None)
        
        # Direct assignment for other types
        field_values["url"] = field_value
        
        
        field_value = getattr(node, "method", None)
        
        # Direct assignment for other types
        field_values["method"] = field_value
        
        
        field_value = getattr(node, "headers", None)
        
        # Convert dict/object fields to JSONScalar
        field_values["headers"] = field_value
        
        
        field_value = getattr(node, "params", None)
        
        # Convert dict/object fields to JSONScalar
        field_values["params"] = field_value
        
        
        field_value = getattr(node, "body", None)
        
        # Convert dict/object fields to JSONScalar
        field_values["body"] = field_value
        
        
        field_value = getattr(node, "timeout", None)
        
        # Direct assignment for other types
        field_values["timeout"] = field_value
        
        
        field_value = getattr(node, "auth_type", None)
        
        # Direct assignment for other types
        field_values["auth_type"] = field_value
        
        
        field_value = getattr(node, "auth_config", None)
        
        # Convert dict/object fields to JSONScalar
        field_values["auth_config"] = field_value
        
        

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
    
    
    # Enum field: Programming language (Values: python, typescript, bash, shell)
    language: str
    
    
    
    filePath: Optional[str] = None  # Path to code file
    
    
    
    code: Optional[str] = None  # Inline code to execute (alternative to filePath)
    
    
    
    functionName: Optional[str] = None  # Function to execute
    
    
    
    timeout: Optional[int] = None  # Execution timeout in seconds
    
    

    @classmethod
    def from_pydantic(cls, node: CodeJobNode) -> "CodeJobDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "language", None)
        
        # Direct assignment for other types
        field_values["language"] = field_value
        
        
        field_value = getattr(node, "filePath", None)
        
        # Direct assignment for other types
        field_values["filePath"] = field_value
        
        
        field_value = getattr(node, "code", None)
        
        # Direct assignment for other types
        field_values["code"] = field_value
        
        
        field_value = getattr(node, "functionName", None)
        
        # Direct assignment for other types
        field_values["functionName"] = field_value
        
        
        field_value = getattr(node, "timeout", None)
        
        # Direct assignment for other types
        field_values["timeout"] = field_value
        
        

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
    
    
    # Enum field: Type of condition to evaluate (Values: detect_max_iterations, check_nodes_executed, custom, llm_decision)
    condition_type: Optional[str] = None
    
    
    
    expression: Optional[str] = None  # Boolean expression to evaluate
    
    
    
    node_indices: Optional[List[JSONScalar]] = None  # Node indices for detect_max_iteration condition
    
    
    
    person: Optional[str] = None  # AI agent to use for decision making
    
    
    
    judge_by: Optional[str] = None  # Prompt for LLM to make a judgment
    
    
    
    judge_by_file: Optional[str] = None  # External prompt file path
    
    
    
    memorize_to: Optional[str] = None  # Memory control strategy (e.g., GOLDFISH for fresh evaluation)
    
    
    
    at_most: Optional[int] = None  # Maximum messages to keep in memory
    
    
    
    expose_index_as: Optional[str] = None  # Variable name to expose the condition node's execution count (0-based index) to downstream nodes
    
    
    
    skippable: Optional[bool] = None  # When true, downstream nodes can execute even if this condition hasn't been evaluated yet
    
    

    @classmethod
    def from_pydantic(cls, node: ConditionNode) -> "ConditionDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "condition_type", None)
        
        # Direct assignment for other types
        field_values["condition_type"] = field_value
        
        
        field_value = getattr(node, "expression", None)
        
        # Direct assignment for other types
        field_values["expression"] = field_value
        
        
        field_value = getattr(node, "node_indices", None)
        
        # Direct assignment for other types
        field_values["node_indices"] = field_value
        
        
        field_value = getattr(node, "person", None)
        
        # Direct assignment for other types
        field_values["person"] = field_value
        
        
        field_value = getattr(node, "judge_by", None)
        
        # Direct assignment for other types
        field_values["judge_by"] = field_value
        
        
        field_value = getattr(node, "judge_by_file", None)
        
        # Direct assignment for other types
        field_values["judge_by_file"] = field_value
        
        
        field_value = getattr(node, "memorize_to", None)
        
        # Direct assignment for other types
        field_values["memorize_to"] = field_value
        
        
        field_value = getattr(node, "at_most", None)
        
        # Direct assignment for other types
        field_values["at_most"] = field_value
        
        
        field_value = getattr(node, "expose_index_as", None)
        
        # Direct assignment for other types
        field_values["expose_index_as"] = field_value
        
        
        field_value = getattr(node, "skippable", None)
        
        # Direct assignment for other types
        field_values["skippable"] = field_value
        
        

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
    
    
    
    # Enum field: Database operation type (Values: fixed_prompt, file, code, api_tool)
    sub_type: str
    
    
    
    # Enum field: Operation configuration (Values: prompt, read, write, append, update)
    operation: str
    
    
    
    query: Optional[str] = None  # Query configuration
    
    
    
    keys: Optional[str] = None  # Single key or list of dot-separated keys to target within the JSON payload
    
    
    
    lines: Optional[str] = None  # Line selection or ranges to read (e.g., 1:120 or ['10:20'])
    
    
    
    data: Optional[JSONScalar] = None  # Data configuration
    
    
    
    serialize_json: Optional[bool] = None  # Serialize structured data to JSON string (for backward compatibility)
    
    
    
    format: Optional[str] = None  # Data format (json, yaml, csv, text, etc.)
    
    

    @classmethod
    def from_pydantic(cls, node: DbNode) -> "DbDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "file", None)
        
        # Direct assignment for other types
        field_values["file"] = field_value
        
        
        field_value = getattr(node, "collection", None)
        
        # Direct assignment for other types
        field_values["collection"] = field_value
        
        
        field_value = getattr(node, "sub_type", None)
        
        # Direct assignment for other types
        field_values["sub_type"] = field_value
        
        
        field_value = getattr(node, "operation", None)
        
        # Direct assignment for other types
        field_values["operation"] = field_value
        
        
        field_value = getattr(node, "query", None)
        
        # Direct assignment for other types
        field_values["query"] = field_value
        
        
        field_value = getattr(node, "keys", None)
        
        # Direct assignment for other types
        field_values["keys"] = field_value
        
        
        field_value = getattr(node, "lines", None)
        
        # Direct assignment for other types
        field_values["lines"] = field_value
        
        
        field_value = getattr(node, "data", None)
        
        # Convert dict/object fields to JSONScalar
        field_values["data"] = field_value
        
        
        field_value = getattr(node, "serialize_json", None)
        
        # Direct assignment for other types
        field_values["serialize_json"] = field_value
        
        
        field_value = getattr(node, "format", None)
        
        # Direct assignment for other types
        field_values["format"] = field_value
        
        

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
class DiffPatchDataType:
    """Apply unified diffs to files with safety controls - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    target_path: str  # Path to the file to patch
    
    
    
    diff: str  # Unified diff content to apply
    
    
    
    # Enum field: Diff format type (Values: unified, git, context, ed, normal)
    format: Optional[str] = None
    
    
    
    # Enum field: How to apply the patch (Values: normal, force, dry_run, reverse)
    apply_mode: Optional[str] = None
    
    
    
    backup: Optional[bool] = None  # Create backup before patching
    
    
    
    validate_patch: Optional[bool] = None  # Validate patch before applying
    
    
    
    backup_dir: Optional[str] = None  # Directory for backup files
    
    
    
    strip_level: Optional[int] = None  # Strip N leading path components (like patch -pN)
    
    
    
    fuzz_factor: Optional[int] = None  # Number of lines that can be ignored when matching context
    
    
    
    reject_file: Optional[str] = None  # Path to save rejected hunks
    
    
    
    ignore_whitespace: Optional[bool] = None  # Ignore whitespace changes when matching
    
    
    
    create_missing: Optional[bool] = None  # Create target file if it doesn't exist
    
    

    @classmethod
    def from_pydantic(cls, node: DiffPatchNode) -> "DiffPatchDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "target_path", None)
        
        # Direct assignment for other types
        field_values["target_path"] = field_value
        
        
        field_value = getattr(node, "diff", None)
        
        # Direct assignment for other types
        field_values["diff"] = field_value
        
        
        field_value = getattr(node, "format", None)
        
        # Direct assignment for other types
        field_values["format"] = field_value
        
        
        field_value = getattr(node, "apply_mode", None)
        
        # Direct assignment for other types
        field_values["apply_mode"] = field_value
        
        
        field_value = getattr(node, "backup", None)
        
        # Direct assignment for other types
        field_values["backup"] = field_value
        
        
        field_value = getattr(node, "validate_patch", None)
        
        # Direct assignment for other types
        field_values["validate_patch"] = field_value
        
        
        field_value = getattr(node, "backup_dir", None)
        
        # Direct assignment for other types
        field_values["backup_dir"] = field_value
        
        
        field_value = getattr(node, "strip_level", None)
        
        # Direct assignment for other types
        field_values["strip_level"] = field_value
        
        
        field_value = getattr(node, "fuzz_factor", None)
        
        # Direct assignment for other types
        field_values["fuzz_factor"] = field_value
        
        
        field_value = getattr(node, "reject_file", None)
        
        # Direct assignment for other types
        field_values["reject_file"] = field_value
        
        
        field_value = getattr(node, "ignore_whitespace", None)
        
        # Direct assignment for other types
        field_values["ignore_whitespace"] = field_value
        
        
        field_value = getattr(node, "create_missing", None)
        
        # Direct assignment for other types
        field_values["create_missing"] = field_value
        
        

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
    
    
    save_to_file: Optional[bool] = None  # Save results to file
    
    
    
    file_name: Optional[str] = None  # Output filename
    
    

    @classmethod
    def from_pydantic(cls, node: EndpointNode) -> "EndpointDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "save_to_file", None)
        
        # Direct assignment for other types
        field_values["save_to_file"] = field_value
        
        
        field_value = getattr(node, "file_name", None)
        
        # Direct assignment for other types
        field_values["file_name"] = field_value
        
        

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
    
    
    # Enum field: Type of hook to execute (Values: shell, http, python, file)
    hook_type: str
    
    
    
    command: Optional[str] = None  # Shell command to run (for shell hooks)
    
    
    
    url: Optional[str] = None  # Webhook URL (for HTTP hooks)
    
    
    
    timeout: Optional[int] = None  # Execution timeout in seconds
    
    
    
    retry_count: Optional[int] = None  # Number of retries on failure
    
    

    @classmethod
    def from_pydantic(cls, node: HookNode) -> "HookDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "hook_type", None)
        
        # Direct assignment for other types
        field_values["hook_type"] = field_value
        
        
        field_value = getattr(node, "command", None)
        
        # Direct assignment for other types
        field_values["command"] = field_value
        
        
        field_value = getattr(node, "url", None)
        
        # Direct assignment for other types
        field_values["url"] = field_value
        
        
        field_value = getattr(node, "timeout", None)
        
        # Direct assignment for other types
        field_values["timeout"] = field_value
        
        
        field_value = getattr(node, "retry_count", None)
        
        # Direct assignment for other types
        field_values["retry_count"] = field_value
        
        

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
    
    
    
    timeout: Optional[int] = None  # Request timeout in seconds
    
    
    
    max_retries: Optional[int] = None  # Maximum retry attempts
    
    

    @classmethod
    def from_pydantic(cls, node: IntegratedApiNode) -> "IntegratedApiDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "provider", None)
        
        # Direct assignment for other types
        field_values["provider"] = field_value
        
        
        field_value = getattr(node, "operation", None)
        
        # Direct assignment for other types
        field_values["operation"] = field_value
        
        
        field_value = getattr(node, "resource_id", None)
        
        # Direct assignment for other types
        field_values["resource_id"] = field_value
        
        
        field_value = getattr(node, "config", None)
        
        # Convert dict/object fields to JSONScalar
        field_values["config"] = field_value
        
        
        field_value = getattr(node, "timeout", None)
        
        # Direct assignment for other types
        field_values["timeout"] = field_value
        
        
        field_value = getattr(node, "max_retries", None)
        
        # Direct assignment for other types
        field_values["max_retries"] = field_value
        
        

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
class IrBuilderDataType:
    """Build Intermediate Representation for code generation - Data fields only"""
    # Base fields (all nodes have these)
    id: NodeIDScalar
    position: Vec2Type
    type: strawberry.Private[NodeType]  # Not exposed in GraphQL
    label: Optional[str] = None
    flipped: Optional[bool] = False
    metadata: Optional[JSONScalar] = None  # Use JSONScalar for Dict fields

    # Node-specific fields from specification
    
    
    # Enum field: Type of IR builder to use (Values: backend, frontend, strawberry, custom)
    builder_type: str
    
    
    
    # Enum field: Type of source data (Values: ast, schema, config, auto)
    source_type: Optional[str] = None
    
    
    
    config_path: Optional[str] = None  # Path to configuration directory
    
    
    
    # Enum field: Output format for IR (Values: json, yaml, python)
    output_format: Optional[str] = None
    
    
    
    cache_enabled: Optional[bool] = None  # Enable IR caching
    
    
    
    validate_output: Optional[bool] = None  # Validate IR structure before output
    
    

    @classmethod
    def from_pydantic(cls, node: IrBuilderNode) -> "IrBuilderDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "builder_type", None)
        
        # Direct assignment for other types
        field_values["builder_type"] = field_value
        
        
        field_value = getattr(node, "source_type", None)
        
        # Direct assignment for other types
        field_values["source_type"] = field_value
        
        
        field_value = getattr(node, "config_path", None)
        
        # Direct assignment for other types
        field_values["config_path"] = field_value
        
        
        field_value = getattr(node, "output_format", None)
        
        # Direct assignment for other types
        field_values["output_format"] = field_value
        
        
        field_value = getattr(node, "cache_enabled", None)
        
        # Direct assignment for other types
        field_values["cache_enabled"] = field_value
        
        
        field_value = getattr(node, "validate_output", None)
        
        # Direct assignment for other types
        field_values["validate_output"] = field_value
        
        

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
    
    
    
    json_schema: Optional[JSONScalar] = None  # Inline JSON schema
    
    
    
    data_path: Optional[str] = None  # Data Path configuration
    
    
    
    strict_mode: Optional[bool] = None  # Strict Mode configuration
    
    
    
    error_on_extra: Optional[bool] = None  # Error On Extra configuration
    
    

    @classmethod
    def from_pydantic(cls, node: JsonSchemaValidatorNode) -> "JsonSchemaValidatorDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "schema_path", None)
        
        # Direct assignment for other types
        field_values["schema_path"] = field_value
        
        
        field_value = getattr(node, "json_schema", None)
        
        # Convert dict/object fields to JSONScalar
        field_values["json_schema"] = field_value
        
        
        field_value = getattr(node, "data_path", None)
        
        # Direct assignment for other types
        field_values["data_path"] = field_value
        
        
        field_value = getattr(node, "strict_mode", None)
        
        # Direct assignment for other types
        field_values["strict_mode"] = field_value
        
        
        field_value = getattr(node, "error_on_extra", None)
        
        # Direct assignment for other types
        field_values["error_on_extra"] = field_value
        
        

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
    
    
    
    first_only_prompt: Optional[str] = None  # Prompt used only on first execution
    
    
    
    first_prompt_file: Optional[str] = None  # External prompt file for first iteration only
    
    
    
    default_prompt: Optional[str] = None  # Default prompt template
    
    
    
    prompt_file: Optional[str] = None  # Path to prompt file in /files/prompts/
    
    
    
    max_iteration: int  # Maximum execution iterations
    
    
    
    memorize_to: Optional[str] = None  # Criteria used to select helpful messages for this task. Empty = memorize all. Special: 'GOLDFISH' for goldfish mode. Comma-separated for multiple criteria.
    
    
    
    at_most: Optional[int] = None  # Select at most N messages to keep (system messages may be preserved in addition).
    
    
    
    ignore_person: Optional[str] = None  # Comma-separated list of person IDs whose messages should be excluded from memory selection.
    
    
    
    tools: Optional[str] = None  # Tools available to the AI agent
    
    
    
    text_format: Optional[str] = None  # JSON schema or response format for structured outputs
    
    
    
    text_format_file: Optional[str] = None  # Path to Python file containing Pydantic models for structured outputs
    
    
    
    resolved_prompt: Optional[str] = None  # Pre-resolved prompt content from compile-time
    
    
    
    resolved_first_prompt: Optional[str] = None  # Pre-resolved first prompt content from compile-time
    
    
    
    batch: Optional[bool] = None  # Enable batch mode for processing multiple items
    
    
    
    batch_input_key: Optional[str] = None  # Key containing the array to iterate over in batch mode
    
    
    
    batch_parallel: Optional[bool] = None  # Execute batch items in parallel
    
    
    
    max_concurrent: Optional[int] = None  # Maximum concurrent executions in batch mode
    
    

    @classmethod
    def from_pydantic(cls, node: PersonJobNode) -> "PersonJobDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "person", None)
        
        # Direct assignment for other types
        field_values["person"] = field_value
        
        
        field_value = getattr(node, "first_only_prompt", None)
        
        # Direct assignment for other types
        field_values["first_only_prompt"] = field_value
        
        
        field_value = getattr(node, "first_prompt_file", None)
        
        # Direct assignment for other types
        field_values["first_prompt_file"] = field_value
        
        
        field_value = getattr(node, "default_prompt", None)
        
        # Direct assignment for other types
        field_values["default_prompt"] = field_value
        
        
        field_value = getattr(node, "prompt_file", None)
        
        # Direct assignment for other types
        field_values["prompt_file"] = field_value
        
        
        field_value = getattr(node, "max_iteration", None)
        
        # Direct assignment for other types
        field_values["max_iteration"] = field_value
        
        
        field_value = getattr(node, "memorize_to", None)
        
        # Direct assignment for other types
        field_values["memorize_to"] = field_value
        
        
        field_value = getattr(node, "at_most", None)
        
        # Direct assignment for other types
        field_values["at_most"] = field_value
        
        
        field_value = getattr(node, "ignore_person", None)
        
        # Direct assignment for other types
        field_values["ignore_person"] = field_value
        
        
        field_value = getattr(node, "tools", None)
        
        # Direct assignment for other types
        field_values["tools"] = field_value
        
        
        field_value = getattr(node, "text_format", None)
        
        # Direct assignment for other types
        field_values["text_format"] = field_value
        
        
        field_value = getattr(node, "text_format_file", None)
        
        # Direct assignment for other types
        field_values["text_format_file"] = field_value
        
        
        field_value = getattr(node, "resolved_prompt", None)
        
        # Direct assignment for other types
        field_values["resolved_prompt"] = field_value
        
        
        field_value = getattr(node, "resolved_first_prompt", None)
        
        # Direct assignment for other types
        field_values["resolved_first_prompt"] = field_value
        
        
        field_value = getattr(node, "batch", None)
        
        # Direct assignment for other types
        field_values["batch"] = field_value
        
        
        field_value = getattr(node, "batch_input_key", None)
        
        # Direct assignment for other types
        field_values["batch_input_key"] = field_value
        
        
        field_value = getattr(node, "batch_parallel", None)
        
        # Direct assignment for other types
        field_values["batch_parallel"] = field_value
        
        
        field_value = getattr(node, "max_concurrent", None)
        
        # Direct assignment for other types
        field_values["max_concurrent"] = field_value
        
        

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
    
    
    # Enum field: How this start node is triggered (Values: none, manual, hook)
    trigger_mode: Optional[str] = None
    
    
    
    custom_data: Optional[str] = None  # Custom data to pass when manually triggered
    
    
    
    output_data_structure: Optional[JSONScalar] = None  # Expected output data structure
    
    
    
    hook_event: Optional[str] = None  # Event name to listen for
    
    
    
    hook_filters: Optional[JSONScalar] = None  # Filters to apply to incoming events
    
    

    @classmethod
    def from_pydantic(cls, node: StartNode) -> "StartDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "trigger_mode", None)
        
        # Direct assignment for other types
        field_values["trigger_mode"] = field_value
        
        
        field_value = getattr(node, "custom_data", None)
        
        # Direct assignment for other types
        field_values["custom_data"] = field_value
        
        
        field_value = getattr(node, "output_data_structure", None)
        
        # Convert dict/object fields to JSONScalar
        field_values["output_data_structure"] = field_value
        
        
        field_value = getattr(node, "hook_event", None)
        
        # Direct assignment for other types
        field_values["hook_event"] = field_value
        
        
        field_value = getattr(node, "hook_filters", None)
        
        # Convert dict/object fields to JSONScalar
        field_values["hook_filters"] = field_value
        
        

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
    
    
    
    timeout: Optional[int] = None  # Execution timeout in seconds
    
    
    
    wait_for_completion: Optional[bool] = None  # Whether to wait for sub-diagram completion
    
    
    
    isolate_conversation: Optional[bool] = None  # Create isolated conversation context for sub-diagram
    
    
    
    ignoreIfSub: Optional[bool] = None  # Skip execution if this diagram is being run as a sub-diagram
    
    
    
    # Enum field: Format of the diagram file (yaml, json, or light) (Values: yaml, json, light)
    diagram_format: Optional[str] = None
    
    
    
    batch: Optional[bool] = None  # Execute sub-diagram in batch mode for multiple inputs
    
    
    
    batch_input_key: Optional[str] = None  # Key in inputs containing the array of items for batch processing
    
    
    
    batch_parallel: Optional[bool] = None  # Execute batch items in parallel
    
    

    @classmethod
    def from_pydantic(cls, node: SubDiagramNode) -> "SubDiagramDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "diagram_name", None)
        
        # Direct assignment for other types
        field_values["diagram_name"] = field_value
        
        
        field_value = getattr(node, "diagram_data", None)
        
        # Convert dict/object fields to JSONScalar
        field_values["diagram_data"] = field_value
        
        
        field_value = getattr(node, "input_mapping", None)
        
        # Convert dict/object fields to JSONScalar
        field_values["input_mapping"] = field_value
        
        
        field_value = getattr(node, "output_mapping", None)
        
        # Convert dict/object fields to JSONScalar
        field_values["output_mapping"] = field_value
        
        
        field_value = getattr(node, "timeout", None)
        
        # Direct assignment for other types
        field_values["timeout"] = field_value
        
        
        field_value = getattr(node, "wait_for_completion", None)
        
        # Direct assignment for other types
        field_values["wait_for_completion"] = field_value
        
        
        field_value = getattr(node, "isolate_conversation", None)
        
        # Direct assignment for other types
        field_values["isolate_conversation"] = field_value
        
        
        field_value = getattr(node, "ignoreIfSub", None)
        
        # Direct assignment for other types
        field_values["ignoreIfSub"] = field_value
        
        
        field_value = getattr(node, "diagram_format", None)
        
        # Direct assignment for other types
        field_values["diagram_format"] = field_value
        
        
        field_value = getattr(node, "batch", None)
        
        # Direct assignment for other types
        field_values["batch"] = field_value
        
        
        field_value = getattr(node, "batch_input_key", None)
        
        # Direct assignment for other types
        field_values["batch_input_key"] = field_value
        
        
        field_value = getattr(node, "batch_parallel", None)
        
        # Direct assignment for other types
        field_values["batch_parallel"] = field_value
        
        

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
    
    
    
    # Enum field: Template engine to use (Values: internal, jinja2)
    engine: Optional[str] = None
    
    
    
    preprocessor: Optional[str] = None  # Preprocessor function to apply before templating
    
    

    @classmethod
    def from_pydantic(cls, node: TemplateJobNode) -> "TemplateJobDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "template_path", None)
        
        # Direct assignment for other types
        field_values["template_path"] = field_value
        
        
        field_value = getattr(node, "template_content", None)
        
        # Direct assignment for other types
        field_values["template_content"] = field_value
        
        
        field_value = getattr(node, "output_path", None)
        
        # Direct assignment for other types
        field_values["output_path"] = field_value
        
        
        field_value = getattr(node, "variables", None)
        
        # Convert dict/object fields to JSONScalar
        field_values["variables"] = field_value
        
        
        field_value = getattr(node, "engine", None)
        
        # Direct assignment for other types
        field_values["engine"] = field_value
        
        
        field_value = getattr(node, "preprocessor", None)
        
        # Direct assignment for other types
        field_values["preprocessor"] = field_value
        
        

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
    
    
    source: Optional[str] = None  # TypeScript source code to parse
    
    
    
    # Enum field: Patterns to extract from the AST (Values: interface, type, enum, class, function, const, export)
    extractPatterns: Optional[str] = None
    
    
    
    includeJSDoc: Optional[bool] = None  # Include JSDoc comments in the extracted data
    
    
    
    # Enum field: TypeScript parsing mode (Values: module, script)
    parseMode: Optional[str] = None
    
    
    
    transformEnums: Optional[bool] = None  # Transform enum definitions to a simpler format
    
    
    
    flattenOutput: Optional[bool] = None  # Flatten the output structure for easier consumption
    
    
    
    # Enum field: Output format for the parsed data (Values: standard, for_codegen, for_analysis)
    outputFormat: Optional[str] = None
    
    
    
    batch: Optional[bool] = None  # Enable batch processing mode
    
    
    
    batchInputKey: Optional[str] = None  # Key to extract batch items from input
    
    

    @classmethod
    def from_pydantic(cls, node: TypescriptAstNode) -> "TypescriptAstDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "source", None)
        
        # Direct assignment for other types
        field_values["source"] = field_value
        
        
        field_value = getattr(node, "extractPatterns", None)
        
        # Direct assignment for other types
        field_values["extractPatterns"] = field_value
        
        
        field_value = getattr(node, "includeJSDoc", None)
        
        # Direct assignment for other types
        field_values["includeJSDoc"] = field_value
        
        
        field_value = getattr(node, "parseMode", None)
        
        # Direct assignment for other types
        field_values["parseMode"] = field_value
        
        
        field_value = getattr(node, "transformEnums", None)
        
        # Direct assignment for other types
        field_values["transformEnums"] = field_value
        
        
        field_value = getattr(node, "flattenOutput", None)
        
        # Direct assignment for other types
        field_values["flattenOutput"] = field_value
        
        
        field_value = getattr(node, "outputFormat", None)
        
        # Direct assignment for other types
        field_values["outputFormat"] = field_value
        
        
        field_value = getattr(node, "batch", None)
        
        # Direct assignment for other types
        field_values["batch"] = field_value
        
        
        field_value = getattr(node, "batchInputKey", None)
        
        # Direct assignment for other types
        field_values["batchInputKey"] = field_value
        
        

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
    
    
    
    timeout: Optional[int] = None  # Response timeout in seconds
    
    

    @classmethod
    def from_pydantic(cls, node: UserResponseNode) -> "UserResponseDataType":
        """Convert from Pydantic model to Strawberry type."""
        # Convert Dict fields to JSONScalar
        metadata = node.metadata if node.metadata else None

        # Get node-specific fields with type conversion
        field_values = {}
        
        field_value = getattr(node, "prompt", None)
        
        # Direct assignment for other types
        field_values["prompt"] = field_value
        
        
        field_value = getattr(node, "timeout", None)
        
        # Direct assignment for other types
        field_values["timeout"] = field_value
        
        

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

        DiffPatchDataType,

        EndpointDataType,

        HookDataType,

        IntegratedApiDataType,

        IrBuilderDataType,

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

    'ApiJobDataType',

    'CodeJobDataType',

    'ConditionDataType',

    'DbDataType',

    'DiffPatchDataType',

    'EndpointDataType',

    'HookDataType',

    'IntegratedApiDataType',

    'IrBuilderDataType',

    'JsonSchemaValidatorDataType',

    'PersonJobDataType',

    'StartDataType',

    'SubDiagramDataType',

    'TemplateJobDataType',

    'TypescriptAstDataType',

    'UserResponseDataType',

]
