"""
Strawberry GraphQL mutations for DiPeO nodes.
Generated automatically from node specifications.

Generated at: 2025-09-17T16:05:06.250858
"""

import strawberry
from typing import *
from strawberry.types import *

# Import data types and unions
from .strawberry_nodes import *

# Import base types
from dipeo.diagram_generated.graphql.domain_types import *
from dipeo.diagram_generated.graphql.inputs import *
from .enums import DiagramFormatGraphQL
from strawberry.file_uploads import Upload

# Import services and keys
from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import (
    DIAGRAM_PORT,
    EXECUTION_SERVICE,
    PERSON_REPOSITORY,
    CONVERSATION_REPOSITORY,
    API_KEY_SERVICE,
    ServiceKey
)


# Generate input types for each node if node_specs exist


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
class CreateIrBuilderInput:
    """Input for creating a IR Builder node"""
    diagram_id: str
    position: Vec2Input
    # TODO: Add node-specific fields from spec
    # For now, we accept a generic data dict that will be validated
    data: strawberry.scalars.JSON

@strawberry.input
class UpdateIrBuilderInput:
    """Input for updating a IR Builder node"""
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




    @strawberry.mutation
    async def create_api_key(
        self,
        info: Info,
        
        
        input: CreateApiKeyInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """CreateApiKey - ApiKey mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "CreateApiKey".lower()

        
        # API Key mutations
        service = registry.resolve(API_KEY_SERVICE)
        result = await service.handle_mutation("CreateApiKey", variables)

        

        return result


    @strawberry.mutation
    async def test_api_key(
        self,
        info: Info,
        
        
        api_key_id: str
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """TestApiKey - ApiKey mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "api_key_id": api_key_id
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "TestApiKey".lower()

        
        # API Key mutations
        service = registry.resolve(API_KEY_SERVICE)
        result = await service.handle_mutation("TestApiKey", variables)

        

        return result


    @strawberry.mutation
    async def delete_api_key(
        self,
        info: Info,
        
        
        api_key_id: str
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """DeleteApiKey - ApiKey mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "api_key_id": api_key_id
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "DeleteApiKey".lower()

        
        # API Key mutations
        service = registry.resolve(API_KEY_SERVICE)
        result = await service.handle_mutation("DeleteApiKey", variables)

        

        return result


    @strawberry.mutation
    async def register_cli_session(
        self,
        info: Info,
        
        
        input: RegisterCliSessionInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """RegisterCliSession - CliSession mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "RegisterCliSession".lower()

        
        # Default to DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("RegisterCliSession", variables)
        

        return result


    @strawberry.mutation
    async def unregister_cli_session(
        self,
        info: Info,
        
        
        input: UnregisterCliSessionInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """UnregisterCliSession - CliSession mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "UnregisterCliSession".lower()

        
        # Default to DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("UnregisterCliSession", variables)
        

        return result


    @strawberry.mutation
    async def create_diagram(
        self,
        info: Info,
        
        
        input: CreateDiagramInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """CreateDiagram - Diagram mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "CreateDiagram".lower()

        
        # Diagram mutations
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("CreateDiagram", variables)

        

        return result


    @strawberry.mutation
    async def execute_diagram(
        self,
        info: Info,
        
        
        input: ExecuteDiagramInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """ExecuteDiagram - Diagram mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "ExecuteDiagram".lower()

        
        # Diagram mutations
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("ExecuteDiagram", variables)

        

        return result


    @strawberry.mutation
    async def delete_diagram(
        self,
        info: Info,
        
        
        diagram_id: str
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """DeleteDiagram - Diagram mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "diagram_id": diagram_id
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "DeleteDiagram".lower()

        
        # Diagram mutations
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("DeleteDiagram", variables)

        

        return result


    @strawberry.mutation
    async def control_execution(
        self,
        info: Info,
        
        
        input: ExecutionControlInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """ControlExecution - Execution mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "ControlExecution".lower()

        
        # Execution mutations
        service = registry.resolve(EXECUTION_SERVICE)
        result = await service.handle_mutation("ControlExecution", variables)

        

        return result


    @strawberry.mutation
    async def send_interactive_response(
        self,
        info: Info,
        
        
        input: InteractiveResponseInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """SendInteractiveResponse - Execution mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "SendInteractiveResponse".lower()

        
        # Default to DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("SendInteractiveResponse", variables)
        

        return result


    @strawberry.mutation
    async def update_node_state(
        self,
        info: Info,
        
        
        input: UpdateNodeStateInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """UpdateNodeState - Execution mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "UpdateNodeState".lower()

        
        # Node-related mutations use DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)

        # Call the appropriate method based on the operation
        
        result = await service.update_node(**variables)
        

        

        return result


    @strawberry.mutation
    async def upload_file(
        self,
        info: Info,
        
        
        file: Upload,
        
        path: Optional[str]
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """UploadFile - File mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "file": file,
            
            "path": path
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "UploadFile".lower()

        
        # Default to DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("UploadFile", variables)
        

        return result


    @strawberry.mutation
    async def upload_diagram(
        self,
        info: Info,
        
        
        file: Upload,
        
        format: DiagramFormatGraphQL
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """UploadDiagram - File mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "file": file,
            
            "format": format
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "UploadDiagram".lower()

        
        # Diagram mutations
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("UploadDiagram", variables)

        

        return result


    @strawberry.mutation
    async def validate_diagram(
        self,
        info: Info,
        
        
        content: str,
        
        format: DiagramFormatGraphQL
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """ValidateDiagram - File mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "content": content,
            
            "format": format
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "ValidateDiagram".lower()

        
        # Diagram mutations
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("ValidateDiagram", variables)

        

        return result


    @strawberry.mutation
    async def convert_diagram_format(
        self,
        info: Info,
        
        
        content: str,
        
        from_format: DiagramFormatGraphQL,
        
        to_format: DiagramFormatGraphQL
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """ConvertDiagramFormat - File mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "content": content,
            
            "from_format": from_format,
            
            "to_format": to_format
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "ConvertDiagramFormat".lower()

        
        # Diagram mutations
        service = registry.resolve(DIAGRAM_PORT)
        result = await service.handle_mutation("ConvertDiagramFormat", variables)

        

        return result


    @strawberry.mutation
    async def create_node(
        self,
        info: Info,
        
        
        diagram_id: str,
        
        input: CreateNodeInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """CreateNode - Node mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "diagram_id": diagram_id,
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "CreateNode".lower()

        
        # Node-related mutations use DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)

        # Call the appropriate method based on the operation
        
        result = await service.create_node(**variables)
        

        

        return result


    @strawberry.mutation
    async def update_node(
        self,
        info: Info,
        
        
        diagram_id: str,
        
        node_id: str,
        
        input: UpdateNodeInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """UpdateNode - Node mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "diagram_id": diagram_id,
            
            "node_id": node_id,
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "UpdateNode".lower()

        
        # Node-related mutations use DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)

        # Call the appropriate method based on the operation
        
        result = await service.update_node(**variables)
        

        

        return result


    @strawberry.mutation
    async def delete_node(
        self,
        info: Info,
        
        
        diagram_id: str,
        
        node_id: str
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """DeleteNode - Node mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "diagram_id": diagram_id,
            
            "node_id": node_id
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "DeleteNode".lower()

        
        # Node-related mutations use DIAGRAM_PORT
        service = registry.resolve(DIAGRAM_PORT)

        # Call the appropriate method based on the operation
        
        result = await service.delete_node(**variables)
        

        

        return result


    @strawberry.mutation
    async def create_person(
        self,
        info: Info,
        
        
        input: CreatePersonInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """CreatePerson - Person mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "CreatePerson".lower()

        
        # Person mutations
        service = registry.resolve(PERSON_REPOSITORY)
        result = await service.handle_mutation("CreatePerson", variables)

        

        return result


    @strawberry.mutation
    async def update_person(
        self,
        info: Info,
        
        
        person_id: str,
        
        input: UpdatePersonInput
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """UpdatePerson - Person mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "person_id": person_id,
            
            "input": input
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "UpdatePerson".lower()

        
        # Person mutations
        service = registry.resolve(PERSON_REPOSITORY)
        result = await service.handle_mutation("UpdatePerson", variables)

        

        return result


    @strawberry.mutation
    async def delete_person(
        self,
        info: Info,
        
        
        person_id: str
        
        
    ) -> Any:  # Return type will be determined by the resolver
        """DeletePerson - Person mutation"""
        registry: ServiceRegistry = info.context["registry"]

        # Build variables dict
        variables = {
            
            
            "person_id": person_id
            
            
        }

        # Determine service and execute mutation based on type
        mutation_lower = "DeletePerson".lower()

        
        # Person mutations
        service = registry.resolve(PERSON_REPOSITORY)
        result = await service.handle_mutation("DeletePerson", variables)

        

        return result





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

    'CreateIrBuilderInput',
    'UpdateIrBuilderInput',

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
