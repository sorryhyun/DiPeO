"""GraphQL resolvers for person and API key operations."""

import logging

from dipeo_domain import LLMService

from ..context import GraphQLContext
from ..types import (
    ApiKeyID,
    PersonID,
)
from ..types import (
    DomainApiKeyType as DomainApiKey,
)
from ..types import (
    DomainPersonType as DomainPerson,
)

logger = logging.getLogger(__name__)


class PersonResolver:
    """Handles person and API key queries."""

    async def get_person(self, person_id: PersonID, info) -> DomainPerson | None:
        """Returns person by ID."""
        # Persons are diagram-scoped
        logger.warning(
            f"get_person called for {person_id} - persons are diagram-scoped"
        )
        return None

    async def list_persons(self, limit: int, info) -> list[DomainPerson]:
        """Returns person list."""
        # Persons are diagram-scoped
        logger.warning("list_persons called - persons are diagram-scoped")
        return []

    async def get_api_key(self, api_key_id: ApiKeyID, info) -> DomainApiKey | None:
        """Returns API key by ID."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service

            api_key_data = api_key_service.get_api_key(api_key_id)

            if not api_key_data:
                return None

            # Only LLM service keys
            if not self._is_llm_service(api_key_data["service"]):
                logger.debug(
                    f"API key {api_key_id} is for non-LLM service: {api_key_data['service']}"
                )
                return None

            return DomainApiKey(
                id=api_key_data["id"],
                label=api_key_data["label"],
                service=self._map_service(api_key_data["service"]),
            )


        except Exception as e:
            logger.error(f"Failed to get API key {api_key_id}: {e}")
            return None

    async def list_api_keys(self, service: str | None, info) -> list[DomainApiKey]:
        """Returns API key list, optionally filtered."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service

            all_keys = api_key_service.list_api_keys()

            if service:
                all_keys = [k for k in all_keys if k["service"] == service]

            result = []
            for key_data in all_keys:
                # Only LLM service keys
                if self._is_llm_service(key_data["service"]):
                    pydantic_api_key = DomainApiKey(
                        id=key_data["id"],
                        label=key_data["label"],
                        service=self._map_service(key_data["service"]),
                    )
                    result.append(pydantic_api_key)
                else:
                    logger.debug(
                        f"Skipping non-LLM service API key: {key_data['service']}"
                    )

            return result

        except Exception as e:
            logger.error(f"Failed to list API keys: {e}")
            return []

    async def get_available_models(
        self, service: str, api_key_id: ApiKeyID, info
    ) -> list[str]:
        """Returns available models for service/API key."""
        try:
            context: GraphQLContext = info.context
            llm_service = context.llm_service

            return await llm_service.get_available_models(
                service=service, api_key_id=api_key_id
            )


        except Exception as e:
            logger.error(
                f"Failed to get available models for {service}/{api_key_id}: {e}"
            )
            return []

    def _is_llm_service(self, service: str) -> bool:
        """Validates LLM service."""
        try:
            LLMService(service.lower())
            return True
        except ValueError:
            return False

    def _map_service(self, service: str) -> str:
        """Maps service string to enum value."""
        try:
            # Validate that it's a valid LLMService, then return the string value
            enum_value = LLMService(service.lower())
            return enum_value.value
        except ValueError:
            raise ValueError(f"Unknown LLM service: {service}")


person_resolver = PersonResolver()
