"""
Strawberry GraphQL mutations for DiPeO nodes.
Generated automatically from node specifications.

Generated at: 2025-08-01T14:04:11.829121
"""

import strawberry
from typing import Optional
from strawberry.types import Info

# Import data types and unions
from .strawberry_nodes import (
    NodeDataUnion,

    ApiJobDataType,

    CodeJobDataType,

    ConditionDataType,

    DbDataType,

    EndpointDataType,

    HookDataType,

    JsonSchemaValidatorDataType,

    NotionDataType,

    PersonBatchJobDataType,

    PersonJobDataType,

    StartDataType,

    SubDiagramDataType,

    TemplateJobDataType,

    TypescriptAstDataType,

    UserResponseDataType,

)

# Import base types
from dipeo.application.graphql.types.domain_types import DomainNodeType
from dipeo.application.graphql.types.inputs import Vec2Input

# Import services and keys
from dipeo.application.registry import ServiceRegistry, ServiceKey

# Service keys
INTEGRATED_DIAGRAM_SERVICE = ServiceKey("integrated_diagram_service")


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
class CreateNotionInput:
    """Input for creating a Notion node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input  
class UpdateNotionInput:
    """Input for updating a Notion node"""
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: Optional[strawberry.scalars.JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreatePersonBatchJobInput:
    """Input for creating a Person Batch Job node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input  
class UpdatePersonBatchJobInput:
    """Input for updating a Person Batch Job node"""
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
    

    @strawberry.mutation
    async def create_api_job_node(
        self,
        info: Info,
        input: CreateApiJobInput
    ) -> ApiJobDataType:
        """Create a Api Job node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "api_job",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_api_job_node(
        self,
        info: Info,
        id: str, input: UpdateApiJobInput
    ) -> ApiJobDataType:
        """Update a Api Job node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def create_code_job_node(
        self,
        info: Info,
        input: CreateCodeJobInput
    ) -> CodeJobDataType:
        """Create a Code Job node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "code_job",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_code_job_node(
        self,
        info: Info,
        id: str, input: UpdateCodeJobInput
    ) -> CodeJobDataType:
        """Update a Code Job node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def create_condition_node(
        self,
        info: Info,
        input: CreateConditionInput
    ) -> ConditionDataType:
        """Create a Condition node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "condition",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_condition_node(
        self,
        info: Info,
        id: str, input: UpdateConditionInput
    ) -> ConditionDataType:
        """Update a Condition node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def create_db_node(
        self,
        info: Info,
        input: CreateDbInput
    ) -> DbDataType:
        """Create a Db node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "db",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_db_node(
        self,
        info: Info,
        id: str, input: UpdateDbInput
    ) -> DbDataType:
        """Update a Db node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def create_endpoint_node(
        self,
        info: Info,
        input: CreateEndpointInput
    ) -> EndpointDataType:
        """Create a Endpoint node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "endpoint",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_endpoint_node(
        self,
        info: Info,
        id: str, input: UpdateEndpointInput
    ) -> EndpointDataType:
        """Update a Endpoint node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def create_hook_node(
        self,
        info: Info,
        input: CreateHookInput
    ) -> HookDataType:
        """Create a Hook node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "hook",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_hook_node(
        self,
        info: Info,
        id: str, input: UpdateHookInput
    ) -> HookDataType:
        """Update a Hook node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def create_json_schema_validator_node(
        self,
        info: Info,
        input: CreateJsonSchemaValidatorInput
    ) -> JsonSchemaValidatorDataType:
        """Create a Json Schema Validator node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "json_schema_validator",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_json_schema_validator_node(
        self,
        info: Info,
        id: str, input: UpdateJsonSchemaValidatorInput
    ) -> JsonSchemaValidatorDataType:
        """Update a Json Schema Validator node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def create_notion_node(
        self,
        info: Info,
        input: CreateNotionInput
    ) -> NotionDataType:
        """Create a Notion node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "notion",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_notion_node(
        self,
        info: Info,
        id: str, input: UpdateNotionInput
    ) -> NotionDataType:
        """Update a Notion node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def create_person_batch_job_node(
        self,
        info: Info,
        input: CreatePersonBatchJobInput
    ) -> PersonBatchJobDataType:
        """Create a Person Batch Job node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "person_batch_job",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_person_batch_job_node(
        self,
        info: Info,
        id: str, input: UpdatePersonBatchJobInput
    ) -> PersonBatchJobDataType:
        """Update a Person Batch Job node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def create_person_job_node(
        self,
        info: Info,
        input: CreatePersonJobInput
    ) -> PersonJobDataType:
        """Create a Person Job node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "person_job",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_person_job_node(
        self,
        info: Info,
        id: str, input: UpdatePersonJobInput
    ) -> PersonJobDataType:
        """Update a Person Job node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def create_start_node(
        self,
        info: Info,
        input: CreateStartInput
    ) -> StartDataType:
        """Create a Start node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "start",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_start_node(
        self,
        info: Info,
        id: str, input: UpdateStartInput
    ) -> StartDataType:
        """Update a Start node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def create_sub_diagram_node(
        self,
        info: Info,
        input: CreateSubDiagramInput
    ) -> SubDiagramDataType:
        """Create a Sub Diagram node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "sub_diagram",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_sub_diagram_node(
        self,
        info: Info,
        id: str, input: UpdateSubDiagramInput
    ) -> SubDiagramDataType:
        """Update a Sub Diagram node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def create_template_job_node(
        self,
        info: Info,
        input: CreateTemplateJobInput
    ) -> TemplateJobDataType:
        """Create a Template Job node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "template_job",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_template_job_node(
        self,
        info: Info,
        id: str, input: UpdateTemplateJobInput
    ) -> TemplateJobDataType:
        """Update a Template Job node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def create_typescript_ast_node(
        self,
        info: Info,
        input: CreateTypescriptAstInput
    ) -> TypescriptAstDataType:
        """Create a Typescript Ast node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "typescript_ast",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_typescript_ast_node(
        self,
        info: Info,
        id: str, input: UpdateTypescriptAstInput
    ) -> TypescriptAstDataType:
        """Update a Typescript Ast node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def create_user_response_node(
        self,
        info: Info,
        input: CreateUserResponseInput
    ) -> UserResponseDataType:
        """Create a User Response node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "user_response",
            "position": input.position,
            "data": input.data
        }
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Create the node
        domain_node = await integrated_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )


    @strawberry.mutation
    async def update_user_response_node(
        self,
        info: Info,
        id: str, input: UpdateUserResponseInput
    ) -> UserResponseDataType:
        """Update a User Response node"""
        registry: ServiceRegistry = info.context["registry"]
        
        
        # Get integrated diagram service
        integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
        
        # Update the node
        domain_node = await integrated_service.update_node(
            diagram_id=None,  # TODO: Need diagram_id from somewhere
            node_id=id,
            data=input.data
        )
        
        
        # Convert to GraphQL type
        # For now, return the DomainNodeType directly
        return DomainNodeType(
            id=domain_node.id,
            type=domain_node.type,
            position=domain_node.position,
            data=domain_node.data
        )




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

    'CreateJsonSchemaValidatorInput',
    'UpdateJsonSchemaValidatorInput',

    'CreateNotionInput',
    'UpdateNotionInput',

    'CreatePersonBatchJobInput',
    'UpdatePersonBatchJobInput',

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