"""Phase-aware execution capability for LLM providers."""

import logging
from typing import Any, Dict, List, Optional

from dipeo.config.llm import MEMORY_SELECTION_TEMPERATURE, MEMORY_SELECTION_MAX_TOKENS
from dipeo.diagram_generated import Message

from ..core.types import ExecutionPhase, MemorySelectionOutput, ProviderType

logger = logging.getLogger(__name__)


class PhaseHandler:
    """Handles execution phase-specific behavior for LLM providers."""
    
    def __init__(self, provider: ProviderType):
        """Initialize phase handler for specific provider."""
        self.provider = provider
    
    def prepare_messages_for_phase(
        self,
        messages: List[Message],
        phase: ExecutionPhase
    ) -> List[Message]:
        """Prepare messages based on execution phase."""
        if phase == ExecutionPhase.MEMORY_SELECTION:
            return self._prepare_memory_selection_messages(messages)
        elif phase == ExecutionPhase.DIRECT_EXECUTION:
            return self._prepare_direct_execution_messages(messages)
        else:
            return messages
    
    def _prepare_memory_selection_messages(self, messages: List[Message]) -> List[Message]:
        """Prepare messages for memory selection phase."""
        # Add instructions for memory selection
        system_prompt = (
            "You are a memory selection assistant. Your task is to analyze the conversation "
            "and select the most relevant message IDs based on the given criteria. "
            "Return only the selected message IDs in the specified format."
        )
        
        prepared_messages = []
        
        # Add or update system message
        has_system = any(msg.role == "system" for msg in messages)
        if not has_system:
            prepared_messages.append(Message(
                role="system",
                content=system_prompt
            ))
        
        # Add the rest of the messages
        for msg in messages:
            if msg.role == "system" and not has_system:
                # Enhance existing system message
                enhanced_content = f"{msg.content}\n\n{system_prompt}"
                prepared_messages.append(Message(
                    role=msg.role,
                    content=enhanced_content
                ))
            else:
                prepared_messages.append(msg)
        
        return prepared_messages
    
    def _prepare_direct_execution_messages(self, messages: List[Message]) -> List[Message]:
        """Prepare messages for direct execution phase."""
        # Direct execution uses messages as-is
        return messages
    
    def get_phase_specific_params(
        self,
        phase: ExecutionPhase
    ) -> Dict[str, Any]:
        """Get phase-specific parameters for the API call."""
        params = {}
        
        if phase == ExecutionPhase.MEMORY_SELECTION:
            # Memory selection typically needs structured output
            params['temperature'] = MEMORY_SELECTION_TEMPERATURE
            params['max_tokens'] = MEMORY_SELECTION_MAX_TOKENS
            
            if self.provider == ProviderType.OPENAI:
                params['response_format'] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "memory_selection",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "message_ids": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["message_ids"],
                            "additionalProperties": False
                        }
                    }
                }
            elif self.provider == ProviderType.ANTHROPIC:
                params['tool_choice'] = {
                    "type": "tool",
                    "name": "select_messages"
                }
                params['tools'] = [{
                    "name": "select_messages",
                    "description": "Select relevant message IDs",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "message_ids": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["message_ids"]
                    }
                }]
        
        elif phase == ExecutionPhase.DIRECT_EXECUTION:
            # Direct execution uses standard parameters
            pass
        
        return params
    
    def process_phase_response(
        self,
        response: Any,
        phase: ExecutionPhase
    ) -> Any:
        """Process response based on execution phase."""
        if phase == ExecutionPhase.MEMORY_SELECTION:
            return self._process_memory_selection_response(response)
        else:
            return response
    
    def _process_memory_selection_response(self, response: Any) -> MemorySelectionOutput:
        """Process memory selection phase response."""
        # Extract message IDs from response
        message_ids = []
        
        if self.provider == ProviderType.OPENAI:
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                if content:
                    import json
                    try:
                        data = json.loads(content)
                        message_ids = data.get('message_ids', [])
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse memory selection response: {content}")
        
        elif self.provider == ProviderType.ANTHROPIC:
            if hasattr(response, 'content'):
                for block in response.content:
                    if block.type == 'tool_use' and block.name == 'select_messages':
                        message_ids = block.input.get('message_ids', [])
                        break
        
        return MemorySelectionOutput(message_ids=message_ids)
    
    def validate_phase_transition(
        self,
        from_phase: ExecutionPhase,
        to_phase: ExecutionPhase
    ) -> bool:
        """Validate if phase transition is allowed."""
        # Define valid transitions
        valid_transitions = {
            ExecutionPhase.DEFAULT: [
                ExecutionPhase.MEMORY_SELECTION,
                ExecutionPhase.DIRECT_EXECUTION
            ],
            ExecutionPhase.MEMORY_SELECTION: [
                ExecutionPhase.DIRECT_EXECUTION,
                ExecutionPhase.DEFAULT
            ],
            ExecutionPhase.DIRECT_EXECUTION: [
                ExecutionPhase.DEFAULT,
                ExecutionPhase.MEMORY_SELECTION
            ]
        }
        
        return to_phase in valid_transitions.get(from_phase, [])


class MemorySelector:
    """Handles memory selection for conversations."""
    
    def __init__(self, phase_handler: PhaseHandler):
        """Initialize memory selector with phase handler."""
        self.phase_handler = phase_handler
    
    def create_selector_facet(
        self,
        criteria: str,
        conversation_id: str,
        max_messages: Optional[int] = None
    ) -> Message:
        """Create a selector facet message for memory selection."""
        content = f"Select messages from conversation {conversation_id} based on: {criteria}"
        
        if max_messages:
            content += f"\nMaximum messages to select: {max_messages}"
        
        return Message(
            role="user",
            content=content,
            metadata={
                "type": "selector_facet",
                "conversation_id": conversation_id,
                "criteria": criteria,
                "max_messages": max_messages
            }
        )
    
    def filter_selector_facets(self, messages: List[Message]) -> List[Message]:
        """Filter out selector facet messages from conversation."""
        return [
            msg for msg in messages
            if not (
                msg.metadata and
                msg.metadata.get("type") == "selector_facet"
            )
        ]
    
    def preserve_system_messages(self, messages: List[Message]) -> List[Message]:
        """Ensure system messages are preserved in selection."""
        system_messages = [msg for msg in messages if msg.role == "system"]
        other_messages = [msg for msg in messages if msg.role != "system"]
        return system_messages + other_messages