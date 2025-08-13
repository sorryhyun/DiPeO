"""
Pydantic models for DiPeO light diagram generation via LLM.
Leverages existing generated models with their descriptions for better LLM understanding.
"""

from enum import Enum
from typing import List, Dict, Optional, Literal, Union, Any
from pydantic import BaseModel, Field, model_validator, ConfigDict, create_model

from dipeo.diagram_generated.domain_models import (
    StartNodeData as _StartNodeData, 
    DBNodeData as _DBNodeData, 
    CodeJobNodeData as _CodeJobNodeData, 
    PersonJobNodeData as _PersonJobNodeData,
    ConditionNodeData as _ConditionNodeData, 
    SubDiagramNodeData as _SubDiagramNodeData, 
    EndpointNodeData as _EndpointNodeData,
    TemplateJobNodeData as _TemplateJobNodeData, 
    ApiJobNodeData as _ApiJobNodeData, 
    UserResponseNodeData as _UserResponseNodeData
)


# ============================================================================
# Helper function to exclude label field from node data models
# ============================================================================
# The original domain models from dipeo.diagram_generated.domain_models inherit
# from BaseNodeData which includes a 'label' field. In light diagrams, the label
# is at the node level (not in props), so we exclude it to avoid duplication.

def exclude_label_field(model_class):
    """Create a version of the model class without the 'label' field."""
    # Get all fields except 'label'
    fields = {}
    for field_name, field_info in model_class.model_fields.items():
        if field_name != 'label':
            fields[field_name] = (field_info.annotation, field_info)
    
    # Create new model with same name but without label field
    return create_model(
        model_class.__name__,
        __base__=BaseModel,
        __module__=__name__,
        **fields
    )

# Create versions without label field
StartNodeData = exclude_label_field(_StartNodeData)
DBNodeData = exclude_label_field(_DBNodeData)
CodeJobNodeData = exclude_label_field(_CodeJobNodeData)
PersonJobNodeData = exclude_label_field(_PersonJobNodeData)
ConditionNodeData = exclude_label_field(_ConditionNodeData)
SubDiagramNodeData = exclude_label_field(_SubDiagramNodeData)
EndpointNodeData = exclude_label_field(_EndpointNodeData)
TemplateJobNodeData = exclude_label_field(_TemplateJobNodeData)
ApiJobNodeData = exclude_label_field(_ApiJobNodeData)
UserResponseNodeData = exclude_label_field(_UserResponseNodeData)



# ============================================================================
# Light Node Type Enum (matching DiPeO's NodeType values)
# ============================================================================

class LightNodeType(str, Enum):
    """Node types for light diagram format."""
    START = "start"
    DB = "db"
    CODE_JOB = "code_job"
    PERSON_JOB = "person_job"
    CONDITION = "condition"
    SUB_DIAGRAM = "sub_diagram"
    ENDPOINT = "endpoint"
    TEMPLATE_JOB = "template_job"
    API_JOB = "api_job"
    USER_RESPONSE = "user_response"

# ============================================================================
# Light Format Models (simplified for LLM generation)
# ============================================================================

class Position(BaseModel):
    """Node position on the diagram canvas."""
    model_config = ConfigDict(extra='forbid')
    
    x: int = Field(default=100, ge=0, le=3500, description="X coordinate (increment by 200-300 for readability)")
    y: int = Field(default=200, ge=0, le=3500, description="Y coordinate (keep consistent for linear flow)")


# ============================================================================
# Typed Node Classes for Each Node Type
# ============================================================================

class StartNode(BaseModel):
    """Start node in light diagram format."""
    model_config = ConfigDict(extra='forbid')
    
    label: str = Field(description="Unique identifier for this node")
    type: Literal[LightNodeType.START] = LightNodeType.START
    position: Position = Field(default_factory=Position)
    props: StartNodeData

class DBNode(BaseModel):
    """Database node in light diagram format."""
    model_config = ConfigDict(extra='forbid')
    
    label: str = Field(description="Unique identifier for this node")
    type: Literal[LightNodeType.DB] = LightNodeType.DB
    position: Position = Field(default_factory=Position)
    props: DBNodeData

class CodeJobNode(BaseModel):
    """Code execution node in light diagram format."""
    model_config = ConfigDict(extra='forbid')
    
    label: str = Field(description="Unique identifier for this node")
    type: Literal[LightNodeType.CODE_JOB] = LightNodeType.CODE_JOB
    position: Position = Field(default_factory=Position)
    props: CodeJobNodeData

class PersonJobNode(BaseModel):
    """LLM agent node in light diagram format."""
    model_config = ConfigDict(extra='forbid')
    
    label: str = Field(description="Unique identifier for this node")
    type: Literal[LightNodeType.PERSON_JOB] = LightNodeType.PERSON_JOB
    position: Position = Field(default_factory=Position)
    props: PersonJobNodeData

class ConditionNode(BaseModel):
    """Conditional branching node in light diagram format."""
    model_config = ConfigDict(extra='forbid')
    
    label: str = Field(description="Unique identifier for this node")
    type: Literal[LightNodeType.CONDITION] = LightNodeType.CONDITION
    position: Position = Field(default_factory=Position)
    props: ConditionNodeData

class SubDiagramNode(BaseModel):
    """Sub-diagram execution node in light diagram format."""
    model_config = ConfigDict(extra='forbid')
    
    label: str = Field(description="Unique identifier for this node")
    type: Literal[LightNodeType.SUB_DIAGRAM] = LightNodeType.SUB_DIAGRAM
    position: Position = Field(default_factory=Position)
    props: SubDiagramNodeData

class EndpointNode(BaseModel):
    """Endpoint node in light diagram format."""
    model_config = ConfigDict(extra='forbid')
    
    label: str = Field(description="Unique identifier for this node")
    type: Literal[LightNodeType.ENDPOINT] = LightNodeType.ENDPOINT
    position: Position = Field(default_factory=Position)
    props: EndpointNodeData

class TemplateJobNode(BaseModel):
    """Template rendering node in light diagram format."""
    model_config = ConfigDict(extra='forbid')
    
    label: str = Field(description="Unique identifier for this node")
    type: Literal[LightNodeType.TEMPLATE_JOB] = LightNodeType.TEMPLATE_JOB
    position: Position = Field(default_factory=Position)
    props: TemplateJobNodeData

class ApiJobNode(BaseModel):
    """API call node in light diagram format."""
    model_config = ConfigDict(extra='forbid')
    
    label: str = Field(description="Unique identifier for this node")
    type: Literal[LightNodeType.API_JOB] = LightNodeType.API_JOB
    position: Position = Field(default_factory=Position)
    props: ApiJobNodeData

class UserResponseNode(BaseModel):
    """User interaction node in light diagram format."""
    model_config = ConfigDict(extra='forbid')
    
    label: str = Field(description="Unique identifier for this node")
    type: Literal[LightNodeType.USER_RESPONSE] = LightNodeType.USER_RESPONSE
    position: Position = Field(default_factory=Position)
    props: UserResponseNodeData

# Union type for all possible nodes
LightNode = Union[
    StartNode,
    DBNode,
    CodeJobNode,
    PersonJobNode,
    ConditionNode,
    SubDiagramNode,
    EndpointNode,
    TemplateJobNode,
    ApiJobNode,
    UserResponseNode,
]

from dipeo.diagram_generated.enums import ContentType

class LightConnection(BaseModel):
    """Data flow connection between nodes."""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    
    from_node: str = Field(alias="from", description="Source node label or condition handle (e.g., 'Check_condtrue')")
    to: str = Field(description="Target node label")
    label: Optional[str] = Field(
        default=None,
        description="Variable name for accessing this data in target node (e.g., 'raw_data', 'config')"
    )
    content_type: ContentType = Field(
        default=None,
        description="Data transformation: 'raw_text' (default), 'conversation_state', 'object' (dictionary object)"
    )


class LightPerson(BaseModel):
    """LLM agent configuration."""
    model_config = ConfigDict(extra='forbid')
    
    service: str = Field(default="openai", description="LLM service: openai, anthropic, ollama")
    model: str = Field(default="gpt-5-nano-2025-08-07", description="Model identifier")
    api_key_id: str = Field(default="APIKEY_52609F", description="API key ID from apikeys.json")
    system_prompt: Optional[str] = Field(default=None, description="Agent's role and behavior")


class LightDiagram(BaseModel):
    """Complete light diagram specification."""
    model_config = ConfigDict(extra='forbid')
    
    version: Literal["light"] = "light"
    name: str = Field(
        description="Diagram name (alphanumeric with underscores, no spaces)",
        pattern="^[a-zA-Z][a-zA-Z0-9_]*$"
    )
    description: str = Field(description="Brief description of what the diagram does")
    nodes: List[LightNode] = Field(
        min_items=2,
        description="List of typed nodes (must include 'start' node, usually ends with 'endpoint')"
    )
    connections: List[LightConnection] = Field(
        default_factory=list,
        description="Data flow connections between nodes"
    )
    persons: Optional[Dict[str, LightPerson]] = Field(
        default=None,
        description="Named LLM agent configurations (referenced by person_job nodes)"
    )
    
    @model_validator(mode="after")
    def validate_structure(self):
        """Validate diagram structure."""
        # Check for unique labels
        labels = [node.label for node in self.nodes]
        if len(set(labels)) != len(labels):
            duplicates = [l for l in labels if labels.count(l) > 1]
            raise ValueError(f"Duplicate node labels: {duplicates}")
        
        # Check for start node
        has_start = any(node.type == "start" for node in self.nodes)
        if not has_start:
            raise ValueError("Diagram must have a start node")
        
        # Basic connection validation
        valid_labels = set(labels)
        for node in self.nodes:
            if node.type == "condition":
                # Add condition handles
                valid_labels.add(f"{node.label}_condtrue")
                valid_labels.add(f"{node.label}_condfalse")
        
        for conn in self.connections:
            if conn.from_node not in valid_labels:
                raise ValueError(f"Connection from unknown node: {conn.from_node}")
            if conn.to not in labels:
                raise ValueError(f"Connection to unknown node: {conn.to}")
        
        return self


# ============================================================================
# Response Model for LLM Generation
# ============================================================================

class Response(BaseModel):
    """Response containing the generated light diagram."""
    model_config = ConfigDict(extra='forbid')
    
    diagram: LightDiagram

# Rebuild models to ensure proper schema generation for OpenAI API
if __name__ == "__main__":
    LightNode.model_rebuild()
    LightDiagram.model_rebuild()
    Response.model_rebuild()

# ============================================================================
# Helper Functions
# ============================================================================

def create_minimal_diagram(name: str, description: str) -> LightDiagram:
    """Create a minimal valid diagram structure."""
    from dipeo.diagram_generated.enums import HookTriggerMode
    
    return LightDiagram(
        name=name,
        description=description,
        nodes=[
            StartNode(
                label="start",
                type=LightNodeType.START,
                position=Position(x=100, y=200),
                props=StartNodeData(
                    trigger_mode=HookTriggerMode.MANUAL
                )
            ),
            EndpointNode(
                label="endpoint",
                type=LightNodeType.ENDPOINT,
                position=Position(x=300, y=200),
                props=EndpointNodeData(save_to_file=False)
            )
        ],
        connections=[
            LightConnection(from_node="start", to="endpoint")
        ]
    )


def create_pydantic_text_format(class_definitions: str) -> str:
    """
    Helper to create properly formatted text_format content for PersonJob nodes.
    
    Example:
        text_format = create_pydantic_text_format('''
            class Person(BaseModel):
                name: str
                age: int
                
            class Response(BaseModel):
                person: Person
        ''')
    """
    # Ensure necessary imports are included
    if 'from pydantic import' not in class_definitions and 'BaseModel' in class_definitions:
        imports = "from pydantic import BaseModel, Field\nfrom typing import List, Optional, Dict, Any\nfrom enum import Enum\n\n"
        class_definitions = imports + class_definitions
    
    return class_definitions.strip()
