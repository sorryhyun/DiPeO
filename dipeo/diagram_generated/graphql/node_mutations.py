"""
Strawberry GraphQL mutations for DiPeO nodes.
Generated automatically from node specifications.

Generated at: 2025-09-13T16:47:42.128948
"""

import strawberry
from typing import *
from strawberry.types import *

# Import data types and unions
from .strawberry_nodes import *

# Import base types
from dipeo.diagram_generated.graphql.domain_types import *
from dipeo.diagram_generated.graphql.inputs import *

# Import services and keys
from dipeo.application.registry import *
from dipeo.application.registry.keys import *


# Generate input types for each node

@strawberry.input
class CreateApiJobInput:
    """Input for creating a API Job node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdateApiJobInput:
    """Input for updating a API Job node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreateCodeJobInput:
    """Input for creating a Code Job node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdateCodeJobInput:
    """Input for updating a Code Job node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreateConditionInput:
    """Input for creating a Condition node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdateConditionInput:
    """Input for updating a Condition node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreateDbInput:
    """Input for creating a Database node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdateDbInput:
    """Input for updating a Database node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreateEndpointInput:
    """Input for creating a End Node node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdateEndpointInput:
    """Input for updating a End Node node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreateHookInput:
    """Input for creating a Hook node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdateHookInput:
    """Input for updating a Hook node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreateIntegratedApiInput:
    """Input for creating a Integrated API node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdateIntegratedApiInput:
    """Input for updating a Integrated API node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreateJsonSchemaValidatorInput:
    """Input for creating a JSON Schema Validator node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdateJsonSchemaValidatorInput:
    """Input for updating a JSON Schema Validator node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreatePersonJobInput:
    """Input for creating a Person Job node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdatePersonJobInput:
    """Input for updating a Person Job node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreateStartInput:
    """Input for creating a Start Node node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdateStartInput:
    """Input for updating a Start Node node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreateSubDiagramInput:
    """Input for creating a Sub-Diagram node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdateSubDiagramInput:
    """Input for updating a Sub-Diagram node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreateTemplateJobInput:
    """Input for creating a Template Job node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdateTemplateJobInput:
    """Input for updating a Template Job node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreateTypescriptAstInput:
    """Input for creating a TypeScript AST Parser node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdateTypescriptAstInput:
    """Input for updating a TypeScript AST Parser node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreateUserResponseInput:
    """Input for creating a User Response node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdateUserResponseInput:
    """Input for updating a User Response node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None




@strawberry.type
class NodeMutations:
    """Type-safe mutations for node operations"""




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

    'CreateEndpointInput',
    'UpdateEndpointInput',

    'CreateHookInput',
    'UpdateHookInput',

    'CreateIntegratedApiInput',
    'UpdateIntegratedApiInput',

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
