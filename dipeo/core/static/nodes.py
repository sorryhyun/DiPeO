"""Immutable node dataclasses for executable diagrams."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

from dipeo.models import (
    NodeID, NodeType, Vec2, PersonID, PersonLLMConfig,
    MemoryConfig, ToolConfig, SupportedLanguage, HttpMethod,
    DBBlockSubType, NotionOperation, HookType, HookTriggerMode
)


@dataclass(frozen=True)
class BaseExecutableNode:
    """Base class for all executable nodes."""
    id: NodeID
    type: NodeType
    position: Vec2
    label: str
    flipped: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type,
            "position": self.position,
            "label": self.label,
            "flipped": self.flipped,
            "metadata": self.metadata
        }


@dataclass(frozen=True)
class StartNode(BaseExecutableNode):
    """Immutable start node configuration."""
    type: NodeType = field(default=NodeType.start, init=False)
    custom_data: Dict[str, Any] = field(default_factory=dict)
    output_data_structure: Dict[str, str] = field(default_factory=dict)
    trigger_mode: Optional[HookTriggerMode] = None
    hook_event: Optional[str] = None
    hook_filters: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data.update({
            "custom_data": self.custom_data,
            "output_data_structure": self.output_data_structure,
            "trigger_mode": self.trigger_mode,
            "hook_event": self.hook_event,
            "hook_filters": self.hook_filters
        })
        return data


@dataclass(frozen=True)
class PersonNode(BaseExecutableNode):
    """Immutable person node configuration."""
    type: NodeType = field(default=NodeType.person_job, init=False)
    person_id: Optional[PersonID] = None
    first_only_prompt: str = ""
    default_prompt: Optional[str] = None
    max_iteration: int = 1
    memory_config: Optional[MemoryConfig] = None
    tools: Optional[List[ToolConfig]] = None
    llm_config: Optional[PersonLLMConfig] = None  # Resolved from person reference
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data.update({
            "person_id": self.person_id,
            "first_only_prompt": self.first_only_prompt,
            "default_prompt": self.default_prompt,
            "max_iteration": self.max_iteration,
            "memory_config": self.memory_config,
            "tools": self.tools,
            "llm_config": self.llm_config
        })
        return data


@dataclass(frozen=True)
class ConditionNode(BaseExecutableNode):
    """Immutable condition node configuration."""
    type: NodeType = field(default=NodeType.condition, init=False)
    condition_type: str = "expression"
    expression: Optional[str] = None
    node_indices: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data.update({
            "condition_type": self.condition_type,
            "expression": self.expression,
            "node_indices": self.node_indices
        })
        return data


@dataclass(frozen=True)
class CodeJobNode(BaseExecutableNode):
    """Immutable code job node configuration."""
    type: NodeType = field(default=NodeType.code_job, init=False)
    language: SupportedLanguage = SupportedLanguage.python
    code: str = ""
    timeout: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data.update({
            "language": self.language,
            "code": self.code,
            "timeout": self.timeout
        })
        return data


@dataclass(frozen=True)
class ApiJobNode(BaseExecutableNode):
    """Immutable API job node configuration."""
    type: NodeType = field(default=NodeType.api_job, init=False)
    url: str = ""
    method: HttpMethod = HttpMethod.GET
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    body: Optional[Any] = None
    timeout: Optional[int] = None
    auth_type: Optional[str] = None
    auth_config: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data.update({
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "params": self.params,
            "body": self.body,
            "timeout": self.timeout,
            "auth_type": self.auth_type,
            "auth_config": self.auth_config
        })
        return data


@dataclass(frozen=True)
class EndpointNode(BaseExecutableNode):
    """Immutable endpoint node configuration."""
    type: NodeType = field(default=NodeType.endpoint, init=False)
    save_to_file: bool = False
    file_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data.update({
            "save_to_file": self.save_to_file,
            "file_name": self.file_name
        })
        return data


@dataclass(frozen=True)
class DBNode(BaseExecutableNode):
    """Immutable database node configuration."""
    type: NodeType = field(default=NodeType.db, init=False)
    file: Optional[str] = None
    collection: Optional[str] = None
    sub_type: DBBlockSubType = DBBlockSubType.fixed_prompt
    operation: str = "read"
    query: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data.update({
            "file": self.file,
            "collection": self.collection,
            "sub_type": self.sub_type,
            "operation": self.operation,
            "query": self.query,
            "data": self.data
        })
        return data


@dataclass(frozen=True)
class UserResponseNode(BaseExecutableNode):
    """Immutable user response node configuration."""
    type: NodeType = field(default=NodeType.user_response, init=False)
    prompt: str = ""
    timeout: int = 300  # 5 minutes default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data.update({
            "prompt": self.prompt,
            "timeout": self.timeout
        })
        return data


@dataclass(frozen=True)
class NotionNode(BaseExecutableNode):
    """Immutable Notion node configuration."""
    type: NodeType = field(default=NodeType.notion, init=False)
    operation: NotionOperation = NotionOperation.create_page
    page_id: Optional[str] = None
    database_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data.update({
            "operation": self.operation,
            "page_id": self.page_id,
            "database_id": self.database_id,
            "properties": self.properties
        })
        return data


@dataclass(frozen=True)
class PersonBatchJobNode(BaseExecutableNode):
    """Immutable person batch job node configuration."""
    type: NodeType = field(default=NodeType.person_batch_job, init=False)
    person_id: Optional[PersonID] = None
    first_only_prompt: str = ""
    default_prompt: Optional[str] = None
    max_iteration: int = 1
    memory_config: Optional[MemoryConfig] = None
    tools: Optional[List[ToolConfig]] = None
    llm_config: Optional[PersonLLMConfig] = None  # Resolved from person reference
    batch_size: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data.update({
            "person_id": self.person_id,
            "first_only_prompt": self.first_only_prompt,
            "default_prompt": self.default_prompt,
            "max_iteration": self.max_iteration,
            "memory_config": self.memory_config,
            "tools": self.tools,
            "llm_config": self.llm_config,
            "batch_size": self.batch_size
        })
        return data


@dataclass(frozen=True)
class HookNode(BaseExecutableNode):
    """Immutable hook node configuration."""
    type: NodeType = field(default=NodeType.hook, init=False)
    hook_type: HookType = HookType.shell
    config: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[int] = None
    retry_count: Optional[int] = None
    retry_delay: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data.update({
            "hook_type": self.hook_type,
            "config": self.config,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay
        })
        return data


# Type alias for any executable node
ExecutableNode = (
    StartNode | PersonNode | ConditionNode | CodeJobNode | 
    ApiJobNode | EndpointNode | DBNode | UserResponseNode | 
    NotionNode | PersonBatchJobNode | HookNode
)


def create_executable_node(node_type: NodeType, node_id: NodeID, 
                          position: Vec2, label: str,
                          data: Dict[str, Any]) -> ExecutableNode:
    """Factory function to create the appropriate executable node type.
    
    Args:
        node_type: The type of node to create
        node_id: Unique identifier for the node
        position: Position coordinates
        label: Display label
        data: Node-specific data
        
    Returns:
        An executable node instance of the appropriate type
        
    Raises:
        ValueError: If the node type is not supported
    """
    common_args = {
        "id": node_id,
        "position": position,
        "label": label,
        "flipped": data.get("flipped", False),
        "metadata": data.get("metadata", {})
    }
    
    if node_type == NodeType.start:
        return StartNode(
            **common_args,
            custom_data=data.get("custom_data", {}),
            output_data_structure=data.get("output_data_structure", {}),
            trigger_mode=data.get("trigger_mode"),
            hook_event=data.get("hook_event"),
            hook_filters=data.get("hook_filters")
        )
    
    elif node_type == NodeType.person_job:
        return PersonNode(
            **common_args,
            person_id=data.get("person"),
            first_only_prompt=data.get("first_only_prompt", ""),
            default_prompt=data.get("default_prompt"),
            max_iteration=data.get("max_iteration", 1),
            memory_config=data.get("memory_config"),
            tools=data.get("tools"),
            llm_config=data.get("llm_config")
        )
    
    elif node_type == NodeType.condition:
        return ConditionNode(
            **common_args,
            condition_type=data.get("condition_type", "expression"),
            expression=data.get("expression"),
            node_indices=data.get("node_indices")
        )
    
    elif node_type == NodeType.code_job:
        return CodeJobNode(
            **common_args,
            language=data.get("language", SupportedLanguage.python),
            code=data.get("code", ""),
            timeout=data.get("timeout")
        )
    
    elif node_type == NodeType.api_job:
        return ApiJobNode(
            **common_args,
            url=data.get("url", ""),
            method=data.get("method", HttpMethod.GET),
            headers=data.get("headers"),
            params=data.get("params"),
            body=data.get("body"),
            timeout=data.get("timeout"),
            auth_type=data.get("auth_type"),
            auth_config=data.get("auth_config")
        )
    
    elif node_type == NodeType.endpoint:
        return EndpointNode(
            **common_args,
            save_to_file=data.get("save_to_file", False),
            file_name=data.get("file_name")
        )
    
    elif node_type == NodeType.db:
        return DBNode(
            **common_args,
            file=data.get("file"),
            collection=data.get("collection"),
            sub_type=data.get("sub_type", DBBlockSubType.fixed_prompt),
            operation=data.get("operation", "read"),
            query=data.get("query"),
            data=data.get("data")
        )
    
    elif node_type == NodeType.user_response:
        return UserResponseNode(
            **common_args,
            prompt=data.get("prompt", ""),
            timeout=data.get("timeout", 300)
        )
    
    elif node_type == NodeType.notion:
        return NotionNode(
            **common_args,
            operation=data.get("operation", NotionOperation.create_page),
            page_id=data.get("page_id"),
            database_id=data.get("database_id"),
            properties=data.get("properties")
        )
    
    elif node_type == NodeType.person_batch_job:
        return PersonBatchJobNode(
            **common_args,
            person_id=data.get("person"),
            first_only_prompt=data.get("first_only_prompt", ""),
            default_prompt=data.get("default_prompt"),
            max_iteration=data.get("max_iteration", 1),
            memory_config=data.get("memory_config"),
            tools=data.get("tools"),
            llm_config=data.get("llm_config"),
            batch_size=data.get("batch_size", 10)
        )
    
    elif node_type == NodeType.hook:
        return HookNode(
            **common_args,
            hook_type=data.get("hook_type", HookType.shell),
            config=data.get("config", {}),
            timeout=data.get("timeout"),
            retry_count=data.get("retry_count"),
            retry_delay=data.get("retry_delay")
        )
    
    else:
        raise ValueError(f"Unsupported node type: {node_type}")