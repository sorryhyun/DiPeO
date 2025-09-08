"""
Strawberry GraphQL types for DiPeO nodes.
Generated automatically from node specifications.

Generated at: 2025-09-08T13:30:38.637056
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

@strawberry.experimental.pydantic.type(ApiJobNode, all_fields=True)
class ApiJobDataType:
    """Make HTTP API requests - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(CodeJobNode, all_fields=True)
class CodeJobDataType:
    """Execute custom code functions - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(ConditionNode, all_fields=True)
class ConditionDataType:
    """Conditional branching based on expressions - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(DbNode, all_fields=True)
class DbDataType:
    """Database operations - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(EndpointNode, all_fields=True)
class EndpointDataType:
    """Exit point for diagram execution - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(HookNode, all_fields=True)
class HookDataType:
    """Executes hooks at specific points in the diagram execution - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(IntegratedApiNode, all_fields=True)
class IntegratedApiDataType:
    """Connect to external APIs like Notion, Slack, GitHub, and more - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(JsonSchemaValidatorNode, all_fields=True)
class JsonSchemaValidatorDataType:
    """Validate data against JSON schema - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(PersonJobNode, all_fields=True)
class PersonJobDataType:
    """Execute tasks using AI language models - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(StartNode, all_fields=True)
class StartDataType:
    """Entry point for diagram execution - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(SubDiagramNode, all_fields=True)
class SubDiagramDataType:
    """Execute another diagram as a node within the current diagram - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(TemplateJobNode, all_fields=True)
class TemplateJobDataType:
    """Process templates with data - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(TypescriptAstNode, all_fields=True)
class TypescriptAstDataType:
    """Parses TypeScript source code and extracts AST, interfaces, types, and enums - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(UserResponseNode, all_fields=True)
class UserResponseDataType:
    """Collect user input - Data fields only"""
    pass




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

    'ApiJobDataType',

    'CodeJobDataType',

    'ConditionDataType',

    'DbDataType',

    'EndpointDataType',

    'HookDataType',

    'IntegratedApiDataType',

    'JsonSchemaValidatorDataType',

    'PersonJobDataType',

    'StartDataType',

    'SubDiagramDataType',

    'TemplateJobDataType',

    'TypescriptAstDataType',

    'UserResponseDataType',

]
