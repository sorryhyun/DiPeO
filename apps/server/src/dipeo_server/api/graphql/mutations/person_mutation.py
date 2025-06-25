"""GraphQL mutations for person (LLM agent) management."""

import logging
import uuid

import strawberry
from dipeo_domain import DomainPerson, LLMService, PersonID as DomainPersonID
from ..context import GraphQLContext
from ..types import (
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
    """Handles person/LLM agent CRUD operations."""

    @strawberry.mutation
    async def create_person(
        self,
        diagram_id: DiagramID,
        person_input: CreatePersonInput,
        info: strawberry.Info[GraphQLContext],
    ) -> PersonResult:
        """Creates a new person (LLM agent) in diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_storage_service

            # Use input directly without conversion

            diagram_data = await diagram_service.read_file(diagram_id)
            if not diagram_data:
                return PersonResult(success=False, error="Diagram not found")

            person_id = f"person_{str(uuid.uuid4())[:8]}"

            person = DomainPerson(
                id=DomainPersonID(person_id),
                label=person_input.label,
                service=person_input.service,
                model=person_input.model,
                apiKeyId=person_input.api_key_id,
                systemPrompt=person_input.system_prompt or "",
                type="person",
            )

            person_data = person.model_dump()
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
                person=person,  # Strawberry will handle conversion
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
        """Updates person configuration and properties."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_storage_service

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

            if person_input.label is not None:
                person_data["label"] = person_input.label
            if person_input.model is not None:
                person_data["model"] = person_input.model
            if person_input.api_key_id is not None:
                person_data["apiKeyId"] = person_input.api_key_id
            if person_input.system_prompt is not None:
                person_data["systemPrompt"] = person_input.system_prompt
            if person_input.temperature is not None:
                person_data["temperature"] = person_input.temperature
            if person_input.max_tokens is not None:
                person_data["maxTokens"] = person_input.max_tokens
            if person_input.top_p is not None:
                person_data["topP"] = person_input.top_p

            try:
                service = LLMService(person_data["service"].lower())
            except ValueError:
                service = LLMService.openai

            updated_person = DomainPerson(
                id=person_input.id,
                label=person_data["label"],
                service=service,
                model=person_data.get("model", person_data.get("modelName", "gpt-4")),
                apiKeyId=person_data.get("apiKeyId", ""),
                systemPrompt=person_data.get("systemPrompt", ""),
                type=person_data.get("type", "person"),
            )

            person_dict = updated_person.model_dump()
            person_dict.update(
                {
                    "temperature": person_data.get("temperature"),
                    "maxTokens": person_data.get("maxTokens"),
                    "topP": person_data.get("topP"),
                }
            )
            diagram_data["persons"][person_input.id] = person_dict

            # Save updated diagram
            await diagram_service.write_file(diagram_id, diagram_data)

            return PersonResult(
                success=True,
                person=updated_person,  # Strawberry will handle conversion
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
        """Removes person and updates referencing nodes."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_storage_service

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
        self, info: strawberry.Info[GraphQLContext], person_id: PersonID
    ) -> PersonResult:
        """Warms up model for faster first execution."""
        try:
            context: GraphQLContext = info.context
            llm_service = context.llm_service
            diagram_service = context.diagram_storage_service

            person_data = None

            diagrams = await diagram_service.list_files()
            for diagram_meta in diagrams:
                diagram = await diagram_service.read_file(diagram_meta.path)
                if person_id in diagram.get("persons", {}):
                    person_data = diagram["persons"][person_id]
                    break

            if not person_data:
                return PersonResult(
                    success=False, error=f"Person {person_id} not found"
                )

            api_key_id = person_data.get("apiKeyId")
            if not api_key_id:
                return PersonResult(
                    success=False, error=f"Person {person_id} has no API key configured"
                )

            service_str = context.api_key_service.get_api_key(api_key_id)["service"]
            model = person_data.get(
                "model", person_data.get("modelName", "gpt-4o-mini")
            )

            # Initialize the model by making a simple call
            messages = [
                {"role": "user", "content": "Say 'initialized'", "personId": person_id}
            ]
            await llm_service.call_llm(
                service=service_str,
                api_key_id=api_key_id,
                model=model,
                messages=messages,
                system_prompt="",
            )

            try:
                service = LLMService(service_str.lower())
            except ValueError:
                service = LLMService.openai

            person = DomainPerson(
                id=person_id,
                label=person_data.get("label", ""),
                service=service,
                model=model,
                apiKeyId=api_key_id,
                systemPrompt=person_data.get("systemPrompt", ""),
                type=person_data.get("type", "person"),
            )

            return PersonResult(
                success=True,
                person=person,  # Strawberry will handle conversion
                message=f"Model {model} initialized successfully",
            )

        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            return PersonResult(
                success=False, error=f"Failed to initialize model: {e!s}"
            )

    @strawberry.mutation
    async def clear_conversations(self, info: strawberry.Info) -> DeleteResult:
        """Clear all conversation history for all persons."""
        try:
            context: GraphQLContext = info.context
            memory_service = context.memory_service

            # Clear all conversations
            memory_service.clear_all_conversations()

            return DeleteResult(success=True, message="All conversations cleared")

        except Exception as e:
            logger.error(f"Failed to clear conversations: {e}")
            return DeleteResult(
                success=False, error=f"Failed to clear conversations: {e!s}"
            )
