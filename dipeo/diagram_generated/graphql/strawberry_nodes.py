







"""
Strawberry GraphQL types for DiPeO nodes.
Generated automatically from node specifications.

Generated at: 2025-08-15T17:45:30.621921
"""

import strawberry
from typing import *
from strawberry.types import *

# Import Pydantic models

from ..domain_models import *


# Import scalars
from dipeo.application.graphql.types.scalars import *


# Generate Strawberry types for node data

@strawberry.experimental.pydantic.type(ApiJobNodeData, all_fields=True)
class ApiJobDataType:
    """Make HTTP API requests - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(CodeJobNodeData, all_fields=True)
class CodeJobDataType:
    """Execute custom code functions - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(ConditionNodeData, all_fields=True)
class ConditionDataType:
    """Conditional branching based on expressions - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(DBNodeData, all_fields=True)
class DBDataType:
    """Database operations - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(EndpointNodeData, all_fields=True)
class EndpointDataType:
    """Exit point for diagram execution - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(HookNodeData, all_fields=True)
class HookDataType:
    """Executes hooks at specific points in the diagram execution - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(IntegratedApiNodeData, all_fields=True)
class IntegratedApiDataType:
    """Connect to external APIs like Notion, Slack, GitHub, and more - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(JsonSchemaValidatorNodeData, all_fields=True)
class JsonSchemaValidatorDataType:
    """Validate data against JSON schema - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(PersonBatchJobNodeData, all_fields=True)
class PersonBatchJobDataType:
    """Execute AI tasks on batches of data using language models - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(PersonJobNodeData, all_fields=True)
class PersonJobDataType:
    """Execute tasks using AI language models - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(StartNodeData, all_fields=True)
class StartDataType:
    """Entry point for diagram execution - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(SubDiagramNodeData, all_fields=True)
class SubDiagramDataType:
    """Execute another diagram as a node within the current diagram - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(TemplateJobNodeData, all_fields=True)
class TemplateJobDataType:
    """Process templates with data - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(TypescriptAstNodeData, all_fields=True)
class TypescriptAstDataType:
    """Parses TypeScript source code and extracts AST, interfaces, types, and enums - Data fields only"""
    pass


@strawberry.experimental.pydantic.type(UserResponseNodeData, all_fields=True)
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

        DBDataType,

        EndpointDataType,

        HookDataType,

        IntegratedApiDataType,

        JsonSchemaValidatorDataType,

        PersonBatchJobDataType,

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

    'DBDataType',

    'EndpointDataType',

    'HookDataType',

    'IntegratedApiDataType',

    'JsonSchemaValidatorDataType',

    'PersonBatchJobDataType',

    'PersonJobDataType',

    'StartDataType',

    'SubDiagramDataType',

    'TemplateJobDataType',

    'TypescriptAstDataType',

    'UserResponseDataType',

]