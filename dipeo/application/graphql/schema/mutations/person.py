"""Person mutations using ServiceRegistry."""

import logging
from uuid import uuid4

import strawberry

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import EXECUTION_ORCHESTRATOR
from dipeo.diagram_generated import DomainPerson
from dipeo.diagram_generated.domain_models import ApiKeyID, LLMService, PersonID, PersonLLMConfig
from dipeo.diagram_generated.graphql.inputs import CreatePersonInput, UpdatePersonInput
from dipeo.diagram_generated.graphql.results import DeleteResult, PersonResult

logger = logging.getLogger(__name__)


# Standalone resolver functions for operation executor
async def create_person(input: CreatePersonInput, registry: ServiceRegistry = None) -> PersonResult:
    """Create a new person."""
    try:
        execution_orchestrator = registry.resolve(EXECUTION_ORCHESTRATOR)

        llm_config = PersonLLMConfig(
            service=input.llm_config.service,
            model=input.llm_config.model,
            api_key_id=input.llm_config.api_key_id,
            system_prompt=input.llm_config.system_prompt,
        )

        # Create person
        person_id = PersonID(f"person_{uuid4().hex[:8]}")

        # Use get_or_create_person to create the person
        execution_orchestrator.get_or_create_person(
            person_id=person_id, name=input.label, llm_config=llm_config
        )

        # Create DomainPerson for GraphQL response
        person = DomainPerson(
            id=person_id,
            label=input.label,
            llm_config=llm_config,
            type="person",
        )

        return PersonResult.success_result(data=person, message=f"Created person: {person.label}")

    except Exception as e:
        logger.error(f"Failed to create person: {e}")
        return PersonResult.error_result(error=f"Failed to create person: {e!s}")


async def update_person(
    person_id: strawberry.ID, input: UpdatePersonInput, registry: ServiceRegistry = None
) -> PersonResult:
    """Update an existing person."""
    try:
        person_id_typed = PersonID(str(person_id))
        execution_orchestrator = registry.resolve(EXECUTION_ORCHESTRATOR)

        # Try to get existing person
        try:
            existing_person = execution_orchestrator.get_person(person_id_typed)
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
                service=input.llm_config.service
                if input.llm_config.service
                else existing_llm_config.service,
                model=input.llm_config.model
                if input.llm_config.model
                else existing_llm_config.model,
                api_key_id=input.llm_config.api_key_id
                if input.llm_config.api_key_id
                else existing_llm_config.api_key_id,
                system_prompt=input.llm_config.system_prompt
                if input.llm_config.system_prompt is not None
                else existing_llm_config.system_prompt,
            )
        else:
            updated_llm_config = existing_llm_config

        # Use get_or_create_person which will either get or create
        # For updates, we'll use register_person for backward compatibility
        if existing_person:
            # Update using register_person (backward compatibility method)
            execution_orchestrator.register_person(
                person_id=str(person_id_typed),
                config={
                    "name": updated_label,
                    "service": updated_llm_config.service,
                    "model": updated_llm_config.model,
                    "api_key_id": updated_llm_config.api_key_id,
                },
            )
        else:
            # Create new person
            execution_orchestrator.get_or_create_person(
                person_id=person_id, name=updated_label, llm_config=updated_llm_config
            )

        # Create DomainPerson for response
        updated_person = DomainPerson(
            id=person_id_typed,
            label=updated_label,
            llm_config=updated_llm_config,
            type="person",
        )

        return PersonResult.success_result(
            data=updated_person, message=f"Updated person: {updated_label}"
        )

    except Exception as e:
        logger.error(f"Failed to update person {person_id}: {e}")
        return PersonResult.error_result(error=f"Failed to update person: {e!s}")


async def delete_person(person_id: strawberry.ID, registry: ServiceRegistry = None) -> DeleteResult:
    """Delete a person (not currently supported)."""
    try:
        person_id_typed = PersonID(str(person_id))
        # Since ExecutionOrchestrator doesn't have delete,
        # we'll need to access the repository directly
        # For now, return an error indicating this operation is not supported
        logger.warning(
            f"Delete person operation not supported in current architecture for person {person_id_typed}"
        )

        return DeleteResult.error_result(
            error="Delete operation not currently supported. Persons are managed through execution context."
        )

    except Exception as e:
        logger.error(f"Failed to delete person {person_id}: {e}")
        return DeleteResult.error_result(error=f"Failed to delete person: {e!s}")


def create_person_mutations(registry: ServiceRegistry) -> type:
    """Create person mutation methods with injected registry."""

    @strawberry.type
    class PersonMutations:
        @strawberry.mutation
        async def create_person(self, input: CreatePersonInput) -> PersonResult:
            try:
                execution_orchestrator = registry.resolve(EXECUTION_ORCHESTRATOR)

                llm_config = PersonLLMConfig(
                    service=input.llm_config.service,
                    model=input.llm_config.model,
                    api_key_id=input.llm_config.api_key_id,
                    system_prompt=input.llm_config.system_prompt,
                )

                # Create person
                person_id = PersonID(f"person_{uuid4().hex[:8]}")

                # Use get_or_create_person to create the person
                execution_orchestrator.get_or_create_person(
                    person_id=person_id, name=input.label, llm_config=llm_config
                )

                # Create DomainPerson for GraphQL response
                person = DomainPerson(
                    id=person_id,
                    label=input.label,
                    llm_config=llm_config,
                    type="person",
                )

                return PersonResult.success_result(
                    data=person, message=f"Created person: {person.label}"
                )

            except Exception as e:
                logger.error(f"Failed to create person: {e}")
                return PersonResult.error_result(error=f"Failed to create person: {e!s}")

        @strawberry.mutation
        async def update_person(
            self, person_id: strawberry.ID, input: UpdatePersonInput
        ) -> PersonResult:
            try:
                person_id_typed = PersonID(str(person_id))
                execution_orchestrator = registry.resolve(EXECUTION_ORCHESTRATOR)

                # Try to get existing person
                try:
                    existing_person = execution_orchestrator.get_person(person_id_typed)
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
                        service=input.llm_config.service
                        if input.llm_config.service
                        else existing_llm_config.service,
                        model=input.llm_config.model
                        if input.llm_config.model
                        else existing_llm_config.model,
                        api_key_id=input.llm_config.api_key_id
                        if input.llm_config.api_key_id
                        else existing_llm_config.api_key_id,
                        system_prompt=input.llm_config.system_prompt
                        if input.llm_config.system_prompt is not None
                        else existing_llm_config.system_prompt,
                    )
                else:
                    updated_llm_config = existing_llm_config

                # Use get_or_create_person which will either get or create
                # For updates, we'll use register_person for backward compatibility
                if existing_person:
                    # Update using register_person (backward compatibility method)
                    execution_orchestrator.register_person(
                        person_id=str(person_id_typed),
                        config={
                            "name": updated_label,
                            "service": updated_llm_config.service,
                            "model": updated_llm_config.model,
                            "api_key_id": updated_llm_config.api_key_id,
                        },
                    )
                else:
                    # Create new person
                    execution_orchestrator.get_or_create_person(
                        person_id=person_id, name=updated_label, llm_config=updated_llm_config
                    )

                # Create DomainPerson for response
                updated_person = DomainPerson(
                    id=person_id_typed,
                    label=updated_label,
                    llm_config=updated_llm_config,
                    type="person",
                )

                return PersonResult.success_result(
                    data=updated_person, message=f"Updated person: {updated_label}"
                )

            except Exception as e:
                logger.error(f"Failed to update person {person_id}: {e}")
                return PersonResult.error_result(error=f"Failed to update person: {e!s}")

        @strawberry.mutation
        async def delete_person(self, person_id: strawberry.ID) -> DeleteResult:
            try:
                person_id_typed = PersonID(str(person_id))
                # Since ExecutionOrchestrator doesn't have delete,
                # we'll need to access the repository directly
                # For now, return an error indicating this operation is not supported
                logger.warning(
                    f"Delete person operation not supported in current architecture for person {person_id_typed}"
                )

                return DeleteResult.error_result(
                    error="Delete operation not currently supported. Persons are managed through execution context."
                )

            except Exception as e:
                logger.error(f"Failed to delete person {person_id}: {e}")
                return DeleteResult.error_result(error=f"Failed to delete person: {e!s}")

    return PersonMutations
