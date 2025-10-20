"""Person-related query resolvers."""

import logging

import strawberry

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import DIAGRAM_PORT
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.domain_models import PersonID, PersonLLMConfig
from dipeo.diagram_generated.graphql.domain_types import DomainPersonType

logger = get_module_logger(__name__)


async def get_person(
    registry: ServiceRegistry, person_id: strawberry.ID
) -> DomainPersonType | None:
    """Get a single person by ID."""
    try:
        integrated_service = registry.resolve(DIAGRAM_PORT)
        if not integrated_service:
            logger.warning("Integrated diagram service not available")
            return None

        diagram_infos = await integrated_service.list_diagrams()
        person_id_typed = PersonID(str(person_id))

        for diagram_info in diagram_infos:
            path = diagram_info.get("path", "")
            diagram_id = path.split(".")[0] if path else diagram_info.get("id")

            diagram_dict = await integrated_service.get_diagram(diagram_id)
            if not diagram_dict:
                continue

            persons = diagram_dict.get("persons", {})
            if str(person_id_typed) in persons:
                person_data = persons[str(person_id_typed)]
                return DomainPersonType(
                    id=person_id_typed,
                    label=person_data.get("name", ""),
                    llm_config=PersonLLMConfig(
                        service=person_data.get("service", "openai"),
                        model=person_data.get("modelName", "gpt-4.1-nano"),
                        api_key_id=person_data.get("apiKeyId", ""),
                        system_prompt=person_data.get("systemPrompt", ""),
                    ),
                    type="person",
                )

        return None

    except Exception as e:
        logger.error(f"Error fetching person {person_id}: {e}")
        return None


async def list_persons(registry: ServiceRegistry, limit: int = 100) -> list[DomainPersonType]:
    """List all persons."""
    try:
        integrated_service = registry.resolve(DIAGRAM_PORT)
        if not integrated_service:
            logger.warning("Integrated diagram service not available")
            return []

        all_persons = {}
        diagram_infos = await integrated_service.list_diagrams()

        for diagram_info in diagram_infos:
            path = diagram_info.get("path", "")
            diagram_id = path.split(".")[0] if path else diagram_info.get("id")

            diagram_dict = await integrated_service.get_diagram(diagram_id)
            if not diagram_dict:
                continue

            persons = diagram_dict.get("persons", {})
            for person_id, person_data in persons.items():
                if person_id not in all_persons:
                    all_persons[person_id] = DomainPersonType(
                        id=PersonID(person_id),
                        label=person_data.get("name", ""),
                        llm_config=PersonLLMConfig(
                            service=person_data.get("service", "openai"),
                            model=person_data.get("modelName", "gpt-4.1-nano"),
                            api_key_id=person_data.get("apiKeyId", ""),
                            system_prompt=person_data.get("systemPrompt", ""),
                        ),
                        type="person",
                    )

        domain_persons = list(all_persons.values())
        return domain_persons[:limit]

    except Exception as e:
        logger.error(f"Error listing persons: {e}")
        return []
