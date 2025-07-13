"""GraphQL mutations for person (LLM agent) management."""

import logging
import uuid

import strawberry
from dipeo.models import DomainPerson, LLMService
from dipeo.models import PersonLLMConfig
from dipeo.models import PersonID as DomainPersonID

from ..context import GraphQLContext
from ..types import (
    ApiKeyID,
    CreatePersonInput,
    DeleteResult,
    DiagramID,
    PersonID,
    PersonResult,
    UpdatePersonInput,
)

logger = logging.getLogger(__name__)


@strawberry.type
class PersonMutations:
    # Handles person/LLM agent CRUD operations

    @strawberry.mutation
    async def create_person(
        self,
        diagram_id: DiagramID,
        person_input: CreatePersonInput,
        info: strawberry.Info[GraphQLContext],
    ) -> PersonResult:
        try:
            context: GraphQLContext = info.context
            diagram_service = context.get_service("diagram_storage_domain_service")

            # Use input directly without conversion

            diagram_data = await diagram_service.read_file(diagram_id)
            if not diagram_data:
                return PersonResult(success=False, error="Diagram not found")

            person_id = f"person_{str(uuid.uuid4())[:8]}"

            person = DomainPerson(
                id=DomainPersonID(person_id),
                label=person_input.label,
                llm_config=PersonLLMConfig(  # Use snake_case for field name
                    service=person_input.service,
                    model=person_input.model,
                    api_key_id=person_input.api_key_id,  # Use snake_case
                    system_prompt=person_input.system_prompt or "",
                ),
                type="person",
            )

            # Use mode='json' to serialize enums as values
            person_data = person.model_dump(mode="json")

            person_data.update(
                {
                    "temperature": getattr(person_input, "temperature", 0.7),
                    "maxTokens": getattr(person_input, "max_tokens", 1000),
                    "topP": getattr(person_input, "top_p", 1.0),
                }
            )

            if "persons" not in diagram_data:
                diagram_data["persons"] = {}
            diagram_data["persons"][person_id] = person_data

            # Save updated diagram
            await diagram_service.write_file(diagram_id, diagram_data)

            return PersonResult(
                success=True,
                person=person,
                message=f"Created person {person_id}",
            )

        except ValueError as e:
            logger.error(f"Validation error creating person: {e}")
            return PersonResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            logger.error(f"Failed to create person: {e}")
            return PersonResult(success=False, error=f"Failed to create person: {e!s}")

    @strawberry.mutation
    async def update_person(
        self, person_input: UpdatePersonInput, info: strawberry.Info[GraphQLContext]
    ) -> PersonResult:
        try:
            context: GraphQLContext = info.context
            diagram_service = context.get_service("diagram_storage_domain_service")

            # Use input directly without conversion

            diagrams = await diagram_service.list_files()
            diagram_id = None
            diagram_data = None

            for diagram_meta in diagrams:
                temp_diagram = await diagram_service.read_file(diagram_meta.path)
                if person_input.id in temp_diagram.get("persons", {}):
                    diagram_id = diagram_meta.path
                    diagram_data = temp_diagram
                    break

            if not diagram_data:
                return PersonResult(
                    success=False,
                    error=f"Person {person_input.id} not found in any diagram",
                )

            person_data = diagram_data["persons"][person_input.id]

            # Handle both flat and nested llmConfig structures
            # Get existing values with fallbacks for different formats
            existing_service = person_data.get("service") or person_data.get(
                "llmConfig", {}
            ).get("service", "openai")
            existing_api_key = (
                person_data.get("api_key_id")
                or person_data.get("apiKeyId")
                or person_data.get("llmConfig", {}).get("apiKeyId", "")
            )
            existing_model = (
                person_data.get("model")
                or person_data.get("modelName")
                or person_data.get("llmConfig", {}).get("model", "gpt-4")
            )
            existing_system_prompt = (
                person_data.get("system_prompt")
                or person_data.get("systemPrompt")
                or person_data.get("llmConfig", {}).get("systemPrompt", "")
            )

            if person_input.label is not None:
                person_data["label"] = person_input.label
            if person_input.model is not None:
                # If model is empty string or null, remove it so it can be re-selected
                if person_input.model:
                    person_data["model"] = person_input.model
                else:
                    # Clear the model field
                    person_data.pop("model", None)
                    person_data.pop("modelName", None)
            if person_input.api_key_id is not None:
                person_data["api_key_id"] = person_input.api_key_id
                person_data["apiKeyId"] = (
                    person_input.api_key_id
                )  # Support both formats
            if person_input.system_prompt is not None:
                person_data["system_prompt"] = person_input.system_prompt
                person_data["systemPrompt"] = (
                    person_input.system_prompt
                )  # Support both formats
            if person_input.temperature is not None:
                person_data["temperature"] = person_input.temperature
            if person_input.max_tokens is not None:
                person_data["maxTokens"] = person_input.max_tokens
                person_data["max_tokens"] = (
                    person_input.max_tokens
                )  # Support both formats
            if person_input.top_p is not None:
                person_data["topP"] = person_input.top_p
                person_data["top_p"] = person_input.top_p  # Support both formats

            # Ensure service field exists
            if "service" not in person_data:
                person_data["service"] = existing_service

            try:
                service = LLMService(
                    person_data.get("service", existing_service).lower()
                )
            except (ValueError, AttributeError):
                service = LLMService.openai

            # Get the current API key ID - check all possible field names
            current_api_key_id = (
                person_data.get("api_key_id")
                or person_data.get("apiKeyId")
                or person_data.get("llmConfig", {}).get("apiKeyId")
                or person_data.get("llmConfig", {}).get("api_key_id")
                or existing_api_key
            )

            if not current_api_key_id:
                return PersonResult(
                    success=False,
                    error="API key ID is required for person configuration",
                )

            updated_person = DomainPerson(
                id=person_input.id,
                label=person_data["label"],
                llm_config=PersonLLMConfig(  # Use snake_case for field name
                    service=service,
                    model=person_data.get("model")
                    or person_data.get("modelName")
                    or existing_model
                    or "gpt-4",  # Default to gpt-4 if no model
                    api_key_id=current_api_key_id,  # Use snake_case as expected by the model
                    system_prompt=person_data.get("system_prompt")
                    or person_data.get("systemPrompt")
                    or existing_system_prompt,
                ),
                type=person_data.get("type", "person"),
            )

            # Use mode='json' to serialize enums as values
            person_dict = updated_person.model_dump(mode="json")

            # Store additional fields for backward compatibility
            person_dict.update(
                {
                    "temperature": person_data.get("temperature"),
                    "maxTokens": person_data.get("maxTokens"),
                    "topP": person_data.get("topP"),
                    "api_key_id": current_api_key_id,
                    "apiKeyId": current_api_key_id,
                }
            )
            diagram_data["persons"][person_input.id] = person_dict

            # Save updated diagram
            await diagram_service.write_file(diagram_id, diagram_data)

            return PersonResult(
                success=True,
                person=updated_person,
                message=f"Updated person {person_input.id}",
            )

        except ValueError as e:
            # Pydantic validation error
            logger.error(f"Validation error updating person: {e}")
            return PersonResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            logger.error(f"Failed to update person: {e}")
            return PersonResult(success=False, error=f"Failed to update person: {e!s}")

    @strawberry.mutation
    async def delete_person(
        self, person_id: PersonID, info: strawberry.Info[GraphQLContext]
    ) -> DeleteResult:
        try:
            context: GraphQLContext = info.context
            diagram_service = context.get_service("diagram_storage_domain_service")

            diagrams = await diagram_service.list_files()
            diagram_id = None
            diagram_data = None

            for diagram_meta in diagrams:
                temp_diagram = await diagram_service.read_file(diagram_meta.path)
                if person_id in temp_diagram.get("persons", {}):
                    diagram_id = diagram_meta.path
                    diagram_data = temp_diagram
                    break

            if not diagram_data:
                return DeleteResult(
                    success=False, error=f"Person {person_id} not found in any diagram"
                )

            del diagram_data["persons"][person_id]

            nodes_updated = 0
            for node in diagram_data.get("nodes", {}).values():
                if node.get("data", {}).get("personId") == person_id:
                    del node["data"]["personId"]
                    nodes_updated += 1

            # Save updated diagram
            await diagram_service.write_file(diagram_id, diagram_data)

            return DeleteResult(
                success=True,
                deleted_id=person_id,
                message=f"Deleted person {person_id} and updated {nodes_updated} nodes",
            )

        except Exception as e:
            logger.error(f"Failed to delete person {person_id}: {e}")
            return DeleteResult(success=False, error=f"Failed to delete person: {e!s}")

    @strawberry.mutation
    async def initialize_model(
        self,
        info: strawberry.Info[GraphQLContext],
        person_id: PersonID,
        api_key_id: ApiKeyID,
        model: str,
        label: str = "",
    ) -> PersonResult:
        try:
            context: GraphQLContext = info.context
            llm_service = context.get_service("llm_service")

            # Validate API key exists
            try:
                api_key_data = context.get_service("api_key_service").get_api_key(api_key_id)
                service_str = api_key_data["service"]
            except Exception:
                return PersonResult(
                    success=False, error=f"API key {api_key_id} not found"
                )

            # Initialize the model by making a simple call
            messages = [{"role": "user", "content": "Say 'initialized'"}]
            await llm_service.complete(
                messages=messages,
                model=model,
                api_key_id=api_key_id,
            )

            try:
                service = LLMService(service_str.lower())
            except ValueError:
                service = LLMService.openai

            person = DomainPerson(
                id=person_id,
                label=label,
                llm_config=PersonLLMConfig(
                    service=service,
                    model=model,
                    api_key_id=api_key_id,
                    system_prompt="",
                ),
                type="person",
            )

            return PersonResult(
                success=True,
                person=person,
                message=f"Model {model} initialized successfully",
            )

        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            return PersonResult(
                success=False, error=f"Failed to initialize model: {e!s}"
            )

    @strawberry.mutation
    async def clear_conversations(self, info: strawberry.Info) -> DeleteResult:
        try:
            context: GraphQLContext = info.context
            conversation_service = context.get_service("conversation_service")

            # Clear all conversations
            conversation_service.clear_all_conversations()

            return DeleteResult(success=True, message="All conversations cleared")

        except Exception as e:
            logger.error(f"Failed to clear conversations: {e}")
            return DeleteResult(
                success=False, error=f"Failed to clear conversations: {e!s}"
            )
