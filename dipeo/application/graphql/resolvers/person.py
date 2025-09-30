"""Person and API key resolver using ServiceRegistry."""

import asyncio
import logging

from dipeo.config.base_logger import get_module_logger

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import API_KEY_SERVICE, DIAGRAM_PORT, LLM_SERVICE
from dipeo.diagram_generated.domain_models import (
    ApiKeyID,
    DomainApiKey,
    DomainPerson,
    PersonID,
    PersonLLMConfig,
)

logger = get_module_logger(__name__)

class PersonResolver:
    """Resolver for person and API key related queries using service registry."""

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry

    async def get_person(self, id: PersonID) -> DomainPerson | None:
        try:
            integrated_service = self.registry.resolve(DIAGRAM_PORT)
            if not integrated_service:
                logger.warning("Integrated diagram service not available")
                return None

            diagram_infos = await integrated_service.list_diagrams()

            for diagram_info in diagram_infos:
                path = diagram_info.get("path", "")
                diagram_id = path.split(".")[0] if path else diagram_info.get("id")

                diagram_dict = await integrated_service.get_diagram(diagram_id)
                if not diagram_dict:
                    continue

                persons = diagram_dict.get("persons", {})
                if str(id) in persons:
                    person_data = persons[str(id)]
                    return DomainPerson(
                        id=id,
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
            logger.error(f"Error fetching person {id}: {e}")
            return None

    async def list_persons(self, limit: int = 100) -> list[DomainPerson]:
        try:
            integrated_service = self.registry.resolve(DIAGRAM_PORT)
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
                        all_persons[person_id] = DomainPerson(
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

    async def get_api_key(self, id: ApiKeyID) -> DomainApiKey | None:
        try:
            apikey_service = self.registry.resolve(API_KEY_SERVICE)
            api_keys = await asyncio.to_thread(apikey_service.list_api_keys)
            for key_data in api_keys:
                if key_data.get("id") == str(id):
                    return DomainApiKey(
                        id=key_data["id"],
                        label=key_data["label"],
                        service=key_data["service"],
                        key=key_data.get("key", "***hidden***"),
                    )

            return None

        except Exception as e:
            logger.error(f"Error fetching API key {id}: {e}")
            return None

    async def list_api_keys(self, service: str | None = None) -> list[DomainApiKey]:
        try:
            from dipeo.diagram_generated.enums import APIServiceType

            valid_services = {s.value for s in APIServiceType}

            apikey_service = self.registry.resolve(API_KEY_SERVICE)
            logger.debug(f"Got apikey_service: {apikey_service}")
            api_keys = await asyncio.to_thread(apikey_service.list_api_keys)
            logger.debug(f"Got {len(api_keys)} API keys from service")

            domain_keys = []
            for key_data in api_keys:
                if key_data.get("service") not in valid_services:
                    logger.debug(f"Skipping non-LLM service: {key_data.get('service')}")
                    continue

                if service and key_data.get("service") != service:
                    continue

                domain_keys.append(
                    DomainApiKey(
                        id=key_data["id"],
                        label=key_data["label"],
                        service=key_data["service"],
                        key=key_data.get("key", "***hidden***"),
                    )
                )

            return domain_keys

        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            return []

    async def get_available_models(self, service: str, api_key_id: ApiKeyID) -> list[str]:
        try:
            api_key = await self.get_api_key(api_key_id)
            if not api_key:
                logger.warning(f"API key not found: {api_key_id}")
                return []

            llm_service = self.registry.resolve(LLM_SERVICE)
            models = await llm_service.get_available_models(api_key_id)

            return models

        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
