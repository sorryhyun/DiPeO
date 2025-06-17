"""
CLI-specific models for diagram validation and structure.

These models mirror the server domain models but are maintained independently
to ensure the CLI remains decoupled from server internals.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum


class NodeType(str, Enum):
    """Types of nodes in a diagram"""
    CONDITION = "condition"
    DB = "db"
    ENDPOINT = "endpoint"
    JOB = "job"
    LLM = "llm"
    MAPPER = "mapper"
    NOTION = "notion"
    PERSON_JOB = "person_job"
    START = "start"
    USER_RESPONSE = "user_response"


class LLMService(str, Enum):
    """Available LLM service providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    BEDROCK = "bedrock"
    GOOGLE = "google"
    GROQ = "groq"
    OLLAMA = "ollama"
    TEST = "test"


@dataclass
class DiagramMetadata:
    """Metadata for a diagram"""
    name: str = "Untitled Diagram"
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    modified: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "2.0.0"
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "created": self.created,
            "modified": self.modified,
            "version": self.version,
            "description": self.description,
            "tags": self.tags
        }


@dataclass
class Node:
    """Basic node structure"""
    id: str
    type: str
    position: Dict[str, float]
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type,
            "position": self.position,
            "data": self.data
        }


@dataclass 
class Arrow:
    """Connection between nodes"""
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "sourceHandle": self.sourceHandle,
            "targetHandle": self.targetHandle
        }


@dataclass
class Handle:
    """Connection point on a node"""
    id: str
    nodeId: str
    type: str  # "source" or "target"
    position: str  # "top", "bottom", "left", "right"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "nodeId": self.nodeId,
            "type": self.type,
            "position": self.position
        }


@dataclass
class Person:
    """Person entity in diagram"""
    id: str
    name: str
    apiKey: str
    llmModel: str = "gpt-4.1-nano"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "apiKey": self.apiKey,
            "llmModel": self.llmModel
        }


@dataclass
class APIKey:
    """API key configuration"""
    id: str
    label: str
    service: str
    key: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "label": self.label,
            "service": self.service,
            "key": self.key
        }


class DomainDiagram:
    """
    Domain diagram model for CLI validation.
    
    This is a simplified version that provides basic validation
    without requiring the full server Pydantic models.
    """
    
    def __init__(self, **kwargs):
        # Required fields
        self.nodes: Dict[str, Node] = {}
        self.arrows: Dict[str, Arrow] = {}
        self.handles: Dict[str, Handle] = {}
        self.persons: Dict[str, Person] = {}
        self.api_keys: Dict[str, APIKey] = {}
        
        # Optional metadata
        self.metadata = DiagramMetadata()
        
        # Process input data
        self._process_input(kwargs)
    
    def _process_input(self, data: Dict[str, Any]):
        """Process input data and populate fields"""
        # Convert nodes
        if 'nodes' in data:
            for node_id, node_data in data['nodes'].items():
                self.nodes[node_id] = Node(
                    id=node_id,
                    type=node_data.get('type', 'unknown'),
                    position=node_data.get('position', {'x': 0, 'y': 0}),
                    data=node_data.get('data', {})
                )
        
        # Convert arrows
        if 'arrows' in data:
            for arrow_id, arrow_data in data['arrows'].items():
                self.arrows[arrow_id] = Arrow(
                    id=arrow_id,
                    source=arrow_data.get('source', ''),
                    target=arrow_data.get('target', ''),
                    sourceHandle=arrow_data.get('sourceHandle'),
                    targetHandle=arrow_data.get('targetHandle')
                )
        
        # Convert handles
        if 'handles' in data:
            for handle_id, handle_data in data['handles'].items():
                self.handles[handle_id] = Handle(
                    id=handle_id,
                    nodeId=handle_data.get('nodeId', ''),
                    type=handle_data.get('type', 'source'),
                    position=handle_data.get('position', 'bottom')
                )
        
        # Convert persons
        if 'persons' in data:
            for person_id, person_data in data['persons'].items():
                self.persons[person_id] = Person(
                    id=person_id,
                    name=person_data.get('name', 'Unknown'),
                    apiKey=person_data.get('apiKey', ''),
                    llmModel=person_data.get('llmModel', 'gpt-4.1-nano')
                )
        
        # Convert API keys (handle both api_keys and apiKeys)
        api_keys_data = data.get('api_keys', data.get('apiKeys', {}))
        if api_keys_data:
            for key_id, key_data in api_keys_data.items():
                self.api_keys[key_id] = APIKey(
                    id=key_id,
                    label=key_data.get('label', 'API Key'),
                    service=key_data.get('service', 'openai'),
                    key=key_data.get('key', '')
                )
        
        # Process metadata
        if 'metadata' in data:
            meta = data['metadata']
            self.metadata = DiagramMetadata(
                name=meta.get('name', 'Untitled Diagram'),
                created=meta.get('created', datetime.now().isoformat()),
                modified=meta.get('modified', datetime.now().isoformat()),
                version=meta.get('version', '2.0.0'),
                description=meta.get('description'),
                tags=meta.get('tags', [])
            )
    
    def model_dump(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "arrows": {k: v.to_dict() for k, v in self.arrows.items()},
            "handles": {k: v.to_dict() for k, v in self.handles.items()},
            "persons": {k: v.to_dict() for k, v in self.persons.items()},
            "api_keys": {k: v.to_dict() for k, v in self.api_keys.items()},
            "metadata": self.metadata.to_dict()
        }
    
    def validate(self) -> bool:
        """Basic validation"""
        # Check for start node
        has_start = any(node.type == NodeType.START for node in self.nodes.values())
        if not has_start:
            raise ValueError("Diagram must have at least one START node")
        
        # Check that arrows reference valid nodes
        node_ids = set(self.nodes.keys())
        for arrow in self.arrows.values():
            if arrow.source not in node_ids:
                raise ValueError(f"Arrow {arrow.id} references invalid source node: {arrow.source}")
            if arrow.target not in node_ids:
                raise ValueError(f"Arrow {arrow.id} references invalid target node: {arrow.target}")
        
        # Check that persons reference valid API keys
        api_key_ids = set(self.api_keys.keys())
        for person in self.persons.values():
            if person.apiKey and person.apiKey not in api_key_ids:
                raise ValueError(f"Person {person.id} references invalid API key: {person.apiKey}")
        
        return True