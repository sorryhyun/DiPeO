"""Simple conversation service for executing person_job nodes locally."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from dipeo_core import SupportsMemory, SupportsLLM
from dipeo_domain import (
    DomainPerson,
    PersonJobNodeData,
    LLMService,
    Message,
    Conversation
)
0

logger = logging.getLogger(__name__)


class SimpleConversationService:
    """Basic conversation management for person_job nodes in local execution."""
    
    def __init__(self, memory_service: SupportsMemory, llm_service: SupportsLLM):
        """
        Initialize the conversation service.
        
        Args:
            memory_service: Service for managing conversation memory
            llm_service: Service for LLM interactions
        """
        self.memory_service = memory_service
        self.llm_service = llm_service
    
    async def execute_person_job(
        self,
        person: Person,
        job: PersonJob,
        execution_id: str,
        node_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a person job by managing the conversation with an LLM.
        
        Args:
            person: The person entity
            job: The job to execute
            execution_id: Current execution ID
            node_id: Optional node ID in the diagram
            variables: Optional variables for template substitution
            
        Returns:
            Dict containing the response and metadata
        """
        try:
            # Get or create person memory
            self.memory_service.get_or_create_person_memory(person.id)
            
            # Build the conversation context
            context = self._build_conversation_context(person, job, variables)
            
            # Get conversation history
            history = self.memory_service.get_conversation_history(person.id)
            
            # Prepare messages for LLM
            messages = self._prepare_messages(person, context, history)
            
            # Add user message to memory
            self.memory_service.add_message_to_conversation(
                person_id=person.id,
                execution_id=execution_id,
                role="user",
                content=context.user_message,
                current_person_id=person.id,
                node_id=node_id
            )
            
            # Call LLM
            llm_config = job.llm_config or person.llm_config or LLMConfig()
            response = await self.llm_service.call_llm(
                model=llm_config.model,
                messages=messages,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens
            )
            
            # Extract response content
            response_content = response.get("content", "")
            
            # Add assistant response to memory
            self.memory_service.add_message_to_conversation(
                person_id=person.id,
                execution_id=execution_id,
                role="assistant",
                content=response_content,
                current_person_id=person.id,
                node_id=node_id
            )
            
            return {
                "success": True,
                "response": response_content,
                "person_id": person.id,
                "job_id": job.id,
                "execution_id": execution_id,
                "node_id": node_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing person job: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "person_id": person.id,
                "job_id": job.id,
                "execution_id": execution_id
            }
    
    def _build_conversation_context(
        self,
        person: Person,
        job: PersonJob,
        variables: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """Build the conversation context from person and job."""
        # Start with job instructions
        user_message = job.job or ""
        
        # Apply variable substitution if needed
        if variables:
            for key, value in variables.items():
                user_message = user_message.replace(f"{{{key}}}", str(value))
        
        # Build system prompt
        system_parts = []
        
        # Add person instructions
        if person.instructions:
            system_parts.append(f"Instructions: {person.instructions}")
        
        # Add role if specified
        if person.role:
            system_parts.append(f"Role: {person.role}")
        
        # Add job-specific system prompt if any
        if hasattr(job, "system_prompt") and job.system_prompt:
            system_parts.append(job.system_prompt)
        
        system_prompt = "\n\n".join(system_parts) if system_parts else None
        
        return ConversationContext(
            system_prompt=system_prompt,
            user_message=user_message
        )
    
    def _prepare_messages(
        self,
        person: Person,
        context: ConversationContext,
        history: List[Dict[str, Any]]
    ) -> List[MessageDict]:
        """Prepare messages for LLM call."""
        messages: List[MessageDict] = []
        
        # Add system message if present
        if context.system_prompt:
            messages.append({
                "role": "system",
                "content": context.system_prompt
            })
        
        # Add conversation history
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": context.user_message
        })
        
        return messages
    
    async def execute_simple_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        llm_config: Optional[LLMConfig] = None
    ) -> Dict[str, Any]:
        """
        Execute a simple prompt without person context.
        
        This is useful for one-off LLM calls that don't need conversation memory.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            llm_config: Optional LLM configuration
            
        Returns:
            Dict containing the response
        """
        try:
            messages: List[MessageDict] = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            config = llm_config or LLMConfig()
            response = await self.llm_service.call_llm(
                model=config.model,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
            
            return {
                "success": True,
                "response": response.get("content", ""),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing simple prompt: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }