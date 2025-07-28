"""Person and API key resolver using UnifiedServiceRegistry."""

import logging
from typing import Optional, List

from dipeo.application.unified_service_registry import UnifiedServiceRegistry, ServiceKey
from dipeo.diagram_generated.domain_models import (
    PersonID, ApiKeyID,
    DomainPerson,
    DomainApiKey
)
from dipeo.core.dynamic import PersonManager
from dipeo.core.ports import APIKeyPort
from dipeo.infra.llm import LLMInfraService

from ..types.inputs import PersonLLMConfigInput

logger = logging.getLogger(__name__)

# Service keys
PERSON_MANAGER = ServiceKey[PersonManager]("person_manager")
APIKEY_SERVICE = ServiceKey[APIKeyPort]("apikey_service")
LLM_SERVICE = ServiceKey[LLMInfraService]("llm_service")


class PersonResolver:
    """Resolver for person and API key related queries using service registry."""
    
    def __init__(self, registry: UnifiedServiceRegistry):
        self.registry = registry
    
    async def get_person(self, id: PersonID) -> Optional[DomainPerson]:
        """Get a single person by ID."""
        try:
            person_manager = self.registry.require(PERSON_MANAGER)
            # get_all_persons is not async and returns dict[PersonID, Person]
            persons_dict = person_manager.get_all_persons()
            
            # Check if person exists
            if id in persons_dict:
                person = persons_dict[id]
                # Convert Person to DomainPerson
                return DomainPerson(
                    id=person.id,
                    label=person.name,
                    llm_config=person.llm_config,
                    type="person"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching person {id}: {e}")
            return None
    
    async def list_persons(self, limit: int = 100) -> List[DomainPerson]:
        """List all persons."""
        try:
            person_manager = self.registry.require(PERSON_MANAGER)
            # get_all_persons is not async and returns dict[PersonID, Person]
            persons_dict = person_manager.get_all_persons()
            
            # Convert to DomainPerson list
            domain_persons = []
            for person in persons_dict.values():
                domain_persons.append(DomainPerson(
                    id=person.id,
                    label=person.name,
                    llm_config=person.llm_config,
                    type="person"
                ))
            
            # Apply limit
            return domain_persons[:limit]
            
        except Exception as e:
            logger.error(f"Error listing persons: {e}")
            return []
    
    async def get_api_key(self, id: ApiKeyID) -> Optional[DomainApiKey]:
        """Get a single API key by ID."""
        try:
            apikey_service = self.registry.require(APIKEY_SERVICE)
            # list_api_keys is not async and returns list of dicts
            api_keys = apikey_service.list_api_keys()
            
            # Find API key with matching ID
            for key_data in api_keys:
                if key_data.get('id') == str(id):
                    # Convert dict to DomainApiKey
                    return DomainApiKey(
                        id=key_data['id'],
                        label=key_data['label'],
                        service=key_data['service'],
                        key=key_data.get('key', '***hidden***')
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching API key {id}: {e}")
            return None
    
    async def list_api_keys(self, service: Optional[str] = None) -> List[DomainApiKey]:
        """List API keys, optionally filtered by service."""
        try:
            apikey_service = self.registry.require(APIKEY_SERVICE)
            # list_api_keys is not async and returns list of dicts
            api_keys = apikey_service.list_api_keys()
            
            # Convert to DomainApiKey objects
            domain_keys = []
            for key_data in api_keys:
                # Filter by service if provided
                if service and key_data.get('service') != service:
                    continue
                    
                domain_keys.append(DomainApiKey(
                    id=key_data['id'],
                    label=key_data['label'],
                    service=key_data['service'],
                    key='***hidden***'  # Never expose actual keys
                ))
            
            return domain_keys
            
        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            return []
    
    async def get_available_models(self, service: str, api_key_id: ApiKeyID) -> List[str]:
        """Get available models for a given service and API key."""
        try:
            # Get the API key
            api_key = await self.get_api_key(api_key_id)
            if not api_key:
                logger.warning(f"API key not found: {api_key_id}")
                return []
            
            # Get available models from LLM service
            llm_service = self.registry.require(LLM_SERVICE)
            models = await llm_service.get_available_models(service, api_key.key)
            
            return models
            
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []