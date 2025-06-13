"""Person and API key resolvers for GraphQL queries."""
from typing import Optional, List

from ..types.domain import Person, ApiKey
from ..types.scalars import PersonID, ApiKeyID

class PersonResolver:
    """Resolver for person and API key related queries."""
    
    async def get_person(self, person_id: PersonID, info) -> Optional[Person]:
        """Get a single person by ID."""
        # TODO: Implement actual person fetching
        return None
    
    async def list_persons(self, limit: int, info) -> List[Person]:
        """List all persons."""
        # TODO: Implement actual person listing
        return []
    
    async def get_api_key(self, api_key_id: ApiKeyID, info) -> Optional[ApiKey]:
        """Get a single API key by ID."""
        # TODO: Implement actual API key fetching
        return None
    
    async def list_api_keys(self, service: Optional[str], info) -> List[ApiKey]:
        """List all API keys, optionally filtered by service."""
        # TODO: Implement actual API key listing
        return []
    
    async def get_available_models(self, service: str, api_key_id: ApiKeyID, info) -> List[str]:
        """Get available models for a service and API key."""
        # TODO: Implement actual model listing
        return []

person_resolver = PersonResolver()