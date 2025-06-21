"""Refactored person (LLM agent) related GraphQL mutations using Pydantic models."""
import strawberry
import logging
import uuid

from ..types.results import PersonResult, DeleteResult
from ..types.scalars import DiagramID, PersonID
from ..types.inputs import CreatePersonInput, UpdatePersonInput
from ..context import GraphQLContext
from dipeo_server.domains.diagram.models import DomainPerson
from dipeo_server.core import LLMService, ForgettingMode
from ..models.input_models import (
    CreatePersonInput as PydanticCreatePersonInput,
    UpdatePersonInput as PydanticUpdatePersonInput
)

logger = logging.getLogger(__name__)


@strawberry.type
class PersonMutations:
    """Mutations for person/LLM agent operations."""
    
    @strawberry.mutation
    async def create_person(
        self,
        diagram_id: DiagramID,
        input: CreatePersonInput,
        info: strawberry.Info[GraphQLContext]
    ) -> PersonResult:
        """Create a new person (LLM agent)."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Convert Strawberry input to Pydantic model for validation
            pydantic_input = PydanticCreatePersonInput(
                label=input.label,
                service=input.service,
                model=input.model,
                api_key_id=input.api_key_id,
                system_prompt=input.system_prompt,
                forgetting_mode=input.forgetting_mode,
                temperature=input.temperature,
                max_tokens=input.max_tokens,
                top_p=input.top_p
            )
            
            # Load diagram
            diagram_data = diagram_service.load_diagram(diagram_id)
            if not diagram_data:
                return PersonResult(
                    success=False,
                    error="Diagram not found"
                )
            
            # Generate person ID
            person_id = f"person_{str(uuid.uuid4())[:8]}"
            
            # Create Pydantic person model with validated data
            person = DomainPerson(
                id=person_id,
                label=pydantic_input.label,  # Already trimmed by validation
                service=pydantic_input.service,
                model=pydantic_input.model,  # Already trimmed by validation
                api_key_id=pydantic_input.api_key_id,
                systemPrompt=pydantic_input.system_prompt or "",
                forgettingMode=pydantic_input.forgetting_mode,
                type="person"
            )
            
            # Convert to dict and add additional validated fields
            person_data = person.model_dump()
            # Add optional fields that might not be in the base model
            person_data.update({
                "temperature": pydantic_input.temperature,
                "maxTokens": pydantic_input.max_tokens,
                "topP": pydantic_input.top_p
            })
            
            # Add person to diagram
            if "persons" not in diagram_data:
                diagram_data["persons"] = {}
            diagram_data["persons"][person_id] = person_data
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            return PersonResult(
                success=True,
                person=person,  # Strawberry will handle conversion
                message=f"Created person {person_id}"
            )
            
        except ValueError as e:
            # Pydantic validation error
            logger.error(f"Validation error creating person: {e}")
            return PersonResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to create person: {e}")
            return PersonResult(
                success=False,
                error=f"Failed to create person: {str(e)}"
            )
    
    @strawberry.mutation
    async def update_person(self, input: UpdatePersonInput, info: strawberry.Info[GraphQLContext]) -> PersonResult:
        """Update an existing person."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Convert Strawberry input to Pydantic model for validation
            pydantic_input = PydanticUpdatePersonInput(
                id=input.id,
                label=input.label,
                model=input.model,
                api_key_id=input.api_key_id,
                system_prompt=input.system_prompt,
                forgetting_mode=input.forgetting_mode,
                temperature=input.temperature,
                max_tokens=input.max_tokens,
                top_p=input.top_p
            )
            
            # Find diagram containing this person
            diagrams = diagram_service.list_diagram_files()
            diagram_id = None
            diagram_data = None
            
            for diagram_meta in diagrams:
                temp_diagram = diagram_service.load_diagram(diagram_meta['path'])
                if pydantic_input.id in temp_diagram.get('persons', {}):
                    diagram_id = diagram_meta['path']
                    diagram_data = temp_diagram
                    break
            
            if not diagram_data:
                return PersonResult(
                    success=False,
                    error=f"Person {pydantic_input.id} not found in any diagram"
                )
            
            # Get existing person data
            person_data = diagram_data['persons'][pydantic_input.id]
            
            # Update fields with validated data
            if pydantic_input.label is not None:
                person_data['label'] = pydantic_input.label  # Already trimmed
            if pydantic_input.model is not None:
                person_data['model'] = pydantic_input.model  # Already trimmed
            if pydantic_input.api_key_id is not None:
                person_data['apiKeyId'] = pydantic_input.api_key_id
            if pydantic_input.system_prompt is not None:
                person_data['systemPrompt'] = pydantic_input.system_prompt
            if pydantic_input.forgetting_mode is not None:
                person_data['forgettingMode'] = pydantic_input.forgetting_mode.value
            if pydantic_input.temperature is not None:
                person_data['temperature'] = pydantic_input.temperature  # Already validated range
            if pydantic_input.max_tokens is not None:
                person_data['maxTokens'] = pydantic_input.max_tokens  # Already validated >= 1
            if pydantic_input.top_p is not None:
                person_data['topP'] = pydantic_input.top_p  # Already validated range
            
            # Map service using Pydantic enum
            try:
                service = LLMService(person_data['service'].lower())
            except ValueError:
                service = LLMService.openai
            
            # Map forgetting mode using Pydantic enum
            try:
                forgetting_mode = ForgettingMode(person_data.get('forgettingMode', 'none'))
            except ValueError:
                forgetting_mode = ForgettingMode.no_forget
            
            # Create updated Pydantic model
            updated_person = DomainPerson(
                id=pydantic_input.id,
                label=person_data['label'],
                service=service,
                model=person_data.get('model', person_data.get('modelName', 'gpt-4')),
                api_key_id=person_data.get('apiKeyId', ''),
                systemPrompt=person_data.get('systemPrompt', ''),
                forgettingMode=forgetting_mode,
                type=person_data.get('type', 'person')
            )
            
            # Update diagram with validated data
            person_dict = updated_person.model_dump()
            # Preserve additional fields
            person_dict.update({
                "temperature": person_data.get('temperature'),
                "maxTokens": person_data.get('maxTokens'),
                "topP": person_data.get('topP')
            })
            diagram_data['persons'][pydantic_input.id] = person_dict
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            return PersonResult(
                success=True,
                person=updated_person,  # Strawberry will handle conversion
                message=f"Updated person {pydantic_input.id}"
            )
            
        except ValueError as e:
            # Pydantic validation error
            logger.error(f"Validation error updating person: {e}")
            return PersonResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to update person: {e}")
            return PersonResult(
                success=False,
                error=f"Failed to update person: {str(e)}"
            )
    
    @strawberry.mutation
    async def delete_person(self, id: PersonID, info: strawberry.Info[GraphQLContext]) -> DeleteResult:
        """Delete a person."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Find diagram containing this person
            diagrams = diagram_service.list_diagram_files()
            diagram_id = None
            diagram_data = None
            
            for diagram_meta in diagrams:
                temp_diagram = diagram_service.load_diagram(diagram_meta['path'])
                if id in temp_diagram.get('persons', {}):
                    diagram_id = diagram_meta['path']
                    diagram_data = temp_diagram
                    break
            
            if not diagram_data:
                return DeleteResult(
                    success=False,
                    error=f"Person {id} not found in any diagram"
                )
            
            # Remove person
            del diagram_data['persons'][id]
            
            # Update any nodes that reference this person
            nodes_updated = 0
            for node in diagram_data.get('nodes', {}).values():
                if node.get('data', {}).get('personId') == id:
                    del node['data']['personId']
                    nodes_updated += 1
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            return DeleteResult(
                success=True,
                deleted_id=id,
                message=f"Deleted person {id} and updated {nodes_updated} nodes"
            )
            
        except Exception as e:
            logger.error(f"Failed to delete person {id}: {e}")
            return DeleteResult(
                success=False,
                error=f"Failed to delete person: {str(e)}"
            )
    
    @strawberry.mutation
    async def initialize_model(self, info, person_id: PersonID) -> PersonResult:
        """Pre-initialize/warm up a model for faster first execution."""
        try:
            context: GraphQLContext = info.context
            llm_service = context.llm_service
            diagram_service = context.diagram_service
            
            # Find person in diagrams
            person_data = None
            diagram_id = None
            
            diagrams = diagram_service.list_diagram_files()
            for diagram_meta in diagrams:
                diagram = diagram_service.load_diagram(diagram_meta['path'])
                if person_id in diagram.get('persons', {}):
                    person_data = diagram['persons'][person_id]
                    diagram_id = diagram_meta['path']
                    break
            
            if not person_data:
                return PersonResult(
                    success=False,
                    error=f"Person {person_id} not found"
                )
            
            # Initialize the model
            api_key_id = person_data.get('apiKeyId')
            if not api_key_id:
                return PersonResult(
                    success=False,
                    error=f"Person {person_id} has no API key configured"
                )
            
            # Warm up the model by making a simple call
            service_str = context.api_key_service.get_api_key(api_key_id)['service']
            model = person_data.get('model', person_data.get('modelName', 'gpt-4o-mini'))
            
            # Make a simple test call to warm up the model
            result = await llm_service.get_completion(
                prompt="Say 'initialized'",
                model=model,
                service=service_str,
                api_key_id=api_key_id,
                max_tokens=10
            )
            
            # Map service using Pydantic enum
            try:
                service = LLMService(service_str.lower())
            except ValueError:
                service = LLMService.openai
            
            # Map forgetting mode using Pydantic enum
            try:
                forgetting_mode = ForgettingMode(person_data.get('forgettingMode', 'none'))
            except ValueError:
                forgetting_mode = ForgettingMode.no_forget
            
            # Create Pydantic model for response
            person = DomainPerson(
                id=person_id,
                label=person_data.get('label', ''),
                service=service,
                model=model,
                api_key_id=api_key_id,
                systemPrompt=person_data.get('systemPrompt', ''),
                forgettingMode=forgetting_mode,
                type=person_data.get('type', 'person')
            )
            
            return PersonResult(
                success=True,
                person=person,  # Strawberry will handle conversion
                message=f"Model {model} initialized successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            return PersonResult(
                success=False,
                error=f"Failed to initialize model: {str(e)}"
            )