"""Person mutations using UnifiedServiceRegistry."""

import logging
from uuid import uuid4

import strawberry

from dipeo.application.unified_service_registry import UnifiedServiceRegistry, ServiceKey
from dipeo.core.dynamic import PersonManager
from dipeo.diagram_generated import DomainPerson
from dipeo.diagram_generated.domain_models import PersonLLMConfig, PersonID

from ...types.inputs import CreatePersonInput, UpdatePersonInput
from ...types.results import PersonResult, DeleteResult

logger = logging.getLogger(__name__)

# Service keys
PERSON_MANAGER = ServiceKey[PersonManager]("person_manager")


def create_person_mutations(registry: UnifiedServiceRegistry) -> type:
    """Create person mutation methods with injected service registry."""
    
    @strawberry.type
    class PersonMutations:
        @strawberry.mutation
        async def create_person(self, input: CreatePersonInput) -> PersonResult:
            try:
                person_manager = registry.require(PERSON_MANAGER)
                
                # Create LLM config from input
                llm_config = PersonLLMConfig(
                    service=input.llm_config.service,
                    model=input.llm_config.model,
                    api_key_id=input.llm_config.api_key_id,
                    system_prompt=input.llm_config.system_prompt,
                )
                
                # Create person
                person_id = f"person_{uuid4().hex[:8]}"
                person = DomainPerson(
                    id=person_id,
                    label=input.label,
                    llm_config=llm_config,
                    type=input.type,
                )
                
                # Add to manager
                await person_manager.create_person(person_id=person_id,
                                                   name=input.label,
                                                   llm_config=llm_config)
                
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
                person_manager = registry.require(PERSON_MANAGER)
                
                # Get existing person
                persons = await person_manager.get_all_persons()
                existing_person = None
                for person in persons:
                    if person.id == person_id:
                        existing_person = person
                        break
                
                if not existing_person:
                    raise ValueError(f"Person not found: {person_id}")
                
                # Update fields
                updated_person = DomainPerson(
                    id=existing_person.id,
                    label=input.label or existing_person.label,
                    llm_config=PersonLLMConfig(
                        service=input.llm_config.service if input.llm_config else existing_person.llm_config.service,
                        model=input.llm_config.model if input.llm_config else existing_person.llm_config.model,
                        api_key_id=input.llm_config.api_key_id if input.llm_config else existing_person.llm_config.api_key_id,
                        system_prompt=input.llm_config.system_prompt if input.llm_config else existing_person.llm_config.system_prompt,
                    ) if input.llm_config else existing_person.llm_config,
                    type=existing_person.type,
                )
                
                # Update in manager
                await person_manager.update_person_config(updated_person)
                
                return PersonResult(
                    success=True,
                    person=updated_person,
                    message=f"Updated person: {updated_person.label}",
                )
                
            except Exception as e:
                logger.error(f"Failed to update person {person_id}: {e}")
                return PersonResult(
                    success=False,
                    error=f"Failed to update person: {str(e)}",
                )
        
        @strawberry.mutation
        async def delete_person(self, id: strawberry.ID) -> DeleteResult:
            try:
                person_id = PersonID(str(id))
                person_manager = registry.require(PERSON_MANAGER)
                
                # Remove from manager
                await person_manager.remove_person(person_id)
                
                return DeleteResult(
                    success=True,
                    deleted_id=str(person_id),
                    message=f"Deleted person: {person_id}",
                )
                
            except Exception as e:
                logger.error(f"Failed to delete person {person_id}: {e}")
                return DeleteResult(
                    success=False,
                    error=f"Failed to delete person: {str(e)}",
                )
    
    return PersonMutations