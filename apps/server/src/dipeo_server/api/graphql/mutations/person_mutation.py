"""GraphQL mutations for person (LLM agent) management."""

import logging
import uuid

import strawberry
from dipeo_domain import DomainPerson, ForgettingMode, LLMService

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
        input: CreatePersonInput,
        info: strawberry.Info[GraphQLContext],
    ) -> PersonResult:
        """Creates a new person (LLM agent) in diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service

            # Use input directly without conversion

            diagram_data = diagram_service.load_diagram(diagram_id)
            if not diagram_data:
                return PersonResult(success=False, error="Diagram not found")

            person_id = f"person_{str(uuid.uuid4())[:8]}"

            person = DomainPerson(
                id=person_id,
                label=input.label,
                service=input.service,
                model=input.model,
                api_key_id=input.api_key_id,
                systemPrompt=input.system_prompt or "",
                forgettingMode=input.forgetting_mode,
                type="person",
            )

            person_data = person.model_dump()
            person_data.update(
                {
                    "temperature": getattr(input, 'temperature', 0.7),
                    "maxTokens": getattr(input, 'max_tokens', 1000),
                    "topP": getattr(input, 'top_p', 1.0),
                }
            )

            if "persons" not in diagram_data:
                diagram_data["persons"] = {}
            diagram_data["persons"][person_id] = person_data

            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)

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
            return PersonResult(
                success=False, error=f"Failed to create person: {e!s}"
            )

    @strawberry.mutation
    async def update_person(
        self, input: UpdatePersonInput, info: strawberry.Info[GraphQLContext]
    ) -> PersonResult:
        """Updates person configuration and properties."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service

            # Use input directly without conversion

            diagrams = diagram_service.list_diagram_files()
            diagram_id = None
            diagram_data = None

            for diagram_meta in diagrams:
                temp_diagram = diagram_service.load_diagram(diagram_meta["path"])
                if input.id in temp_diagram.get("persons", {}):
                    diagram_id = diagram_meta["path"]
                    diagram_data = temp_diagram
                    break

            if not diagram_data:
                return PersonResult(
                    success=False,
                    error=f"Person {input.id} not found in any diagram",
                )

            person_data = diagram_data["persons"][input.id]

            if input.label is not None:
                person_data["label"] = input.label
            if input.model is not None:
                person_data["model"] = input.model
            if input.api_key_id is not None:
                person_data["apiKeyId"] = input.api_key_id
            if input.system_prompt is not None:
                person_data["systemPrompt"] = input.system_prompt
            if input.forgetting_mode is not None:
                person_data["forgettingMode"] = input.forgetting_mode.value
            if input.temperature is not None:
                person_data["temperature"] = input.temperature
            if input.max_tokens is not None:
                person_data["maxTokens"] = input.max_tokens
            if input.top_p is not None:
                person_data["topP"] = input.top_p

            try:
                service = LLMService(person_data["service"].lower())
            except ValueError:
                service = LLMService.openai

            try:
                forgetting_mode = ForgettingMode(
                    person_data.get("forgettingMode", "none")
                )
            except ValueError:
                forgetting_mode = ForgettingMode.no_forget

            updated_person = DomainPerson(
                id=input.id,
                label=person_data["label"],
                service=service,
                model=person_data.get("model", person_data.get("modelName", "gpt-4")),
                api_key_id=person_data.get("apiKeyId", ""),
                systemPrompt=person_data.get("systemPrompt", ""),
                forgettingMode=forgetting_mode,
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
            diagram_data["persons"][input.id] = person_dict

            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)

            return PersonResult(
                success=True,
                person=updated_person,  # Strawberry will handle conversion
                message=f"Updated person {input.id}",
            )

        except ValueError as e:
            # Pydantic validation error
            logger.error(f"Validation error updating person: {e}")
            return PersonResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            logger.error(f"Failed to update person: {e}")
            return PersonResult(
                success=False, error=f"Failed to update person: {e!s}"
            )

    @strawberry.mutation
    async def delete_person(
        self, id: PersonID, info: strawberry.Info[GraphQLContext]
    ) -> DeleteResult:
        """Removes person and updates referencing nodes."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service

            diagrams = diagram_service.list_diagram_files()
            diagram_id = None
            diagram_data = None

            for diagram_meta in diagrams:
                temp_diagram = diagram_service.load_diagram(diagram_meta["path"])
                if id in temp_diagram.get("persons", {}):
                    diagram_id = diagram_meta["path"]
                    diagram_data = temp_diagram
                    break

            if not diagram_data:
                return DeleteResult(
                    success=False, error=f"Person {id} not found in any diagram"
                )

            del diagram_data["persons"][id]

            nodes_updated = 0
            for node in diagram_data.get("nodes", {}).values():
                if node.get("data", {}).get("personId") == id:
                    del node["data"]["personId"]
                    nodes_updated += 1

            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)

            return DeleteResult(
                success=True,
                deleted_id=id,
                message=f"Deleted person {id} and updated {nodes_updated} nodes",
            )

        except Exception as e:
            logger.error(f"Failed to delete person {id}: {e}")
            return DeleteResult(
                success=False, error=f"Failed to delete person: {e!s}"
            )

    @strawberry.mutation
    async def initialize_model(self, info, person_id: PersonID) -> PersonResult:
        """Warms up model for faster first execution."""
        try:
            context: GraphQLContext = info.context
            llm_service = context.llm_service
            diagram_service = context.diagram_service

            person_data = None
            diagram_id = None

            diagrams = diagram_service.list_diagram_files()
            for diagram_meta in diagrams:
                diagram = diagram_service.load_diagram(diagram_meta["path"])
                if person_id in diagram.get("persons", {}):
                    person_data = diagram["persons"][person_id]
                    diagram_id = diagram_meta["path"]
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

            result = await llm_service.get_completion(
                prompt="Say 'initialized'",
                model=model,
                service=service_str,
                api_key_id=api_key_id,
                max_tokens=10,
            )

            try:
                service = LLMService(service_str.lower())
            except ValueError:
                service = LLMService.openai

            try:
                forgetting_mode = ForgettingMode(
                    person_data.get("forgettingMode", "none")
                )
            except ValueError:
                forgetting_mode = ForgettingMode.no_forget

            person = DomainPerson(
                id=person_id,
                label=person_data.get("label", ""),
                service=service,
                model=model,
                api_key_id=api_key_id,
                systemPrompt=person_data.get("systemPrompt", ""),
                forgettingMode=forgetting_mode,
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
