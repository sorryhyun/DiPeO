"""Refactored person and API key resolvers using Pydantic models."""
from typing import Optional, List
import logging

from .domain_types import DomainPerson, DomainApiKey
from .scalars_types import PersonID, ApiKeyID
from .context import GraphQLContext
from dipeo_server.core import LLMService

logger = logging.getLogger(__name__)

class PersonResolver:
    """Resolver for person and API key related queries."""
    
    async def get_person(self, person_id: PersonID, info) -> Optional[DomainPerson]:
        """Get a single person by ID."""
        # Persons are diagram-scoped, not standalone entities
        logger.warning(f"get_person called for {person_id} - persons are diagram-scoped")
        return None
    
    async def list_persons(self, limit: int, info) -> List[DomainPerson]:
        """List all persons."""
        # Persons are diagram-scoped, not global entities
        logger.warning("list_persons called - persons are diagram-scoped")
        return []
    
    async def get_api_key(self, api_key_id: ApiKeyID, info) -> Optional[DomainApiKey]:
        """Get a single API key by ID."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service
            
            api_key_data = api_key_service.get_api_key(api_key_id)
            
            if not api_key_data:
                return None
            
            pydantic_api_key = DomainApiKey(
                id=api_key_data['id'],
                label=api_key_data['label'],
                service=self._map_service(api_key_data['service'])
            )
            
            return pydantic_api_key
            
        except Exception as e:
            logger.error(f"Failed to get API key {api_key_id}: {e}")
            return None
    
    async def list_api_keys(self, service: Optional[str], info) -> List[DomainApiKey]:
        """List all API keys, optionally filtered by service."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service
            
            all_keys = api_key_service.list_api_keys()
            
            if service:
                all_keys = [k for k in all_keys if k['service'] == service]
            
            result = []
            for key_data in all_keys:
                pydantic_api_key = DomainApiKey(
                    id=key_data['id'],
                    label=key_data['label'],
                    service=self._map_service(key_data['service'])
                )
                result.append(pydantic_api_key)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list API keys: {e}")
            return []
    
    async def get_available_models(self, service: str, api_key_id: ApiKeyID, info) -> List[str]:
        """Get available models for a service and API key."""
        try:
            context: GraphQLContext = info.context
            llm_service = context.llm_service
            
            models = await llm_service.get_available_models(
                service=service,
                api_key_id=api_key_id
            )
            
            return models
            
        except Exception as e:
            logger.error(f"Failed to get available models for {service}/{api_key_id}: {e}")
            return []
    
    def _map_service(self, service: str) -> LLMService:
        """Map service string to LLMService enum."""
        try:
            return LLMService(service.lower())
        except ValueError:
            raise ValueError(f"Unknown LLM service: {service}")

person_resolver = PersonResolver()