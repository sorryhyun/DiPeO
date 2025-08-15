"""Node specifications with explicit input/output contracts.

Each node type declares its inputs and outputs explicitly, enabling:
- Compile-time validation
- Explicit data flow
- No hidden dependencies
- Type-safe execution
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Protocol
from enum import Enum

from dipeo.diagram_generated.enums import ContentType


class Cardinality(Enum):
    """Output cardinality for nodes."""
    SINGLE = "single"
    MULTI = "multi"


@dataclass
class InputDecl:
    """Declaration of a node input."""
    
    name: str
    content_type: ContentType
    required: bool = True
    provider: str | None = None  # Name of provider if not from edges
    description: str = ""
    
    def __post_init__(self):
        """Validate input declaration."""
        if self.provider and not self.name.startswith("_"):
            raise ValueError(
                f"Provider-backed inputs should start with underscore: {self.name}"
            )


@dataclass
class OutputSpec:
    """Specification for node outputs."""
    
    content_type: ContentType
    cardinality: Cardinality = Cardinality.SINGLE
    description: str = ""
    
    @classmethod
    def single(cls, content_type: ContentType, description: str = "") -> OutputSpec:
        """Create a single-output spec."""
        return cls(content_type, Cardinality.SINGLE, description)
    
    @classmethod
    def multi(cls, content_type: ContentType, description: str = "") -> OutputSpec:
        """Create a multi-output spec."""
        return cls(content_type, Cardinality.MULTI, description)


@dataclass
class NodeSpec:
    """Complete specification for a node type."""
    
    inputs: dict[str, InputDecl] = field(default_factory=dict)
    outputs: OutputSpec = field(default_factory=lambda: OutputSpec.single(ContentType.RAW_TEXT))
    description: str = ""
    
    def get_required_inputs(self) -> list[str]:
        """Get names of required inputs."""
        return [name for name, decl in self.inputs.items() if decl.required]
    
    def get_provider_inputs(self) -> dict[str, str]:
        """Get inputs that come from providers."""
        return {
            name: decl.provider 
            for name, decl in self.inputs.items() 
            if decl.provider
        }
    
    def validate_inputs(self, provided: dict[str, Any]) -> list[str]:
        """Validate provided inputs against spec.
        
        Returns list of missing required inputs.
        """
        missing = []
        for name in self.get_required_inputs():
            if name not in provided:
                # Check if it's a provider input
                if not self.inputs[name].provider:
                    missing.append(name)
        return missing


# Default specs for common node types
class NodeSpecs:
    """Registry of node specifications."""
    
    START = NodeSpec(
        inputs={},
        outputs=OutputSpec.single(ContentType.RAW_TEXT),
        description="Start node with no inputs"
    )
    
    END = NodeSpec(
        inputs={
            "input": InputDecl("input", ContentType.RAW_TEXT, required=False)
        },
        outputs=OutputSpec.single(ContentType.RAW_TEXT),
        description="End node that collects results"
    )
    
    PERSON_JOB = NodeSpec(
        inputs={
            "prompt": InputDecl("prompt", ContentType.RAW_TEXT, required=True),
            "items": InputDecl("items", ContentType.OBJECT, required=False),
            "_conversation": InputDecl(
                "_conversation",
                ContentType.OBJECT,
                required=False,
                provider="ConversationProvider",
                description="Conversation state from provider"
            ),
            "_variables": InputDecl(
                "_variables",
                ContentType.OBJECT,
                required=False,
                provider="VariablesProvider",
                description="Execution variables from provider"
            )
        },
        outputs=OutputSpec.single(ContentType.RAW_TEXT),
        description="LLM-powered conversation node"
    )
    
    CONDITION = NodeSpec(
        inputs={
            "value": InputDecl("value", ContentType.OBJECT, required=True),
            "_variables": InputDecl(
                "_variables",
                ContentType.OBJECT,
                required=False,
                provider="VariablesProvider"
            )
        },
        outputs=OutputSpec.single(ContentType.OBJECT),
        description="Conditional branching node"
    )
    
    CODE_JOB = NodeSpec(
        inputs={
            "code": InputDecl("code", ContentType.RAW_TEXT, required=True),
            "input": InputDecl("input", ContentType.OBJECT, required=False),
            "_variables": InputDecl(
                "_variables",
                ContentType.OBJECT,
                required=False,
                provider="VariablesProvider"
            )
        },
        outputs=OutputSpec.single(ContentType.OBJECT),
        description="Code execution node"
    )
    
    API = NodeSpec(
        inputs={
            "url": InputDecl("url", ContentType.RAW_TEXT, required=True),
            "method": InputDecl("method", ContentType.RAW_TEXT, required=False),
            "headers": InputDecl("headers", ContentType.OBJECT, required=False),
            "body": InputDecl("body", ContentType.OBJECT, required=False)
        },
        outputs=OutputSpec.single(ContentType.OBJECT),
        description="External API call node"
    )
    
    TYPESCRIPT_AST = NodeSpec(
        inputs={
            "code": InputDecl("code", ContentType.RAW_TEXT, required=True)
        },
        outputs=OutputSpec.single(ContentType.OBJECT),
        description="TypeScript AST parser node"
    )
    
    DB = NodeSpec(
        inputs={
            "query": InputDecl("query", ContentType.RAW_TEXT, required=True),
            "params": InputDecl("params", ContentType.OBJECT, required=False)
        },
        outputs=OutputSpec.single(ContentType.OBJECT),
        description="Database query node"
    )
    
    NOTION = NodeSpec(
        inputs={
            "action": InputDecl("action", ContentType.RAW_TEXT, required=True),
            "params": InputDecl("params", ContentType.OBJECT, required=False)
        },
        outputs=OutputSpec.single(ContentType.OBJECT),
        description="Notion API integration node"
    )
    
    FILE = NodeSpec(
        inputs={
            "path": InputDecl("path", ContentType.RAW_TEXT, required=True),
            "operation": InputDecl("operation", ContentType.RAW_TEXT, required=True),
            "content": InputDecl("content", ContentType.RAW_TEXT, required=False)
        },
        outputs=OutputSpec.single(ContentType.RAW_TEXT),
        description="File system operations node"
    )
    
    BATCH = NodeSpec(
        inputs={
            "items": InputDecl("items", ContentType.OBJECT, required=True),
            "template": InputDecl("template", ContentType.OBJECT, required=True)
        },
        outputs=OutputSpec.multi(ContentType.OBJECT),
        description="Batch processing node with multiple outputs"
    )
    
    @classmethod
    def get(cls, node_type: str) -> NodeSpec | None:
        """Get spec for a node type."""
        return getattr(cls, node_type.upper(), None)


def get_node_spec(node_type: str) -> NodeSpec | None:
    """Get the specification for a node type.
    
    Args:
        node_type: The type of node (e.g., "person_job", "condition")
        
    Returns:
        NodeSpec if found, None otherwise
    """
    return NodeSpecs.get(node_type)