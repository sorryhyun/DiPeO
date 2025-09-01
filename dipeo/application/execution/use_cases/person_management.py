"""Use case for managing persons in diagrams."""

import logging
from typing import Any, Optional, Dict

from dipeo.domain.conversation import Person
from dipeo.diagram_generated.domain_models import PersonID, PersonLLMConfig

logger = logging.getLogger(__name__)


class PersonManagementUseCase:
    """Centralized use case for managing persons (AI agents) in diagrams.
    
    This use case handles:
    - Getting existing persons from person repository
    - Creating persons from diagram metadata
    - Registering persons with person repository
    - Caching persons for performance
    """
    
    def __init__(self):
        """Initialize the person management use case."""
        self._person_cache: dict[str, Person] = {}
    
    def get_or_create_person(
        self,
        person_id: str,
        diagram: Any = None,
        person_repository: Any = None
    ) -> Optional[Person]:
        """Get existing person or create new one from diagram configuration.
        
        Args:
            person_id: The ID of the person to get or create
            diagram: The diagram containing person definitions in metadata
            person_repository: The person repository for person registration
            
        Returns:
            The Person object, or None if not found and couldn't be created
        """
        # Check cache first
        if person_id in self._person_cache:
            logger.debug(f"[PersonManagement] Using cached person: {person_id}")
            return self._person_cache[person_id]
        
        # Try to get from person repository
        if person_repository:
            person = self._get_from_person_repository(person_id, person_repository)
            if person:
                self._person_cache[person_id] = person
                return person
        
        # Create from diagram metadata
        if diagram:
            person = self._create_from_diagram(
                person_id, 
                diagram, 
                person_repository
            )
            if person:
                self._person_cache[person_id] = person
                return person
        
        logger.error(f"[PersonManagement] Could not find or create person: {person_id}")
        return None
    
    def _get_from_person_repository(
        self,
        person_id: str,
        person_repository: Any
    ) -> Optional[Person]:
        """Try to get person from person repository.
        
        Args:
            person_id: The ID of the person to get
            person_repository: The person repository
            
        Returns:
            The Person object if found, None otherwise
        """
        if hasattr(person_repository, 'get'):
            try:
                person = person_repository.get(PersonID(person_id))
                if person:
                    logger.debug(
                        f"[PersonManagement] Found person in person repository: {person_id}"
                    )
                    return person
            except (KeyError, Exception) as e:
                logger.debug(
                    f"[PersonManagement] Person {person_id} not in person repository: {e}"
                )
        return None
    
    def _create_from_diagram(
        self,
        person_id: str,
        diagram: Any,
        person_repository: Any = None
    ) -> Optional[Person]:
        """Create person from diagram metadata.
        
        Args:
            person_id: The ID of the person to create
            diagram: The diagram containing person definitions
            person_repository: Optional person repository for registration
            
        Returns:
            The created Person object, or None if not found in metadata
        """
        if not (hasattr(diagram, 'metadata') and diagram.metadata):
            return None
        
        persons = diagram.metadata.get("persons", {})
        if person_id not in persons:
            logger.debug(
                f"[PersonManagement] Person {person_id} not found in diagram metadata"
            )
            return None
        
        person_config = persons[person_id]
        logger.debug(
            f"[PersonManagement] Creating person {person_id} from metadata: {person_config}"
        )
        
        # Create PersonLLMConfig from config
        llm_config = PersonLLMConfig(
            service=person_config.get('service', 'openai'),
            model=person_config.get('model', 'gpt-5-nano-2025-08-07'),
            api_key_id=person_config.get('api_key_id', 'default'),
            system_prompt=person_config.get('system_prompt', None),
            prompt_file=person_config.get('prompt_file', None)
        )
        
        # Create Person object
        person = Person(
            id=PersonID(person_id),
            name=person_config.get('name', person_id),
            llm_config=llm_config
        )
        
        # Register with person repository if available
        if person_repository:
            self._register_person(person_id, person_config, person_repository)
        
        return person
    
    def _register_person(
        self,
        person_id: str,
        person_config: Dict[str, Any],
        person_repository: Any
    ) -> None:
        """Register person with person repository.
        
        Args:
            person_id: The ID of the person
            person_config: The person configuration
            person_repository: The person repository
        """
        if hasattr(person_repository, 'register_person'):
            try:
                # Convert to format expected by register_person
                config = {
                    "service": person_config.get("service", "openai"),
                    "model": person_config.get("model", "gpt-5-nano-2025-08-07"),
                    "api_key_id": person_config.get("api_key_id", "default"),
                }
                
                if "system_prompt" in person_config:
                    config["system_prompt"] = person_config["system_prompt"]
                
                person_repository.register_person(person_id, config)
                logger.debug(
                    f"[PersonManagement] Registered person {person_id} with person repository"
                )
            except Exception as e:
                logger.warning(
                    f"[PersonManagement] Could not register person {person_id}: {e}"
                )
    
    def register_diagram_persons(
        self,
        diagram: Any,
        person_repository: Any
    ) -> None:
        """Register all persons from diagram metadata with person repository.
        
        This is useful when loading sub-diagrams to ensure all defined persons
        are available for person_job nodes.
        
        Args:
            diagram: The diagram containing person definitions
            person_repository: The person repository for registration
        """
        if not (hasattr(diagram, 'metadata') and diagram.metadata):
            logger.debug("[PersonManagement] No metadata in diagram")
            return
        
        if not person_repository:
            logger.debug("[PersonManagement] No person repository available")
            return
        
        persons = diagram.metadata.get("persons", {})
        if not persons:
            logger.debug("[PersonManagement] No persons found in diagram metadata")
            return
        
        logger.debug(
            f"[PersonManagement] Registering {len(persons)} persons from diagram"
        )
        
        # Register each person
        for person_id, person_config in persons.items():
            try:
                self._register_person(person_id, person_config, person_repository)
            except Exception as e:
                logger.error(
                    f"[PersonManagement] Failed to register person {person_id}: {e}"
                )
    
    def clear_cache(self):
        """Clear the person cache."""
        self._person_cache.clear()
        logger.debug("[PersonManagement] Person cache cleared")
    
    def get_cached_person(self, person_id: str) -> Optional[Person]:
        """Get a person from cache without creating.
        
        Args:
            person_id: The ID of the person
            
        Returns:
            The cached Person object, or None if not cached
        """
        return self._person_cache.get(person_id)