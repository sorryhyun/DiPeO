"""Person mutations using ServiceRegistry."""

import logging
from uuid import uuid4

import strawberry

from dipeo.application.registry import ServiceRegistry, ServiceKey
from dipeo.core.dynamic import PersonManager
from dipeo.diagram_generated import DomainPerson
from dipeo.diagram_generated.domain_models import PersonLLMConfig, PersonID

from ...types.inputs import CreatePersonInput, UpdatePersonInput
from ...types.results import PersonResult, DeleteResult

logger = logging.getLogger(__name__)

# Service keys
PERSON_MANAGER = ServiceKey[PersonManager]("person_manager")


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
                person_id = f"person_{uuid4().hex[:8]}"
                person = DomainPerson(
                    id=person_id,
                    label=input.label,
                    llm_config=llm_config,
                    type=input.type,
                )
                
                # Add to manager
                person_manager.create_person(person_id=person_id,
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
                person_manager = registry.resolve(PERSON_MANAGER)
                
                # Check if person exists in manager
                person_exists = person_manager.person_exists(person_id)
                existing_person = None
                
                if person_exists:
                    existing_person = person_manager.get_person(person_id)
                else:
                    logger.debug(f"Person {person_id} not found in manager, will create new entry")
                
                # Create updated person based on input
                if existing_person:
                    # Update existing person
                    updated_label = input.label if input.label else existing_person.name
                    updated_llm_config = existing_person.llm_config
                    
                    if input.llm_config:
                        # Update LLM config fields
                        updated_llm_config = PersonLLMConfig(
                            service=input.llm_config.service if input.llm_config.service else updated_llm_config.service,
                            model=input.llm_config.model if input.llm_config.model else updated_llm_config.model,
                            api_key_id=input.llm_config.api_key_id if input.llm_config.api_key_id else updated_llm_config.api_key_id,
                            system_prompt=input.llm_config.system_prompt if input.llm_config.system_prompt is not None else updated_llm_config.system_prompt,
                        )
                else:
                    # Create new person with provided data
                    updated_label = input.label or "Unknown Person"
                    updated_llm_config = PersonLLMConfig(
                        service=input.llm_config.service if input.llm_config else "openai",
                        model=input.llm_config.model if input.llm_config else "gpt-4.1-nano",
                        api_key_id=input.llm_config.api_key_id if input.llm_config else "",
                        system_prompt=input.llm_config.system_prompt if input.llm_config and input.llm_config.system_prompt is not None else "",
                    )
                
                # Update or create in person manager
                if person_exists:
                    # Update existing person using update_person_config
                    person_manager.update_person_config(
                        person_id=person_id,
                        llm_config=updated_llm_config
                    )
                    # Also update the name by recreating if needed
                    if input.label and existing_person and existing_person.name != updated_label:
                        # Remove and recreate to update name (since update_person_config doesn't update name)
                        person_manager.remove_person(person_id)
                        person_manager.create_person(
                            person_id=person_id,
                            name=updated_label,
                            llm_config=updated_llm_config
                        )
                else:
                    # Create new person
                    person_manager.create_person(
                        person_id=person_id,
                        name=updated_label,
                        llm_config=updated_llm_config
                    )
                
                # Create DomainPerson for response
                updated_person = DomainPerson(
                    id=person_id,
                    label=updated_label,
                    llm_config=updated_llm_config,
                    type="person"
                )
                
                # Note: We're not updating diagrams here - persons exist independently
                # Diagrams will reference persons by ID when needed
                
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
                person_manager = registry.resolve(PERSON_MANAGER)
                
                # Remove from manager
                person_manager.remove_person(person_id)
                
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