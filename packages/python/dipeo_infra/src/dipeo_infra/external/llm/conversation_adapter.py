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
    Conversation,
    MemoryConfig,
)


logger = logging.getLogger(__name__)


# Define local types that aren't in dipeo_domain
class ConversationContext:
    """Context for a conversation."""

    def __init__(self, system_prompt: Optional[str], user_message: str):
        self.system_prompt = system_prompt
        self.user_message = user_message


class ConversationService:
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
        person: DomainPerson,
        job: PersonJobNodeData,
        execution_id: str,
        node_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
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
                node_id=node_id,
            )

            # Call LLM - use person's model and service
            chat_result = await self.llm_service.call_llm(
                model=person.model,
                messages=messages,
                temperature=job.memory_config.temperature
                if job.memory_config and job.memory_config.temperature
                else 0.7,
                max_tokens=None,  # Let the service use defaults
            )

            # Extract response content
            response_content = chat_result.text

            # Add assistant response to memory
            self.memory_service.add_message_to_conversation(
                person_id=person.id,
                execution_id=execution_id,
                role="assistant",
                content=response_content,
                current_person_id=person.id,
                node_id=node_id,
            )

            return {
                "success": True,
                "response": response_content,
                "person_id": person.id,
                "execution_id": execution_id,
                "node_id": node_id,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error executing person job: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "person_id": person.id,
                "execution_id": execution_id,
            }

    def _build_conversation_context(
        self,
        person: DomainPerson,
        job: PersonJobNodeData,
        variables: Optional[Dict[str, Any]] = None,
    ) -> ConversationContext:
        """Build the conversation context from person and job."""
        # Use the appropriate prompt based on execution count
        # For first execution, use firstOnlyPrompt, otherwise use defaultPrompt
        user_message = job.first_only_prompt or job.default_prompt or ""

        # Apply variable substitution if needed
        if variables:
            for key, value in variables.items():
                user_message = user_message.replace(f"{{{key}}}", str(value))

        # Use person's system prompt
        system_prompt = person.system_prompt

        return ConversationContext(
            system_prompt=system_prompt, user_message=user_message
        )

    def _prepare_messages(
        self,
        person: DomainPerson,
        context: ConversationContext,
        history: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """Prepare messages for LLM call."""
        messages: List[Dict[str, str]] = []

        # Add system message if present
        if context.system_prompt:
            messages.append({"role": "system", "content": context.system_prompt})

        # Add conversation history
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current user message
        messages.append({"role": "user", "content": context.user_message})

        return messages

    async def execute_simple_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "gpt-4.1-nano",
    ) -> Dict[str, Any]:
        """
        Execute a simple prompt without person context.

        This is useful for one-off LLM calls that don't need conversation memory.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            model: LLM model to use (default: gpt-4.1-nano)

        Returns:
            Dict containing the response
        """
        try:
            messages: List[Dict[str, str]] = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            chat_result = await self.llm_service.call_llm(
                model=model, messages=messages, temperature=0.7, max_tokens=None
            )

            return {
                "success": True,
                "response": chat_result.text,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error executing simple prompt: {str(e)}")
            return {"success": False, "error": str(e)}
