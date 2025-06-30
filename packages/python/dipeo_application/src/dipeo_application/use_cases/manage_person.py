"""Use case for managing persons (AI agents) in diagrams."""

from typing import TYPE_CHECKING, Any, Optional
from dipeo_core import BaseService, Result, Error
from dipeo_domain.models import Person, PersonID, LLMService
import uuid

if TYPE_CHECKING:
    from dipeo_domain.domains.conversation import ConversationMemoryDomainService
    from dipeo_domain.domains.apikey import APIKeyDomainService


class ManagePersonUseCase(BaseService):
    """Use case for managing persons (AI agents)."""
    
    def __init__(
        self,
        conversation_memory_service: "ConversationMemoryDomainService",
        api_key_service: "APIKeyDomainService",
    ):
        """Initialize with required services."""
        super().__init__()
        self.conversation_memory = conversation_memory_service
        self.api_key_service = api_key_service
    
    async def create_person(
        self,
        name: str,
        system_prompt: str,
        llm_service: LLMService,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Result[Person, Error]:
        """Create a new person.
        
        Args:
            name: Person name
            system_prompt: System prompt for the AI
            llm_service: LLM service to use
            model: Model name
            temperature: Temperature setting
            max_tokens: Maximum tokens for responses
            
        Returns:
            Result containing created person or error
        """
        # Validate API key exists for the service
        api_key_result = self.api_key_service.get_api_key(llm_service)
        if not api_key_result:
            return Result.err(Error(
                code="API_KEY_NOT_FOUND",
                message=f"No API key configured for {llm_service}"
            ))
        
        # Create person
        try:
            person = Person(
                id=PersonID(str(uuid.uuid4())),
                name=name,
                system_prompt=system_prompt,
                service=llm_service,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Initialize conversation memory
            await self.conversation_memory.get_or_create_person_memory(
                person_id=person.id,
                execution_id="default",  # Default for non-execution context
            )
            
            return Result.ok(person)
            
        except Exception as e:
            return Result.err(Error(
                code="PERSON_CREATION_ERROR",
                message=f"Failed to create person: {str(e)}"
            ))
    
    async def update_person(
        self,
        person_id: PersonID,
        updates: dict[str, Any],
    ) -> Result[Person, Error]:
        """Update an existing person.
        
        Args:
            person_id: ID of person to update
            updates: Fields to update
            
        Returns:
            Result containing updated person or error
        """
        # This would typically load from storage, update, and save
        # For now, returning error as we don't have person storage yet
        return Result.err(Error(
            code="NOT_IMPLEMENTED",
            message="Person storage not yet implemented"
        ))
    
    async def delete_person_memory(
        self,
        person_id: PersonID,
        execution_id: Optional[str] = None,
    ) -> Result[bool, Error]:
        """Delete conversation memory for a person.
        
        Args:
            person_id: ID of person
            execution_id: Optional execution context
            
        Returns:
            Result indicating success or error
        """
        try:
            # Clear memory for the person
            memory = await self.conversation_memory.get_or_create_person_memory(
                person_id=person_id,
                execution_id=execution_id or "default",
            )
            
            # Clear messages
            await memory.clear()
            
            return Result.ok(True)
            
        except Exception as e:
            return Result.err(Error(
                code="MEMORY_DELETION_ERROR",
                message=f"Failed to delete person memory: {str(e)}"
            ))
    
    async def get_person_memory_stats(
        self,
        person_id: PersonID,
        execution_id: Optional[str] = None,
    ) -> Result[dict[str, Any], Error]:
        """Get memory statistics for a person.
        
        Args:
            person_id: ID of person
            execution_id: Optional execution context
            
        Returns:
            Result containing memory stats or error
        """
        try:
            memory = await self.conversation_memory.get_or_create_person_memory(
                person_id=person_id,
                execution_id=execution_id or "default",
            )
            
            messages = await memory.get_messages()
            total_tokens = sum(
                msg.token_usage.total if msg.token_usage else 0
                for msg in messages
            )
            
            return Result.ok({
                "message_count": len(messages),
                "total_tokens": total_tokens,
                "memory_type": memory.__class__.__name__,
            })
            
        except Exception as e:
            return Result.err(Error(
                code="MEMORY_STATS_ERROR",
                message=f"Failed to get memory stats: {str(e)}"
            ))