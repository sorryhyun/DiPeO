"""
Strawberry GraphQL types for DiPeO nodes.
Generated automatically from node specifications.

Generated at: 2025-07-28T22:25:46.312651
"""

import strawberry
from typing import Optional, List, Dict, Any
from strawberry.types import Info

# Import Pydantic models
from dipeo.diagram_generated.nodes import (

    ApiJobNode,

    CodeJobNode,

    ConditionNode,

    DbNode,

    EndpointNode,

    HookNode,

    JsonSchemaValidatorNode,

    NotionNode,

    PersonBatchJobNode,

    PersonJobNode,

    StartNode,

    SubDiagramNode,

    TemplateJobNode,

    TypescriptAstNode,

    UserResponseNode,

)

# Import domain types
from .domain_types import (
    Vec2Type,
    DomainHandleType,
    NodeStateType,
)

# Import scalars
from ..scalars import NodeIDScalar


# Define the Node interface
@strawberry.interface
class Node:
    """Base interface for all diagram nodes"""
    id: NodeIDScalar
    position: Vec2Type
    
    @strawberry.field
    def type(self) -> str:
        """The node type identifier"""
        return self.__class__.__name__.replace('NodeType', '').lower()


# Generate Strawberry types for each node

@strawberry.experimental.pydantic.type(ApiJobNode)
class ApiJobNodeType(Node):
    """Make HTTP API requests"""
    # All fields are automatically generated from Pydantic model
    pass


@strawberry.experimental.pydantic.type(CodeJobNode)
class CodeJobNodeType(Node):
    """Execute custom code functions"""
    # All fields are automatically generated from Pydantic model
    pass


@strawberry.experimental.pydantic.type(ConditionNode)
class ConditionNodeType(Node):
    """Conditional branching based on expressions"""
    # All fields are automatically generated from Pydantic model
    pass


@strawberry.experimental.pydantic.type(DbNode)
class DbNodeType(Node):
    """Database operations"""
    # All fields are automatically generated from Pydantic model
    pass


@strawberry.experimental.pydantic.type(EndpointNode)
class EndpointNodeType(Node):
    """Exit point for diagram execution"""
    # All fields are automatically generated from Pydantic model
    pass


@strawberry.experimental.pydantic.type(HookNode)
class HookNodeType(Node):
    """Executes hooks at specific points in the diagram execution"""
    # All fields are automatically generated from Pydantic model
    pass


@strawberry.experimental.pydantic.type(JsonSchemaValidatorNode)
class JsonSchemaValidatorNodeType(Node):
    """Validate data against JSON schema"""
    # All fields are automatically generated from Pydantic model
    pass


@strawberry.experimental.pydantic.type(NotionNode)
class NotionNodeType(Node):
    """Integrate with Notion API to query, create, or update database entries"""
    # All fields are automatically generated from Pydantic model
    pass


@strawberry.experimental.pydantic.type(PersonBatchJobNode)
class PersonBatchJobNodeType(Node):
    """Execute AI tasks on batches of data using language models"""
    # All fields are automatically generated from Pydantic model
    pass


@strawberry.experimental.pydantic.type(PersonJobNode)
class PersonJobNodeType(Node):
    """Execute tasks using AI language models"""
    # All fields are automatically generated from Pydantic model
    pass


@strawberry.experimental.pydantic.type(StartNode)
class StartNodeType(Node):
    """Entry point for diagram execution"""
    # All fields are automatically generated from Pydantic model
    pass


@strawberry.experimental.pydantic.type(SubDiagramNode)
class SubDiagramNodeType(Node):
    """Execute another diagram as a node within the current diagram"""
    # All fields are automatically generated from Pydantic model
    pass


@strawberry.experimental.pydantic.type(TemplateJobNode)
class TemplateJobNodeType(Node):
    """Process templates with data"""
    # All fields are automatically generated from Pydantic model
    pass


@strawberry.experimental.pydantic.type(TypescriptAstNode)
class TypescriptAstNodeType(Node):
    """Parses TypeScript source code and extracts AST, interfaces, types, and enums"""
    # All fields are automatically generated from Pydantic model
    pass


@strawberry.experimental.pydantic.type(UserResponseNode)
class UserResponseNodeType(Node):
    """Collect user input"""
    # All fields are automatically generated from Pydantic model
    pass



# Create union type for all nodes
DiagramNode = strawberry.union(
    "DiagramNode",
    (

        ApiJobNodeType,

        CodeJobNodeType,

        ConditionNodeType,

        DbNodeType,

        EndpointNodeType,

        HookNodeType,

        JsonSchemaValidatorNodeType,

        NotionNodeType,

        PersonBatchJobNodeType,

        PersonJobNodeType,

        StartNodeType,

        SubDiagramNodeType,

        TemplateJobNodeType,

        TypescriptAstNodeType,

        UserResponseNodeType,

    )
)


# Node type resolver
def resolve_node_type(domain_node: Any) -> Node:
    """Resolve a domain node to the correct GraphQL type."""
    node_type_map = {

        "api_job": ApiJobNodeType,

        "code_job": CodeJobNodeType,

        "condition": ConditionNodeType,

        "db": DbNodeType,

        "endpoint": EndpointNodeType,

        "hook": HookNodeType,

        "json_schema_validator": JsonSchemaValidatorNodeType,

        "notion": NotionNodeType,

        "person_batch_job": PersonBatchJobNodeType,

        "person_job": PersonJobNodeType,

        "start": StartNodeType,

        "sub_diagram": SubDiagramNodeType,

        "template_job": TemplateJobNodeType,

        "typescript_ast": TypescriptAstNodeType,

        "user_response": UserResponseNodeType,

    }
    
    node_type = domain_node.type
    graphql_type = node_type_map.get(node_type)
    
    if not graphql_type:
        raise ValueError(f"Unknown node type: {node_type}")
    
    # Convert domain node to GraphQL type
    return graphql_type.from_pydantic(domain_node)


# Export all types
__all__ = [
    'Node',
    'DiagramNode',
    'resolve_node_type',

    'ApiJobNodeType',

    'CodeJobNodeType',

    'ConditionNodeType',

    'DbNodeType',

    'EndpointNodeType',

    'HookNodeType',

    'JsonSchemaValidatorNodeType',

    'NotionNodeType',

    'PersonBatchJobNodeType',

    'PersonJobNodeType',

    'StartNodeType',

    'SubDiagramNodeType',

    'TemplateJobNodeType',

    'TypescriptAstNodeType',

    'UserResponseNodeType',

]