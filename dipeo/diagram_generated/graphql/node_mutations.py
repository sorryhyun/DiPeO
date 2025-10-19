"""
Strawberry GraphQL mutations for DiPeO nodes.
Generated automatically from node specifications.

Generated at: 2025-10-19T16:24:20.683828
"""

import strawberry
from typing import *
from strawberry.types import *

# Import data types and unions
from .strawberry_nodes import *

# Import base types
from dipeo.diagram_generated.graphql.domain_types import *
from dipeo.diagram_generated.graphql.inputs import *
from .enums import DiagramFormatGraphQL
from strawberry.file_uploads import Upload

# Import services and keys
from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import (
    DIAGRAM_PORT,
    EXECUTION_SERVICE,
    PERSON_REPOSITORY,
    CONVERSATION_REPOSITORY,
    API_KEY_SERVICE,
    ServiceKey
)


# Generate input types for each node if node_specs exist


@strawberry.input
class CreateApiJobInput:
    """Input for creating a API Job node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    url: str  # API endpoint URL
    
    
    
    # Enum field: HTTP method
    method: str  # Values: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
    
    
    
    headers: Optional[strawberry.scalars.JSON] = None  # HTTP headers
    
    
    
    params: Optional[strawberry.scalars.JSON] = None  # Query parameters
    
    
    
    body: Optional[strawberry.scalars.JSON] = None  # Request body
    
    
    
    timeout: Optional[int] = None  # Request timeout in seconds
    
    
    
    # Enum field: Authentication type
    auth_type: Optional[str] = None  # Values: ['none', 'bearer', 'basic', 'api_key']
    
    
    
    auth_config: Optional[strawberry.scalars.JSON] = None  # Authentication configuration
    
    

@strawberry.input
class UpdateApiJobInput:
    """Input for updating a API Job node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    url: Optional[str] = None  # API endpoint URL
    
    
    
    # Enum field: HTTP method
    method: Optional[str] = None  # Values: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
    
    
    
    headers: Optional[strawberry.scalars.JSON] = None  # HTTP headers
    
    
    
    params: Optional[strawberry.scalars.JSON] = None  # Query parameters
    
    
    
    body: Optional[strawberry.scalars.JSON] = None  # Request body
    
    
    
    timeout: Optional[int] = None  # Request timeout in seconds
    
    
    
    # Enum field: Authentication type
    auth_type: Optional[str] = None  # Values: ['none', 'bearer', 'basic', 'api_key']
    
    
    
    auth_config: Optional[strawberry.scalars.JSON] = None  # Authentication configuration
    
    


@strawberry.input
class CreateCodeJobInput:
    """Input for creating a Code Job node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    # Enum field: Programming language
    language: str  # Values: ['python', 'typescript', 'bash', 'shell']
    
    
    
    file_path: Optional[str] = None  # Path to code file
    
    
    
    code: Optional[str] = None  # Inline code to execute (alternative to file_path)
    
    
    
    function_name: Optional[str] = None  # Function to execute
    
    
    
    timeout: Optional[int] = None  # Operation timeout in seconds
    
    

@strawberry.input
class UpdateCodeJobInput:
    """Input for updating a Code Job node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    # Enum field: Programming language
    language: Optional[str] = None  # Values: ['python', 'typescript', 'bash', 'shell']
    
    
    
    file_path: Optional[str] = None  # Path to code file
    
    
    
    code: Optional[str] = None  # Inline code to execute (alternative to file_path)
    
    
    
    function_name: Optional[str] = None  # Function to execute
    
    
    
    timeout: Optional[int] = None  # Operation timeout in seconds
    
    


@strawberry.input
class CreateConditionInput:
    """Input for creating a Condition node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    # Enum field: Type of condition to evaluate
    condition_type: Optional[str] = None  # Values: ['detect_max_iterations', 'check_nodes_executed', 'custom', 'llm_decision']
    
    
    
    expression: Optional[str] = None  # Boolean expression to evaluate
    
    
    
    node_indices: Optional[str] = None  # Node indices for detect_max_iteration condition
    
    
    
    person: Optional[str] = None  # AI agent to use for decision making
    
    
    
    judge_by: Optional[str] = None  # Prompt for LLM to make a judgment
    
    
    
    judge_by_file: Optional[str] = None  # External prompt file path
    
    
    
    memorize_to: Optional[str] = None  # Memory control strategy (e.g., GOLDFISH for fresh evaluation)
    
    
    
    at_most: Optional[int] = None  # Maximum messages to keep in memory
    
    
    
    expose_index_as: Optional[str] = None  # Variable name to expose the condition node's execution count (0-based index) to downstream nodes
    
    
    
    skippable: Optional[bool] = None  # When true, downstream nodes can execute even if this condition hasn't been evaluated yet
    
    

@strawberry.input
class UpdateConditionInput:
    """Input for updating a Condition node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    # Enum field: Type of condition to evaluate
    condition_type: Optional[str] = None  # Values: ['detect_max_iterations', 'check_nodes_executed', 'custom', 'llm_decision']
    
    
    
    expression: Optional[str] = None  # Boolean expression to evaluate
    
    
    
    node_indices: Optional[str] = None  # Node indices for detect_max_iteration condition
    
    
    
    person: Optional[str] = None  # AI agent to use for decision making
    
    
    
    judge_by: Optional[str] = None  # Prompt for LLM to make a judgment
    
    
    
    judge_by_file: Optional[str] = None  # External prompt file path
    
    
    
    memorize_to: Optional[str] = None  # Memory control strategy (e.g., GOLDFISH for fresh evaluation)
    
    
    
    at_most: Optional[int] = None  # Maximum messages to keep in memory
    
    
    
    expose_index_as: Optional[str] = None  # Variable name to expose the condition node's execution count (0-based index) to downstream nodes
    
    
    
    skippable: Optional[bool] = None  # When true, downstream nodes can execute even if this condition hasn't been evaluated yet
    
    


@strawberry.input
class CreateDbInput:
    """Input for creating a Database node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    file: Optional[str] = None  # File path or array of file paths
    
    
    
    collection: Optional[str] = None  # Database collection name
    
    
    
    # Enum field: Database operation type
    sub_type: str  # Values: ['fixed_prompt', 'file', 'code', 'api_tool']
    
    
    
    # Enum field: Operation configuration
    operation: str  # Values: ['prompt', 'read', 'write', 'append', 'update']
    
    
    
    query: Optional[str] = None  # Query configuration
    
    
    
    keys: Optional[str] = None  # Single key or list of dot-separated keys to target within the JSON payload
    
    
    
    lines: Optional[str] = None  # Line selection or ranges to read (e.g., 1:120 or ['10:20'])
    
    
    
    data: Optional[strawberry.scalars.JSON] = None  # Data configuration
    
    
    
    serialize_json: Optional[bool] = None  # Serialize structured data to JSON string (for backward compatibility)
    
    
    
    # Enum field: Data format (json, yaml, csv, text, etc.)
    format: Optional[str] = None  # Values: ['json', 'yaml', 'csv', 'text', 'xml']
    
    

@strawberry.input
class UpdateDbInput:
    """Input for updating a Database node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    file: Optional[str] = None  # File path or array of file paths
    
    
    
    collection: Optional[str] = None  # Database collection name
    
    
    
    # Enum field: Database operation type
    sub_type: Optional[str] = None  # Values: ['fixed_prompt', 'file', 'code', 'api_tool']
    
    
    
    # Enum field: Operation configuration
    operation: Optional[str] = None  # Values: ['prompt', 'read', 'write', 'append', 'update']
    
    
    
    query: Optional[str] = None  # Query configuration
    
    
    
    keys: Optional[str] = None  # Single key or list of dot-separated keys to target within the JSON payload
    
    
    
    lines: Optional[str] = None  # Line selection or ranges to read (e.g., 1:120 or ['10:20'])
    
    
    
    data: Optional[strawberry.scalars.JSON] = None  # Data configuration
    
    
    
    serialize_json: Optional[bool] = None  # Serialize structured data to JSON string (for backward compatibility)
    
    
    
    # Enum field: Data format (json, yaml, csv, text, etc.)
    format: Optional[str] = None  # Values: ['json', 'yaml', 'csv', 'text', 'xml']
    
    


@strawberry.input
class CreateDiffPatchInput:
    """Input for creating a Diff/Patch node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    target_path: str  # Path to the file to patch
    
    
    
    diff: str  # Unified diff content to apply
    
    
    
    # Enum field: Diff format type
    format: Optional[str] = None  # Values: ['unified', 'git', 'context', 'ed', 'normal']
    
    
    
    # Enum field: How to apply the patch
    apply_mode: Optional[str] = None  # Values: ['normal', 'force', 'dry_run', 'reverse']
    
    
    
    backup: Optional[bool] = None  # Create backup before patching
    
    
    
    validate_patch: Optional[bool] = None  # Validate patch before applying
    
    
    
    backup_dir: Optional[str] = None  # Directory for backup files
    
    
    
    strip_level: Optional[int] = None  # Strip N leading path components (like patch -pN)
    
    
    
    fuzz_factor: Optional[int] = None  # Number of lines that can be ignored when matching context
    
    
    
    reject_file: Optional[str] = None  # Path to save rejected hunks
    
    
    
    ignore_whitespace: Optional[bool] = None  # Ignore whitespace changes when matching
    
    
    
    create_missing: Optional[bool] = None  # Create target file if it doesn't exist
    
    

@strawberry.input
class UpdateDiffPatchInput:
    """Input for updating a Diff/Patch node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    target_path: Optional[str] = None  # Path to the file to patch
    
    
    
    diff: Optional[str] = None  # Unified diff content to apply
    
    
    
    # Enum field: Diff format type
    format: Optional[str] = None  # Values: ['unified', 'git', 'context', 'ed', 'normal']
    
    
    
    # Enum field: How to apply the patch
    apply_mode: Optional[str] = None  # Values: ['normal', 'force', 'dry_run', 'reverse']
    
    
    
    backup: Optional[bool] = None  # Create backup before patching
    
    
    
    validate_patch: Optional[bool] = None  # Validate patch before applying
    
    
    
    backup_dir: Optional[str] = None  # Directory for backup files
    
    
    
    strip_level: Optional[int] = None  # Strip N leading path components (like patch -pN)
    
    
    
    fuzz_factor: Optional[int] = None  # Number of lines that can be ignored when matching context
    
    
    
    reject_file: Optional[str] = None  # Path to save rejected hunks
    
    
    
    ignore_whitespace: Optional[bool] = None  # Ignore whitespace changes when matching
    
    
    
    create_missing: Optional[bool] = None  # Create target file if it doesn't exist
    
    


@strawberry.input
class CreateEndpointInput:
    """Input for creating a End Node node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    save_to_file: Optional[bool] = None  # Save results to file
    
    
    
    file_name: Optional[str] = None  # Output filename
    
    

@strawberry.input
class UpdateEndpointInput:
    """Input for updating a End Node node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    save_to_file: Optional[bool] = None  # Save results to file
    
    
    
    file_name: Optional[str] = None  # Output filename
    
    


@strawberry.input
class CreateHookInput:
    """Input for creating a Hook node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    # Enum field: Type of hook to execute
    hook_type: str  # Values: ['shell', 'http', 'python', 'file']
    
    
    
    command: Optional[str] = None  # Shell command to run (for shell hooks)
    
    
    
    url: Optional[str] = None  # Webhook URL (for HTTP hooks)
    
    
    
    timeout: Optional[int] = None  # Execution timeout in seconds
    
    
    
    retry_count: Optional[int] = None  # Number of retries on failure
    
    

@strawberry.input
class UpdateHookInput:
    """Input for updating a Hook node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    # Enum field: Type of hook to execute
    hook_type: Optional[str] = None  # Values: ['shell', 'http', 'python', 'file']
    
    
    
    command: Optional[str] = None  # Shell command to run (for shell hooks)
    
    
    
    url: Optional[str] = None  # Webhook URL (for HTTP hooks)
    
    
    
    timeout: Optional[int] = None  # Execution timeout in seconds
    
    
    
    retry_count: Optional[int] = None  # Number of retries on failure
    
    


@strawberry.input
class CreateIntegratedApiInput:
    """Input for creating a Integrated API node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    provider: str  # API provider to connect to
    
    
    
    operation: str  # Operation to perform (provider-specific)
    
    
    
    resource_id: Optional[str] = None  # Resource identifier (e.g., page ID, channel ID)
    
    
    
    config: Optional[strawberry.scalars.JSON] = None  # Provider-specific configuration
    
    
    
    timeout: Optional[int] = None  # Request timeout in seconds
    
    
    
    max_retries: Optional[int] = None  # Maximum retry attempts
    
    

@strawberry.input
class UpdateIntegratedApiInput:
    """Input for updating a Integrated API node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    provider: Optional[str] = None  # API provider to connect to
    
    
    
    operation: Optional[str] = None  # Operation to perform (provider-specific)
    
    
    
    resource_id: Optional[str] = None  # Resource identifier (e.g., page ID, channel ID)
    
    
    
    config: Optional[strawberry.scalars.JSON] = None  # Provider-specific configuration
    
    
    
    timeout: Optional[int] = None  # Request timeout in seconds
    
    
    
    max_retries: Optional[int] = None  # Maximum retry attempts
    
    


@strawberry.input
class CreateIrBuilderInput:
    """Input for creating a IR Builder node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    # Enum field: Type of IR builder to use
    builder_type: str  # Values: ['backend', 'frontend', 'strawberry', 'custom']
    
    
    
    # Enum field: Type of source data
    source_type: Optional[str] = None  # Values: ['ast', 'schema', 'config', 'auto']
    
    
    
    config_path: Optional[str] = None  # Path to configuration directory
    
    
    
    # Enum field: Output format for IR
    output_format: Optional[str] = None  # Values: ['json', 'yaml', 'python']
    
    
    
    cache_enabled: Optional[bool] = None  # Enable IR caching
    
    
    
    validate_output: Optional[bool] = None  # Validate IR structure before output
    
    

@strawberry.input
class UpdateIrBuilderInput:
    """Input for updating a IR Builder node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    # Enum field: Type of IR builder to use
    builder_type: Optional[str] = None  # Values: ['backend', 'frontend', 'strawberry', 'custom']
    
    
    
    # Enum field: Type of source data
    source_type: Optional[str] = None  # Values: ['ast', 'schema', 'config', 'auto']
    
    
    
    config_path: Optional[str] = None  # Path to configuration directory
    
    
    
    # Enum field: Output format for IR
    output_format: Optional[str] = None  # Values: ['json', 'yaml', 'python']
    
    
    
    cache_enabled: Optional[bool] = None  # Enable IR caching
    
    
    
    validate_output: Optional[bool] = None  # Validate IR structure before output
    
    


@strawberry.input
class CreateJsonSchemaValidatorInput:
    """Input for creating a JSON Schema Validator node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    schema_path: Optional[str] = None  # Path to JSON schema file
    
    
    
    json_schema: Optional[strawberry.scalars.JSON] = None  # Inline JSON schema
    
    
    
    data_path: Optional[str] = None  # Data Path configuration
    
    
    
    strict_mode: Optional[bool] = None  # Strict Mode configuration
    
    
    
    error_on_extra: Optional[bool] = None  # Error On Extra configuration
    
    

@strawberry.input
class UpdateJsonSchemaValidatorInput:
    """Input for updating a JSON Schema Validator node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    schema_path: Optional[str] = None  # Path to JSON schema file
    
    
    
    json_schema: Optional[strawberry.scalars.JSON] = None  # Inline JSON schema
    
    
    
    data_path: Optional[str] = None  # Data Path configuration
    
    
    
    strict_mode: Optional[bool] = None  # Strict Mode configuration
    
    
    
    error_on_extra: Optional[bool] = None  # Error On Extra configuration
    
    


@strawberry.input
class CreatePersonJobInput:
    """Input for creating a Person Job node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    person: Optional[str] = None  # AI person to use for this task
    
    
    
    first_only_prompt: Optional[str] = None  # Prompt used only on first execution
    
    
    
    first_prompt_file: Optional[str] = None  # Path to prompt file in /files/prompts/
    
    
    
    default_prompt: Optional[str] = None  # Prompt template
    
    
    
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
    
    

@strawberry.input
class UpdatePersonJobInput:
    """Input for updating a Person Job node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    person: Optional[str] = None  # AI person to use for this task
    
    
    
    first_only_prompt: Optional[str] = None  # Prompt used only on first execution
    
    
    
    first_prompt_file: Optional[str] = None  # Path to prompt file in /files/prompts/
    
    
    
    default_prompt: Optional[str] = None  # Prompt template
    
    
    
    prompt_file: Optional[str] = None  # Path to prompt file in /files/prompts/
    
    
    
    max_iteration: Optional[int] = None  # Maximum execution iterations
    
    
    
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
    
    


@strawberry.input
class CreateStartInput:
    """Input for creating a Start Node node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    # Enum field: How this start node is triggered
    trigger_mode: Optional[str] = None  # Values: ['none', 'manual', 'hook']
    
    
    
    custom_data: Optional[str] = None  # Custom data to pass when manually triggered
    
    
    
    output_data_structure: Optional[strawberry.scalars.JSON] = None  # Expected output data structure
    
    
    
    hook_event: Optional[str] = None  # Event name to listen for
    
    
    
    hook_filters: Optional[strawberry.scalars.JSON] = None  # Filters to apply to incoming events
    
    

@strawberry.input
class UpdateStartInput:
    """Input for updating a Start Node node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    # Enum field: How this start node is triggered
    trigger_mode: Optional[str] = None  # Values: ['none', 'manual', 'hook']
    
    
    
    custom_data: Optional[str] = None  # Custom data to pass when manually triggered
    
    
    
    output_data_structure: Optional[strawberry.scalars.JSON] = None  # Expected output data structure
    
    
    
    hook_event: Optional[str] = None  # Event name to listen for
    
    
    
    hook_filters: Optional[strawberry.scalars.JSON] = None  # Filters to apply to incoming events
    
    


@strawberry.input
class CreateSubDiagramInput:
    """Input for creating a Sub-Diagram node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    diagram_name: Optional[str] = None  # Name of the diagram to execute (e.g., 'workflow/process')
    
    
    
    diagram_data: Optional[strawberry.scalars.JSON] = None  # Inline diagram data (alternative to diagram_name)
    
    
    
    input_mapping: Optional[strawberry.scalars.JSON] = None  # Map node inputs to sub-diagram variables
    
    
    
    output_mapping: Optional[strawberry.scalars.JSON] = None  # Map sub-diagram outputs to node outputs
    
    
    
    timeout: Optional[int] = None  # Execution timeout in seconds
    
    
    
    wait_for_completion: Optional[bool] = None  # Whether to wait for sub-diagram completion
    
    
    
    isolate_conversation: Optional[bool] = None  # Create isolated conversation context for sub-diagram
    
    
    
    ignore_if_sub: Optional[bool] = None  # Skip execution if this diagram is being run as a sub-diagram
    
    
    
    # Enum field: Format of the diagram file (yaml, json, or light)
    diagram_format: Optional[str] = None  # Values: ['yaml', 'json', 'light']
    
    
    
    batch: Optional[bool] = None  # Execute sub-diagram in batch mode for multiple inputs
    
    
    
    batch_input_key: Optional[str] = None  # Key in inputs containing the array of items for batch processing
    
    
    
    batch_parallel: Optional[bool] = None  # Execute batch items in parallel
    
    

@strawberry.input
class UpdateSubDiagramInput:
    """Input for updating a Sub-Diagram node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    diagram_name: Optional[str] = None  # Name of the diagram to execute (e.g., 'workflow/process')
    
    
    
    diagram_data: Optional[strawberry.scalars.JSON] = None  # Inline diagram data (alternative to diagram_name)
    
    
    
    input_mapping: Optional[strawberry.scalars.JSON] = None  # Map node inputs to sub-diagram variables
    
    
    
    output_mapping: Optional[strawberry.scalars.JSON] = None  # Map sub-diagram outputs to node outputs
    
    
    
    timeout: Optional[int] = None  # Execution timeout in seconds
    
    
    
    wait_for_completion: Optional[bool] = None  # Whether to wait for sub-diagram completion
    
    
    
    isolate_conversation: Optional[bool] = None  # Create isolated conversation context for sub-diagram
    
    
    
    ignore_if_sub: Optional[bool] = None  # Skip execution if this diagram is being run as a sub-diagram
    
    
    
    # Enum field: Format of the diagram file (yaml, json, or light)
    diagram_format: Optional[str] = None  # Values: ['yaml', 'json', 'light']
    
    
    
    batch: Optional[bool] = None  # Execute sub-diagram in batch mode for multiple inputs
    
    
    
    batch_input_key: Optional[str] = None  # Key in inputs containing the array of items for batch processing
    
    
    
    batch_parallel: Optional[bool] = None  # Execute batch items in parallel
    
    


@strawberry.input
class CreateTemplateJobInput:
    """Input for creating a Template Job node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    template_path: Optional[str] = None  # Path to template file
    
    
    
    template_content: Optional[str] = None  # Inline template content
    
    
    
    output_path: Optional[str] = None  # Output file path
    
    
    
    variables: Optional[strawberry.scalars.JSON] = None  # Variables configuration
    
    
    
    # Enum field: Template engine to use
    engine: Optional[str] = None  # Values: ['internal', 'jinja2']
    
    
    
    preprocessor: Optional[str] = None  # Preprocessor function to apply before templating
    
    

@strawberry.input
class UpdateTemplateJobInput:
    """Input for updating a Template Job node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    template_path: Optional[str] = None  # Path to template file
    
    
    
    template_content: Optional[str] = None  # Inline template content
    
    
    
    output_path: Optional[str] = None  # Output file path
    
    
    
    variables: Optional[strawberry.scalars.JSON] = None  # Variables configuration
    
    
    
    # Enum field: Template engine to use
    engine: Optional[str] = None  # Values: ['internal', 'jinja2']
    
    
    
    preprocessor: Optional[str] = None  # Preprocessor function to apply before templating
    
    


@strawberry.input
class CreateTypescriptAstInput:
    """Input for creating a TypeScript AST Parser node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    source: Optional[str] = None  # TypeScript source code to parse
    
    
    
    # Enum field: Patterns to extract from the AST
    extract_patterns: Optional[str] = None  # Values: ['interface', 'type', 'enum', 'class', 'function', 'const', 'export']
    
    
    
    include_jsdoc: Optional[bool] = None  # Include JSDoc comments in the extracted data
    
    
    
    # Enum field: TypeScript parsing mode
    parse_mode: Optional[str] = None  # Values: ['module', 'script']
    
    
    
    transform_enums: Optional[bool] = None  # Transform enum definitions to a simpler format
    
    
    
    flatten_output: Optional[bool] = None  # Flatten the output structure for easier consumption
    
    
    
    # Enum field: Output format for the parsed data
    output_format: Optional[str] = None  # Values: ['standard', 'for_codegen', 'for_analysis']
    
    
    
    batch: Optional[bool] = None  # Enable batch processing mode
    
    
    
    batch_input_key: Optional[str] = None  # Key to extract batch items from input
    
    

@strawberry.input
class UpdateTypescriptAstInput:
    """Input for updating a TypeScript AST Parser node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    source: Optional[str] = None  # TypeScript source code to parse
    
    
    
    # Enum field: Patterns to extract from the AST
    extract_patterns: Optional[str] = None  # Values: ['interface', 'type', 'enum', 'class', 'function', 'const', 'export']
    
    
    
    include_jsdoc: Optional[bool] = None  # Include JSDoc comments in the extracted data
    
    
    
    # Enum field: TypeScript parsing mode
    parse_mode: Optional[str] = None  # Values: ['module', 'script']
    
    
    
    transform_enums: Optional[bool] = None  # Transform enum definitions to a simpler format
    
    
    
    flatten_output: Optional[bool] = None  # Flatten the output structure for easier consumption
    
    
    
    # Enum field: Output format for the parsed data
    output_format: Optional[str] = None  # Values: ['standard', 'for_codegen', 'for_analysis']
    
    
    
    batch: Optional[bool] = None  # Enable batch processing mode
    
    
    
    batch_input_key: Optional[str] = None  # Key to extract batch items from input
    
    


@strawberry.input
class CreateUserResponseInput:
    """Input for creating a User Response node"""
    diagram_id: str
    position: Vec2Input
    label: Optional[str] = None

    # Node-specific fields from specification
    
    
    prompt: str  # Question to ask the user
    
    
    
    timeout: Optional[int] = None  # Response timeout in seconds
    
    

@strawberry.input
class UpdateUserResponseInput:
    """Input for updating a User Response node"""
    position: Optional[Vec2Input] = None
    label: Optional[str] = None

    # Node-specific fields from specification (all optional for updates)
    
    
    prompt: Optional[str] = None  # Question to ask the user
    
    
    
    timeout: Optional[int] = None  # Response timeout in seconds
    
    





@strawberry.type
class NodeMutations:
    """Type-safe mutations for node operations"""




    @strawberry.mutation
    async def create_api_key(
        self,
        info: Info,
        
        
        input: CreateApiKeyInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """CreateApiKey - ApiKey mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "CreateApiKey".lower()

        
        # API Key mutations
        service = registry.resolve(API_KEY_SERVICE)
        result = await service.handle_mutation("CreateApiKey", variables)

        

        return result


    @strawberry.mutation
    async def test_api_key(
        self,
        info: Info,
        
        
        api_key_id: str
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """TestApiKey - ApiKey mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "api_key_id": api_key_id
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "TestApiKey".lower()

        
        # API Key mutations
        service = registry.resolve(API_KEY_SERVICE)
        result = await service.handle_mutation("TestApiKey", variables)

        

        return result


    @strawberry.mutation
    async def delete_api_key(
        self,
        info: Info,
        
        
        api_key_id: str
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """DeleteApiKey - ApiKey mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "api_key_id": api_key_id
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "DeleteApiKey".lower()

        
        # API Key mutations
        service = registry.resolve(API_KEY_SERVICE)
        result = await service.handle_mutation("DeleteApiKey", variables)

        

        return result


    @strawberry.mutation
    async def register_cli_session(
        self,
        info: Info,
        
        
        input: RegisterCliSessionInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """RegisterCliSession - CliSession mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "RegisterCliSession".lower()

        
        # Default to DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("RegisterCliSession", variables)
        

        return result


    @strawberry.mutation
    async def unregister_cli_session(
        self,
        info: Info,
        
        
        input: UnregisterCliSessionInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """UnregisterCliSession - CliSession mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "UnregisterCliSession".lower()

        
        # Default to DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("UnregisterCliSession", variables)
        

        return result


    @strawberry.mutation
    async def create_diagram(
        self,
        info: Info,
        
        
        input: CreateDiagramInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """CreateDiagram - Diagram mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "CreateDiagram".lower()

        
        # Diagram mutations
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("CreateDiagram", variables)

        

        return result


    @strawberry.mutation
    async def execute_diagram(
        self,
        info: Info,
        
        
        input: ExecuteDiagramInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """ExecuteDiagram - Diagram mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "ExecuteDiagram".lower()

        
        # Diagram mutations
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("ExecuteDiagram", variables)

        

        return result


    @strawberry.mutation
    async def delete_diagram(
        self,
        info: Info,
        
        
        diagram_id: str
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """DeleteDiagram - Diagram mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "diagram_id": diagram_id
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "DeleteDiagram".lower()

        
        # Diagram mutations
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("DeleteDiagram", variables)

        

        return result


    @strawberry.mutation
    async def control_execution(
        self,
        info: Info,
        
        
        input: ExecutionControlInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """ControlExecution - Execution mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "ControlExecution".lower()

        
        # Execution mutations
        service = registry.resolve(EXECUTION_SERVICE)
        result = await service.handle_mutation("ControlExecution", variables)

        

        return result


    @strawberry.mutation
    async def send_interactive_response(
        self,
        info: Info,
        
        
        input: InteractiveResponseInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """SendInteractiveResponse - Execution mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "SendInteractiveResponse".lower()

        
        # Default to DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("SendInteractiveResponse", variables)
        

        return result


    @strawberry.mutation
    async def update_node_state(
        self,
        info: Info,
        
        
        input: UpdateNodeStateInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """UpdateNodeState - Execution mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "UpdateNodeState".lower()

        
        # Node-related mutations use DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)

        # Call the appropriate method based on the operation
        
        result = await service.update_node(**variables)
        

        

        return result


    @strawberry.mutation
    async def upload_file(
        self,
        info: Info,
        
        
        file: Upload,
        
        path: Optional[str]
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """UploadFile - File mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "file": file,
            
            "path": path
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "UploadFile".lower()

        
        # Default to DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("UploadFile", variables)
        

        return result


    @strawberry.mutation
    async def upload_diagram(
        self,
        info: Info,
        
        
        file: Upload,
        
        format: DiagramFormatGraphQL
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """UploadDiagram - File mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "file": file,
            
            "format": format
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "UploadDiagram".lower()

        
        # Diagram mutations
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("UploadDiagram", variables)

        

        return result


    @strawberry.mutation
    async def validate_diagram(
        self,
        info: Info,
        
        
        content: str,
        
        format: DiagramFormatGraphQL
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """ValidateDiagram - File mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "content": content,
            
            "format": format
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "ValidateDiagram".lower()

        
        # Diagram mutations
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("ValidateDiagram", variables)

        

        return result


    @strawberry.mutation
    async def convert_diagram_format(
        self,
        info: Info,
        
        
        content: str,
        
        from_format: DiagramFormatGraphQL,
        
        to_format: DiagramFormatGraphQL
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """ConvertDiagramFormat - File mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "content": content,
            
            "from_format": from_format,
            
            "to_format": to_format
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "ConvertDiagramFormat".lower()

        
        # Diagram mutations
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("ConvertDiagramFormat", variables)

        

        return result


    @strawberry.mutation
    async def create_node(
        self,
        info: Info,
        
        
        diagram_id: str,
        
        input: CreateNodeInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """CreateNode - Node mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "diagram_id": diagram_id,
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "CreateNode".lower()

        
        # Node-related mutations use DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)

        # Call the appropriate method based on the operation
        
        result = await service.create_node(**variables)
        

        

        return result


    @strawberry.mutation
    async def update_node(
        self,
        info: Info,
        
        
        diagram_id: str,
        
        node_id: str,
        
        input: UpdateNodeInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """UpdateNode - Node mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "diagram_id": diagram_id,
            
            "node_id": node_id,
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "UpdateNode".lower()

        
        # Node-related mutations use DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)

        # Call the appropriate method based on the operation
        
        result = await service.update_node(**variables)
        

        

        return result


    @strawberry.mutation
    async def delete_node(
        self,
        info: Info,
        
        
        diagram_id: str,
        
        node_id: str
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """DeleteNode - Node mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "diagram_id": diagram_id,
            
            "node_id": node_id
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "DeleteNode".lower()

        
        # Node-related mutations use DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)

        # Call the appropriate method based on the operation
        
        result = await service.delete_node(**variables)
        

        

        return result


    @strawberry.mutation
    async def create_person(
        self,
        info: Info,
        
        
        input: CreatePersonInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """CreatePerson - Person mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "CreatePerson".lower()

        
        # Person mutations
        service = registry.resolve(PERSON_REPOSITORY)
        result = await service.handle_mutation("CreatePerson", variables)

        

        return result


    @strawberry.mutation
    async def update_person(
        self,
        info: Info,
        
        
        person_id: str,
        
        input: UpdatePersonInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """UpdatePerson - Person mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "person_id": person_id,
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "UpdatePerson".lower()

        
        # Person mutations
        service = registry.resolve(PERSON_REPOSITORY)
        result = await service.handle_mutation("UpdatePerson", variables)

        

        return result


    @strawberry.mutation
    async def delete_person(
        self,
        info: Info,
        
        
        person_id: str
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """DeletePerson - Person mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "person_id": person_id
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "DeletePerson".lower()

        
        # Person mutations
        service = registry.resolve(PERSON_REPOSITORY)
        result = await service.handle_mutation("DeletePerson", variables)

        

        return result


    @strawberry.mutation
    async def execute_integration(
        self,
        info: Info,
        
        
        input: ExecuteIntegrationInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """ExecuteIntegration - Provider mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "ExecuteIntegration".lower()

        
        # Default to DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("ExecuteIntegration", variables)
        

        return result


    @strawberry.mutation
    async def test_integration(
        self,
        info: Info,
        
        
        input: TestIntegrationInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """TestIntegration - Provider mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "TestIntegration".lower()

        
        # Default to DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("TestIntegration", variables)
        

        return result


    @strawberry.mutation
    async def reload_provider(
        self,
        info: Info,
        
        
        name: str
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """ReloadProvider - Provider mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "name": name
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "ReloadProvider".lower()

        
        # Default to DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("ReloadProvider", variables)
        

        return result





# Export mutations
__all__ = [
    'NodeMutations',


    'CreateApiJobInput',
    'UpdateApiJobInput',

    'CreateCodeJobInput',
    'UpdateCodeJobInput',

    'CreateConditionInput',
    'UpdateConditionInput',

    'CreateDbInput',
    'UpdateDbInput',

    'CreateDiffPatchInput',
    'UpdateDiffPatchInput',

    'CreateEndpointInput',
    'UpdateEndpointInput',

    'CreateHookInput',
    'UpdateHookInput',

    'CreateIntegratedApiInput',
    'UpdateIntegratedApiInput',

    'CreateIrBuilderInput',
    'UpdateIrBuilderInput',

    'CreateJsonSchemaValidatorInput',
    'UpdateJsonSchemaValidatorInput',

    'CreatePersonJobInput',
    'UpdatePersonJobInput',

    'CreateStartInput',
    'UpdateStartInput',

    'CreateSubDiagramInput',
    'UpdateSubDiagramInput',

    'CreateTemplateJobInput',
    'UpdateTemplateJobInput',

    'CreateTypescriptAstInput',
    'UpdateTypescriptAstInput',

    'CreateUserResponseInput',
    'UpdateUserResponseInput',


]
