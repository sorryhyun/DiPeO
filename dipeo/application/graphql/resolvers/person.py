"""Person and API key resolver using ServiceRegistry."""

import asyncio
import logging
from typing import Optional, List

from dipeo.application.registry import ServiceRegistry, ServiceKey
from dipeo.application.registry.keys import DIAGRAM_SERVICE
from dipeo.application.registry.keys import API_KEY_SERVICE, LLM_SERVICE, PERSON_MANAGER
from dipeo.diagram_generated.domain_models import (
    PersonID, ApiKeyID,
    DomainPerson,
    DomainApiKey,
    PersonLLMConfig
)
from dipeo.domain.conversation import PersonManager
from dipeo.core.ports import APIKeyPort
from dipeo.infrastructure.services.llm import LLMInfraService

from ..types.inputs import PersonLLMConfigInput

logger = logging.getLogger(__name__)


class PersonResolver:
    """Resolver for person and API key related queries using service registry."""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
    
    async def get_person(self, id: PersonID) -> Optional[DomainPerson]:
        """Get a single person by ID."""
        try:
            # Get integrated diagram service to find person in diagrams
            integrated_service = self.registry.resolve(DIAGRAM_SERVICE)
            if not integrated_service:
                logger.warning("Integrated diagram service not available")
                return None
            
            # Search through all diagrams for the person
            diagram_infos = await integrated_service.list_diagrams()
            
            for diagram_info in diagram_infos:
                # Extract diagram ID from path
                path = diagram_info.get("path", "")
                diagram_id = path.split(".")[0] if path else diagram_info.get("id")
                
                # Load diagram
                diagram_dict = await integrated_service.get_diagram(diagram_id)
                if not diagram_dict:
                    continue
                
                # Check if this diagram contains the person
                persons = diagram_dict.get("persons", {})
                if str(id) in persons:
                    person_data = persons[str(id)]
                    # Convert to DomainPerson
                    return DomainPerson(
                        id=id,
                        label=person_data.get("name", ""),
                        llm_config=PersonLLMConfig(
                            service=person_data.get("service", "openai"),
                            model=person_data.get("modelName", "gpt-4.1-nano"),
                            api_key_id=person_data.get("apiKeyId", ""),
                            system_prompt=person_data.get("systemPrompt", ""),
                        ),
                        type="person"
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching person {id}: {e}")
            return None
    
    async def list_persons(self, limit: int = 100) -> List[DomainPerson]:
        """List all persons."""
        try:
            # Get integrated diagram service to find persons in diagrams
            integrated_service = self.registry.resolve(DIAGRAM_SERVICE)
            if not integrated_service:
                logger.warning("Integrated diagram service not available")
                return []
            
            # Collect all unique persons across all diagrams
            all_persons = {}
            diagram_infos = await integrated_service.list_diagrams()
            
            for diagram_info in diagram_infos:
                # Extract diagram ID from path
                path = diagram_info.get("path", "")
                diagram_id = path.split(".")[0] if path else diagram_info.get("id")
                
                # Load diagram
                diagram_dict = await integrated_service.get_diagram(diagram_id)
                if not diagram_dict:
                    continue
                
                # Add all persons from this diagram
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
                            type="person"
                        )
            
            # Convert to list and apply limit
            domain_persons = list(all_persons.values())
            return domain_persons[:limit]
            
        except Exception as e:
            logger.error(f"Error listing persons: {e}")
            return []
    
    async def get_api_key(self, id: ApiKeyID) -> Optional[DomainApiKey]:
        """Get a single API key by ID."""
        try:
            apikey_service = self.registry.resolve(API_KEY_SERVICE)
            # Run blocking operation in thread pool to avoid blocking event loop
            api_keys = await asyncio.to_thread(
                apikey_service.list_api_keys
            )
            
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
            apikey_service = self.registry.resolve(API_KEY_SERVICE)
            logger.debug(f"Got apikey_service: {apikey_service}")
            # Run blocking operation in thread pool to avoid blocking event loop
            api_keys = await asyncio.to_thread(
                apikey_service.list_api_keys
            )
            logger.debug(f"Got {len(api_keys)} API keys from service")
            
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
            llm_service = self.registry.resolve(LLM_SERVICE)
            models = await llm_service.get_available_models(api_key_id)
            
            return models
            
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []