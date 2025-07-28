"""
Strawberry GraphQL mutations for DiPeO nodes.
Generated automatically from node specifications.

Generated at: 2025-07-28T22:33:57.106232
"""

import strawberry
from typing import Optional
from strawberry.types import Info

# Import node types
from .strawberry_nodes import (

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

    resolve_node_type,
)

# Import services
from dipeo.application.unified_service_registry import UnifiedServiceRegistry


# Generate input types for each node

@strawberry.input
class CreateApiJobNodeInput:
    """Input for creating a API Job node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdateApiJobNodeInput:
    """Input for updating a API Job node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict


@strawberry.input
class CreateCodeJobNodeInput:
    """Input for creating a Code Job node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdateCodeJobNodeInput:
    """Input for updating a Code Job node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict


@strawberry.input
class CreateConditionNodeInput:
    """Input for creating a Condition node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdateConditionNodeInput:
    """Input for updating a Condition node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict


@strawberry.input
class CreateDbNodeInput:
    """Input for creating a Database node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdateDbNodeInput:
    """Input for updating a Database node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict


@strawberry.input
class CreateEndpointNodeInput:
    """Input for creating a End Node node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdateEndpointNodeInput:
    """Input for updating a End Node node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict


@strawberry.input
class CreateHookNodeInput:
    """Input for creating a Hook node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdateHookNodeInput:
    """Input for updating a Hook node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict


@strawberry.input
class CreateJsonSchemaValidatorNodeInput:
    """Input for creating a JSON Schema Validator node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdateJsonSchemaValidatorNodeInput:
    """Input for updating a JSON Schema Validator node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict


@strawberry.input
class CreateNotionNodeInput:
    """Input for creating a Notion node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdateNotionNodeInput:
    """Input for updating a Notion node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict


@strawberry.input
class CreatePersonBatchJobNodeInput:
    """Input for creating a Person Batch Job node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdatePersonBatchJobNodeInput:
    """Input for updating a Person Batch Job node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict


@strawberry.input
class CreatePersonJobNodeInput:
    """Input for creating a Person Job node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdatePersonJobNodeInput:
    """Input for updating a Person Job node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict


@strawberry.input
class CreateStartNodeInput:
    """Input for creating a Start Node node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdateStartNodeInput:
    """Input for updating a Start Node node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict


@strawberry.input
class CreateSubDiagramNodeInput:
    """Input for creating a Sub-Diagram node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdateSubDiagramNodeInput:
    """Input for updating a Sub-Diagram node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict


@strawberry.input
class CreateTemplateJobNodeInput:
    """Input for creating a Template Job node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdateTemplateJobNodeInput:
    """Input for updating a Template Job node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict


@strawberry.input
class CreatescriptAstNodeInput:
    """Input for creating a TypeScript AST Parser node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdatescriptAstNodeInput:
    """Input for updating a TypeScript AST Parser node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict


@strawberry.input
class CreateUserResponseNodeInput:
    """Input for creating a User Response node"""
    diagram_id: str
    position: dict
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict

@strawberry.input  
class UpdateUserResponseNodeInput:
    """Input for updating a User Response node"""
    # Node-specific fields would be added here based on the spec
    # For now, we accept a generic data dict
    data: dict




@strawberry.type
class NodeMutations:
    """Type-safe mutations for node operations"""
    

    @strawberry.mutation
    async def create_api_job_node(
        self,
        info: Info,
        input: CreateApiJobNodeInput
    ) -> ApiJobNodeType:
        """Create a Api Job node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "api_job",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return ApiJobNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_api_job_node(
        self,
        info: Info,
        id: str, input: UpdateApiJobNodeInput
    ) -> ApiJobNodeType:
        """Update a Api Job node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return ApiJobNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def create_code_job_node(
        self,
        info: Info,
        input: CreateCodeJobNodeInput
    ) -> CodeJobNodeType:
        """Create a Code Job node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "code_job",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return CodeJobNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_code_job_node(
        self,
        info: Info,
        id: str, input: UpdateCodeJobNodeInput
    ) -> CodeJobNodeType:
        """Update a Code Job node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return CodeJobNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def create_condition_node(
        self,
        info: Info,
        input: CreateConditionNodeInput
    ) -> ConditionNodeType:
        """Create a Condition node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "condition",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return ConditionNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_condition_node(
        self,
        info: Info,
        id: str, input: UpdateConditionNodeInput
    ) -> ConditionNodeType:
        """Update a Condition node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return ConditionNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def create_db_node(
        self,
        info: Info,
        input: CreateDbNodeInput
    ) -> DbNodeType:
        """Create a Db node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "db",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return DbNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_db_node(
        self,
        info: Info,
        id: str, input: UpdateDbNodeInput
    ) -> DbNodeType:
        """Update a Db node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return DbNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def create_endpoint_node(
        self,
        info: Info,
        input: CreateEndpointNodeInput
    ) -> EndpointNodeType:
        """Create a Endpoint node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "endpoint",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return EndpointNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_endpoint_node(
        self,
        info: Info,
        id: str, input: UpdateEndpointNodeInput
    ) -> EndpointNodeType:
        """Update a Endpoint node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return EndpointNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def create_hook_node(
        self,
        info: Info,
        input: CreateHookNodeInput
    ) -> HookNodeType:
        """Create a Hook node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "hook",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return HookNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_hook_node(
        self,
        info: Info,
        id: str, input: UpdateHookNodeInput
    ) -> HookNodeType:
        """Update a Hook node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return HookNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def create_json_schema_validator_node(
        self,
        info: Info,
        input: CreateJsonSchemaValidatorNodeInput
    ) -> JsonSchemaValidatorNodeType:
        """Create a Json Schema Validator node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "json_schema_validator",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return JsonSchemaValidatorNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_json_schema_validator_node(
        self,
        info: Info,
        id: str, input: UpdateJsonSchemaValidatorNodeInput
    ) -> JsonSchemaValidatorNodeType:
        """Update a Json Schema Validator node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return JsonSchemaValidatorNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def create_notion_node(
        self,
        info: Info,
        input: CreateNotionNodeInput
    ) -> NotionNodeType:
        """Create a Notion node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "notion",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return NotionNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_notion_node(
        self,
        info: Info,
        id: str, input: UpdateNotionNodeInput
    ) -> NotionNodeType:
        """Update a Notion node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return NotionNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def create_person_batch_job_node(
        self,
        info: Info,
        input: CreatePersonBatchJobNodeInput
    ) -> PersonBatchJobNodeType:
        """Create a Person Batch Job node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "person_batch_job",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return PersonBatchJobNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_person_batch_job_node(
        self,
        info: Info,
        id: str, input: UpdatePersonBatchJobNodeInput
    ) -> PersonBatchJobNodeType:
        """Update a Person Batch Job node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return PersonBatchJobNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def create_person_job_node(
        self,
        info: Info,
        input: CreatePersonJobNodeInput
    ) -> PersonJobNodeType:
        """Create a Person Job node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "person_job",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return PersonJobNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_person_job_node(
        self,
        info: Info,
        id: str, input: UpdatePersonJobNodeInput
    ) -> PersonJobNodeType:
        """Update a Person Job node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return PersonJobNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def create_start_node(
        self,
        info: Info,
        input: CreateStartNodeInput
    ) -> StartNodeType:
        """Create a Start node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "start",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return StartNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_start_node(
        self,
        info: Info,
        id: str, input: UpdateStartNodeInput
    ) -> StartNodeType:
        """Update a Start node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return StartNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def create_sub_diagram_node(
        self,
        info: Info,
        input: CreateSubDiagramNodeInput
    ) -> SubDiagramNodeType:
        """Create a Sub Diagram node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "sub_diagram",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return SubDiagramNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_sub_diagram_node(
        self,
        info: Info,
        id: str, input: UpdateSubDiagramNodeInput
    ) -> SubDiagramNodeType:
        """Update a Sub Diagram node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return SubDiagramNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def create_template_job_node(
        self,
        info: Info,
        input: CreateTemplateJobNodeInput
    ) -> TemplateJobNodeType:
        """Create a Template Job node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "template_job",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return TemplateJobNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_template_job_node(
        self,
        info: Info,
        id: str, input: UpdateTemplateJobNodeInput
    ) -> TemplateJobNodeType:
        """Update a Template Job node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return TemplateJobNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def create_typescript_ast_node(
        self,
        info: Info,
        input: CreatescriptAstNodeInput
    ) -> TypescriptAstNodeType:
        """Create a Typescript Ast node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "typescript_ast",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return TypescriptAstNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_typescript_ast_node(
        self,
        info: Info,
        id: str, input: UpdatescriptAstNodeInput
    ) -> TypescriptAstNodeType:
        """Update a Typescript Ast node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return TypescriptAstNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def create_user_response_node(
        self,
        info: Info,
        input: CreateUserResponseNodeInput
    ) -> UserResponseNodeType:
        """Create a User Response node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Prepare node data
        node_data = {
            "type": "user_response",
            "position": input.position,
            "data": input.data
        }
        
        # Create the node
        domain_node = await registry.diagram_service.create_node(
            diagram_id=input.diagram_id,
            node_data=node_data
        )
        
        
        # Convert to GraphQL type
        return UserResponseNodeType.from_pydantic(domain_node)


    @strawberry.mutation
    async def update_user_response_node(
        self,
        info: Info,
        id: str, input: UpdateUserResponseNodeInput
    ) -> UserResponseNodeType:
        """Update a User Response node"""
        registry: UnifiedServiceRegistry = info.context["registry"]
        
        
        # Update the node
        domain_node = await registry.node_service.update(
            node_id=id,
            updates={"data": input.data}
        )
        
        
        # Convert to GraphQL type
        return UserResponseNodeType.from_pydantic(domain_node)




# Export mutations
__all__ = [
    'NodeMutations',

    'CreateApiJobNodeInput',
    'UpdateApiJobNodeInput',

    'CreateCodeJobNodeInput',
    'UpdateCodeJobNodeInput',

    'CreateConditionNodeInput',
    'UpdateConditionNodeInput',

    'CreateDbNodeInput',
    'UpdateDbNodeInput',

    'CreateEndpointNodeInput',
    'UpdateEndpointNodeInput',

    'CreateHookNodeInput',
    'UpdateHookNodeInput',

    'CreateJsonSchemaValidatorNodeInput',
    'UpdateJsonSchemaValidatorNodeInput',

    'CreateNotionNodeInput',
    'UpdateNotionNodeInput',

    'CreatePersonBatchJobNodeInput',
    'UpdatePersonBatchJobNodeInput',

    'CreatePersonJobNodeInput',
    'UpdatePersonJobNodeInput',

    'CreateStartNodeInput',
    'UpdateStartNodeInput',

    'CreateSubDiagramNodeInput',
    'UpdateSubDiagramNodeInput',

    'CreateTemplateJobNodeInput',
    'UpdateTemplateJobNodeInput',

    'CreatescriptAstNodeInput',
    'UpdatescriptAstNodeInput',

    'CreateUserResponseNodeInput',
    'UpdateUserResponseNodeInput',

]