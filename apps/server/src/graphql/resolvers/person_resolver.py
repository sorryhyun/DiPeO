"""Person and API key resolvers for GraphQL queries."""
from typing import Optional, List
import logging

from ..types.domain import Person, ApiKey
from ..types.scalars import PersonID, ApiKeyID
from ..types.enums import LLMService, ForgettingMode
from ..context import GraphQLContext

logger = logging.getLogger(__name__)

class PersonResolver:
    """Resolver for person and API key related queries."""
    
    async def get_person(self, person_id: PersonID, info) -> Optional[Person]:
        """Get a single person by ID."""
        # Note: Persons are typically defined within diagrams, not as standalone entities
        # This would require loading all diagrams and searching for the person
        # For now, return None as this is not a common use case
        logger.warning(f"get_person called for {person_id} - persons are diagram-scoped")
        return None
    
    async def list_persons(self, limit: int, info) -> List[Person]:
        """List all persons."""
        # Note: Persons are defined within diagrams, not globally
        # To implement this, we'd need to load all diagrams and extract persons
        # This is not efficient and likely not the intended use case
        logger.warning("list_persons called - persons are diagram-scoped")
        return []
    
    async def get_api_key(self, api_key_id: ApiKeyID, info) -> Optional[ApiKey]:
        """Get a single API key by ID."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service
            
            # Get API key from service
            api_key_data = api_key_service.get_api_key(api_key_id)
            
            if not api_key_data:
                return None
            
            # Convert to GraphQL ApiKey type
            return ApiKey(
                id=api_key_data['id'],
                label=api_key_data['label'],
                service=self._map_service(api_key_data['service'])
            )
            
        except Exception as e:
            logger.error(f"Failed to get API key {api_key_id}: {e}")
            return None
    
    async def list_api_keys(self, service: Optional[str], info) -> List[ApiKey]:
        """List all API keys, optionally filtered by service."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service
            
            # Get all API keys
            all_keys = api_key_service.list_api_keys()
            
            # Filter by service if provided
            if service:
                all_keys = [k for k in all_keys if k['service'] == service]
            
            # Convert to GraphQL ApiKey objects
            result = []
            for key_data in all_keys:
                result.append(ApiKey(
                    id=key_data['id'],
                    label=key_data['label'],
                    service=self._map_service(key_data['service'])
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list API keys: {e}")
            return []
    
    async def get_available_models(self, service: str, api_key_id: ApiKeyID, info) -> List[str]:
        """Get available models for a service and API key."""
        try:
            context: GraphQLContext = info.context
            llm_service = context.llm_service
            
            # Get available models from LLM service
            models = llm_service.get_available_models(
                service=service,
                api_key_id=api_key_id
            )
            
            return models
            
        except Exception as e:
            logger.error(f"Failed to get available models for {service}/{api_key_id}: {e}")
            return []
    
    def _map_service(self, service: str) -> LLMService:
        """Map service string to LLMService enum."""
        service_map = {
            'openai': LLMService.OPENAI,
            'claude': LLMService.CLAUDE,
            'gemini': LLMService.GEMINI,
            'groq': LLMService.GROQ,
            'deepseek': LLMService.DEEPSEEK
        }
        return service_map.get(service.lower(), LLMService.OPENAI)

person_resolver = PersonResolver()