"""
Auto-generated static node types from domain models.
DO NOT EDIT THIS FILE DIRECTLY.
Generated by: dipeo/models/scripts/generate-static-nodes.ts
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union, Literal

from dipeo.models.models import (
    NodeType, Vec2, NodeID, PersonID, MemoryConfig, MemorySettings, ToolConfig,
    HookTriggerMode, SupportedLanguage, HttpMethod, DBBlockSubType,
    NotionOperation, HookType, PersonLLMConfig, LLMService
)


@dataclass(frozen=True)
class BaseExecutableNode:
    """Base class for all executable node types."""
    id: NodeID
    type: NodeType
    position: Vec2
    label: str = ""
    flipped: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        result = {
            "id": self.id,
            "type": self.type.value,
            "position": {"x": self.position.x, "y": self.position.y},
            "label": self.label,
            "flipped": self.flipped
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass(frozen=True)
class StartNode(BaseExecutableNode):
    type: NodeType = field(default=NodeType.start, init=False)
    custom_data: Dict[str, Union[str, int, bool]] = field(default_factory=dict)
    output_data_structure: Dict[str, str] = field(default_factory=dict)
    trigger_mode: Optional[HookTriggerMode] = None
    hook_event: str = None
    hook_filters: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data["custom_data"] = self.custom_data
        data["output_data_structure"] = self.output_data_structure
        data["trigger_mode"] = self.trigger_mode
        data["hook_event"] = self.hook_event
        data["hook_filters"] = self.hook_filters
        return data

@dataclass(frozen=True)
class EndpointNode(BaseExecutableNode):
    type: NodeType = field(default=NodeType.endpoint, init=False)
    save_to_file: bool = False
    file_name: str = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data["save_to_file"] = self.save_to_file
        data["file_name"] = self.file_name
        return data

@dataclass(frozen=True)
class PersonJobNode(BaseExecutableNode):
    type: NodeType = field(default=NodeType.person_job, init=False)
    person_id: Optional[PersonID] = None
    first_only_prompt: str = ""
    default_prompt: str = None
    max_iteration: int = 1
    memory_config: Optional[MemoryConfig] = None
    memory_settings: Optional[MemorySettings] = None
    tools: Optional[List[ToolConfig]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data["person"] = self.person_id
        data["first_only_prompt"] = self.first_only_prompt
        data["default_prompt"] = self.default_prompt
        data["max_iteration"] = self.max_iteration
        data["memory_config"] = self.memory_config
        data["memory_settings"] = self.memory_settings
        data["tools"] = self.tools
        return data

@dataclass(frozen=True)
class ConditionNode(BaseExecutableNode):
    type: NodeType = field(default=NodeType.condition, init=False)
    condition_type: str = ""
    expression: str = None
    node_indices: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data["condition_type"] = self.condition_type
        data["expression"] = self.expression
        data["node_indices"] = self.node_indices
        return data

@dataclass(frozen=True)
class CodeJobNode(BaseExecutableNode):
    type: NodeType = field(default=NodeType.code_job, init=False)
    language: SupportedLanguage = SupportedLanguage.python
    code: str = ""
    timeout: int = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data["language"] = self.language
        data["code"] = self.code
        data["timeout"] = self.timeout
        return data

@dataclass(frozen=True)
class ApiJobNode(BaseExecutableNode):
    type: NodeType = field(default=NodeType.api_job, init=False)
    url: str = ""
    method: HttpMethod = HttpMethod.GET
    headers: Dict[str, str] = None
    params: Dict[str, Any] = None
    body: Any = None
    timeout: int = None
    auth_type: Optional[Literal["none", "bearer", "basic", "api_key"]] = None
    auth_config: Dict[str, str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data["url"] = self.url
        data["method"] = self.method
        data["headers"] = self.headers
        data["params"] = self.params
        data["body"] = self.body
        data["timeout"] = self.timeout
        data["auth_type"] = self.auth_type
        data["auth_config"] = self.auth_config
        return data

@dataclass(frozen=True)
class DBNode(BaseExecutableNode):
    type: NodeType = field(default=NodeType.db, init=False)
    file: str = None
    collection: str = None
    sub_type: DBBlockSubType = DBBlockSubType.fixed_prompt
    operation: str = ""
    query: str = None
    data: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data["file"] = self.file
        data["collection"] = self.collection
        data["sub_type"] = self.sub_type
        data["operation"] = self.operation
        data["query"] = self.query
        data["data"] = self.data
        return data

@dataclass(frozen=True)
class UserResponseNode(BaseExecutableNode):
    type: NodeType = field(default=NodeType.user_response, init=False)
    prompt: str = ""
    timeout: int = 60

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data["prompt"] = self.prompt
        data["timeout"] = self.timeout
        return data

@dataclass(frozen=True)
class NotionNode(BaseExecutableNode):
    type: NodeType = field(default=NodeType.notion, init=False)
    operation: NotionOperation = NotionOperation.read_page
    page_id: str = None
    database_id: str = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data["operation"] = self.operation
        data["page_id"] = self.page_id
        data["database_id"] = self.database_id
        return data

@dataclass(frozen=True)
class HookNode(BaseExecutableNode):
    type: NodeType = field(default=NodeType.hook, init=False)
    hook_type: HookType = HookType.shell
    config: Dict[str, Any] = field(default_factory=dict)
    timeout: int = None
    retry_count: int = None
    retry_delay: int = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = super().to_dict()
        data["hook_type"] = self.hook_type
        data["config"] = self.config
        data["timeout"] = self.timeout
        data["retry_count"] = self.retry_count
        data["retry_delay"] = self.retry_delay
        return data

@dataclass(frozen=True)
class PersonBatchJobNode(PersonJobNode):
    """Person batch job node - same as PersonJobNode but with different type."""
    type: NodeType = field(default=NodeType.person_batch_job, init=False)


ExecutableNode = Union[
    StartNode,
    EndpointNode,
    PersonJobNode,
    ConditionNode,
    CodeJobNode,
    ApiJobNode,
    DBNode,
    UserResponseNode,
    NotionNode,
    PersonBatchJobNode,
    HookNode
]


def create_executable_node(
    node_type: NodeType,
    node_id: NodeID,
    position: Vec2,
    label: str = "",
    data: Optional[Dict[str, Any]] = None,
    flipped: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> ExecutableNode:
    """Factory function to create typed executable nodes from diagram data."""
    data = data or {}
    
    if node_type == NodeType.start:
        return StartNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            custom_data=data.get("custom_data"),
            output_data_structure=data.get("output_data_structure"),
            trigger_mode=data.get("trigger_mode"),
            hook_event=data.get("hook_event"),
            hook_filters=data.get("hook_filters"),
        )
    
    if node_type == NodeType.endpoint:
        return EndpointNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            save_to_file=data.get("save_to_file", False),
            file_name=data.get("file_name"),
        )
    
    if node_type == NodeType.person_job:
        return PersonJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            person_id=data.get("person"),
            first_only_prompt=data.get("first_only_prompt", ""),
            default_prompt=data.get("default_prompt"),
            max_iteration=data.get("max_iteration", 1),
            memory_config=MemoryConfig(**data.get("memory_config")) if data.get("memory_config") else None,
            memory_settings=MemorySettings(**data.get("memory_settings")) if data.get("memory_settings") else None,
            tools=[ToolConfig(**tool) if isinstance(tool, dict) else tool for tool in data.get("tools", [])] if data.get("tools") else None,
        )
    
    if node_type == NodeType.condition:
        return ConditionNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            condition_type=data.get("condition_type", ""),
            expression=data.get("expression"),
            node_indices=data.get("node_indices"),
        )
    
    if node_type == NodeType.code_job:
        return CodeJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            language=data.get("language", SupportedLanguage.python),
            code=data.get("code", ""),
            timeout=data.get("timeout"),
        )
    
    if node_type == NodeType.api_job:
        return ApiJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            url=data.get("url", ""),
            method=data.get("method", HttpMethod.GET),
            headers=data.get("headers"),
            params=data.get("params"),
            body=data.get("body"),
            timeout=data.get("timeout"),
            auth_type=data.get("auth_type"),
            auth_config=data.get("auth_config"),
        )
    
    if node_type == NodeType.db:
        return DBNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            file=data.get("file"),
            collection=data.get("collection"),
            sub_type=data.get("sub_type", DBBlockSubType.fixed_prompt),
            operation=data.get("operation", ""),
            query=data.get("query"),
            data=data.get("data"),
        )
    
    if node_type == NodeType.user_response:
        return UserResponseNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            prompt=data.get("prompt", ""),
            timeout=data.get("timeout", 60),
        )
    
    if node_type == NodeType.notion:
        return NotionNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            operation=data.get("operation", NotionOperation.read_page),
            page_id=data.get("page_id"),
            database_id=data.get("database_id"),
        )
    
    if node_type == NodeType.hook:
        return HookNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            hook_type=data.get("hook_type", HookType.shell),
            config=data.get("config", {}),
            timeout=data.get("timeout"),
            retry_count=data.get("retry_count"),
            retry_delay=data.get("retry_delay"),
        )
    
    if node_type == NodeType.person_batch_job:
        return PersonBatchJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            person_id=data.get("person"),
            first_only_prompt=data.get("first_only_prompt", ""),
            default_prompt=data.get("default_prompt"),
            max_iteration=data.get("max_iteration", 1),
            memory_config=MemoryConfig(**data.get("memory_config")) if data.get("memory_config") else None,
            memory_settings=MemorySettings(**data.get("memory_settings")) if data.get("memory_settings") else None,
            tools=[ToolConfig(**tool) if isinstance(tool, dict) else tool for tool in data.get("tools", [])] if data.get("tools") else None
        )
    
    raise ValueError(f"Unknown node type: {node_type}")
