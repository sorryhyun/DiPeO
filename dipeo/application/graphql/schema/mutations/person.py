"""Person mutations using ServiceRegistry."""

import logging
from uuid import uuid4

import strawberry

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import PERSON_MANAGER
from dipeo.diagram_generated import DomainPerson
from dipeo.diagram_generated.domain_models import PersonLLMConfig, PersonID, LLMService, ApiKeyID

from ...types.inputs import CreatePersonInput, UpdatePersonInput
from ...types.results import PersonResult, DeleteResult

logger = logging.getLogger(__name__)


def create_person_mutations(registry: ServiceRegistry) -> type:
    """Create person mutation methods with injected service registry."""
    
    @strawberry.type
    class PersonMutations:
        @strawberry.mutation
        async def create_person(self, input: CreatePersonInput) -> PersonResult:
            try:
                person_manager = registry.resolve(PERSON_MANAGER)
                
                # Create LLM config from input
                llm_config = PersonLLMConfig(
                    service=input.llm_config.service,
                    model=input.llm_config.model,
                    api_key_id=input.llm_config.api_key_id,
                    system_prompt=input.llm_config.system_prompt,
                )
                
                # Create person
                person_id = PersonID(f"person_{uuid4().hex[:8]}")
                
                # Use get_or_create_person to create the person
                person_manager.get_or_create_person(
                    person_id=person_id,
                    name=input.label,
                    llm_config=llm_config
                )
                
                # Create DomainPerson for GraphQL response
                person = DomainPerson(
                    id=person_id,
                    label=input.label,
                    llm_config=llm_config,
                    type="person"  # This is a literal type
                )
                
                return PersonResult(
                    success=True,
                    person=person,
                    message=f"Created person: {person.label}",
                )
                
            except Exception as e:
                logger.error(f"Failed to create person: {e}")
                return PersonResult(
                    success=False,
                    error=f"Failed to create person: {str(e)}",
                )
        
        @strawberry.mutation
        async def update_person(
            self, id: strawberry.ID, input: UpdatePersonInput
        ) -> PersonResult:
            try:
                person_id = PersonID(str(id))
                person_manager = registry.resolve(PERSON_MANAGER)
                
                # Try to get existing person
                try:
                    existing_person = person_manager.get_person(person_id)
                    existing_label = existing_person.name
                    existing_llm_config = existing_person.llm_config
                except (KeyError, Exception):
                    # Person doesn't exist, we'll create it
                    existing_person = None
                    existing_label = "Unknown Person"
                    existing_llm_config = PersonLLMConfig(
                        service=LLMService("openai"),
                        model="gpt-5-nano-2025-08-07",
                        api_key_id=ApiKeyID("default"),
                        system_prompt="",
                    )
                
                # Prepare updated values
                updated_label = input.label if input.label else existing_label
                
                if input.llm_config:
                    # Update LLM config fields
                    updated_llm_config = PersonLLMConfig(
                        service=input.llm_config.service if input.llm_config.service else existing_llm_config.service,
                        model=input.llm_config.model if input.llm_config.model else existing_llm_config.model,
                        api_key_id=input.llm_config.api_key_id if input.llm_config.api_key_id else existing_llm_config.api_key_id,
                        system_prompt=input.llm_config.system_prompt if input.llm_config.system_prompt is not None else existing_llm_config.system_prompt,
                    )
                else:
                    updated_llm_config = existing_llm_config
                
                # Use get_or_create_person which will either get or create
                # For updates, we'll use register_person for backward compatibility
                if existing_person:
                    # Update using register_person (backward compatibility method)
                    person_manager.register_person(
                        person_id=str(person_id),
                        config={
                            'name': updated_label,
                            'service': updated_llm_config.service,
                            'model': updated_llm_config.model,
                            'api_key_id': updated_llm_config.api_key_id,
                        }
                    )
                else:
                    # Create new person
                    person_manager.get_or_create_person(
                        person_id=person_id,
                        name=updated_label,
                        llm_config=updated_llm_config
                    )
                
                # Create DomainPerson for response
                updated_person = DomainPerson(
                    id=person_id,
                    label=updated_label,
                    llm_config=updated_llm_config,
                    type="person"  # This is a literal type
                )
                
                return PersonResult(
                    success=True,
                    person=updated_person,
                    message=f"Updated person: {updated_label}",
                )
                
            except Exception as e:
                logger.error(f"Failed to update person {id}: {e}")
                return PersonResult(
                    success=False,
                    error=f"Failed to update person: {str(e)}",
                )
        
        @strawberry.mutation
        async def delete_person(self, id: strawberry.ID) -> DeleteResult:
            try:
                person_id = PersonID(str(id))
                # Since ExecutionOrchestrator doesn't have delete, 
                # we'll need to access the repository directly
                # For now, return an error indicating this operation is not supported
                logger.warning(f"Delete person operation not supported in current architecture for person {person_id}")
                
                return DeleteResult(
                    success=False,
                    error="Delete operation not currently supported. Persons are managed through execution context.",
                )
                
            except Exception as e:
                logger.error(f"Failed to delete person {id}: {e}")
                return DeleteResult(
                    success=False,
                    error=f"Failed to delete person: {str(e)}",
                )
    
    return PersonMutations