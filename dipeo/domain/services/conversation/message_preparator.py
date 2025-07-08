"""Domain service for preparing messages for LLM calls."""

from typing import Any, Dict, List, Optional


class MessagePreparator:
    """Prepares messages for LLM execution.
    
    Single Responsibility: Message preparation and formatting for LLM calls.
    """
    
    def prepare_messages(
        self,
        system_prompt: Optional[str],
        conversation_messages: List[Dict[str, Any]],
        current_prompt: str,
    ) -> List[Dict[str, Any]]:
        """Prepare messages for LLM execution.
        
        Args:
            system_prompt: Optional system prompt to include
            conversation_messages: Previous conversation messages
            current_prompt: The current user prompt
            
        Returns:
            List of formatted messages for LLM
        """
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add conversation messages
        messages.extend(conversation_messages)
        
        # Add current prompt if provided
        if current_prompt:
            messages.append({
                "role": "user",
                "content": current_prompt
            })
        
        return messages
    
    def format_message(
        self,
        role: str,
        content: str,
        tool_calls: Optional[Any] = None,
        tool_call_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Format a single message.
        
        Args:
            role: Message role (system, user, assistant, tool)
            content: Message content
            tool_calls: Optional tool calls
            tool_call_id: Optional tool call ID
            
        Returns:
            Formatted message dictionary
        """
        message = {
            "role": role,
            "content": content,
        }
        
        if tool_calls is not None:
            message["tool_calls"] = tool_calls
            
        if tool_call_id is not None:
            message["tool_call_id"] = tool_call_id
            
        return message
    
    def validate_messages(
        self,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Validate and clean messages for LLM.
        
        Args:
            messages: List of messages to validate
            
        Returns:
            Validated messages
            
        Raises:
            ValueError: If messages are invalid
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        validated = []
        valid_roles = {"system", "user", "assistant", "tool"}
        
        for msg in messages:
            if not isinstance(msg, dict):
                raise ValueError(f"Message must be a dictionary, got {type(msg)}")
            
            role = msg.get("role")
            if role not in valid_roles:
                raise ValueError(f"Invalid role: {role}. Must be one of {valid_roles}")
            
            content = msg.get("content", "")
            if not isinstance(content, str):
                content = str(content)
            
            validated_msg = {
                "role": role,
                "content": content,
            }
            
            # Preserve optional fields
            if "tool_calls" in msg:
                validated_msg["tool_calls"] = msg["tool_calls"]
            if "tool_call_id" in msg:
                validated_msg["tool_call_id"] = msg["tool_call_id"]
            
            validated.append(validated_msg)
        
        return validated
    
    def merge_conversation_states(
        self,
        states: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Merge multiple conversation states into a single message list.
        
        Args:
            states: List of conversation state dictionaries
            
        Returns:
            Merged list of messages
        """
        merged = []
        
        for state in states:
            if isinstance(state, dict) and "messages" in state:
                messages = state["messages"]
                if isinstance(messages, list):
                    merged.extend(messages)
        
        return merged