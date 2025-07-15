# Message building and formatting for conversations

import json
from datetime import datetime
from typing import Any


class MessageFormatter:
    # Formats messages for LLM conversations
    
    @staticmethod
    def create_message(
        role: str,
        content: str,
        name: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        # Create a properly formatted message
        message = {
            "role": role,
            "content": content
        }
        
        if name:
            message["name"] = name
        
        if metadata:
            message["metadata"] = metadata
        
        return message
    
    @staticmethod
    def create_system_message(
        content: str,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        # Create a system message
        return MessageFormatter.create_message("system", content, metadata=metadata)
    
    @staticmethod
    def create_user_message(
        content: str,
        name: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        # Create a user message
        return MessageFormatter.create_message("user", content, name=name, metadata=metadata)
    
    @staticmethod
    def create_assistant_message(
        content: str,
        name: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        # Create an assistant message
        return MessageFormatter.create_message("assistant", content, name=name, metadata=metadata)
    
    @staticmethod
    def format_input_as_message(
        inputs: dict[str, Any],
        role: str = "user",
        format_type: str = "json"
    ) -> dict[str, Any]:
        # Format inputs as a message
        if format_type == "json":
            content = json.dumps(inputs, indent=2)
        elif format_type == "yaml":
            # Simple YAML-like formatting
            lines = []
            for key, value in inputs.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{key}:")
                    lines.append(f"  {json.dumps(value, indent=2)}")
                else:
                    lines.append(f"{key}: {value}")
            content = "\n".join(lines)
        elif format_type == "text":
            # Human-readable format
            lines = []
            for key, value in inputs.items():
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
            content = "\n".join(lines)
        else:
            # Raw format
            content = str(inputs)
        
        return MessageFormatter.create_message(
            role=role,
            content=content,
            metadata={"format": format_type, "source": "inputs"}
        )
    
    @staticmethod
    def merge_messages(
        messages: list[dict[str, Any]],
        dedup: bool = True
    ) -> list[dict[str, Any]]:
        # Merge multiple message lists, optionally deduplicating
        if not dedup:
            return messages
        
        seen = set()
        result = []
        
        for msg in messages:
            # Create a unique key for the message
            key = (
                msg.get('role'),
                msg.get('content'),
                msg.get('name')
            )
            
            if key not in seen:
                seen.add(key)
                result.append(msg)
        
        return result
    
    @staticmethod
    def add_timestamp(
        message: dict[str, Any],
        timestamp: datetime | None = None
    ) -> dict[str, Any]:
        # Add timestamp to message metadata
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        if 'metadata' not in message:
            message['metadata'] = {}
        
        message['metadata']['timestamp'] = timestamp.isoformat()
        return message
    
    @staticmethod
    def extract_code_blocks(content: str) -> list[dict[str, str]]:
        # Extract code blocks from message content
        import re
        
        code_blocks = []
        pattern = r'```(\w*)\n(.*?)```'
        
        matches = re.findall(pattern, content, re.DOTALL)
        for lang, code in matches:
            code_blocks.append({
                'language': lang or 'plaintext',
                'code': code.strip()
            })
        
        return code_blocks
    
    @staticmethod
    def format_conversation_context(
        messages: list[dict[str, Any]],
        max_length: int | None = None
    ) -> str:
        # Format messages as a conversation context string
        lines = []
        
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if max_length and len(content) > max_length:
                content = content[:max_length] + "..."
            
            lines.append(f"{role.upper()}: {content}")
        
        return "\n\n".join(lines)
    
    @staticmethod
    def create_function_call_message(
        function_name: str,
        arguments: dict[str, Any],
        result: Any,
        role: str = "assistant"
    ) -> dict[str, Any]:
        # Create a message representing a function call
        content = {
            "function": function_name,
            "arguments": arguments,
            "result": result
        }
        
        return MessageFormatter.create_message(
            role=role,
            content=json.dumps(content, indent=2),
            metadata={
                "type": "function_call",
                "function": function_name
            }
        )
    
    @staticmethod
    def validate_message(message: dict[str, Any]) -> list[str]:
        # Validate message structure and return errors
        errors = []
        
        # Check required fields
        if 'role' not in message:
            errors.append("Message missing required 'role' field")
        elif message['role'] not in ['system', 'user', 'assistant', 'function', 'tool']:
            errors.append(f"Invalid role: {message['role']}")
        
        if 'content' not in message:
            errors.append("Message missing required 'content' field")
        elif not isinstance(message['content'], str):
            errors.append("Message content must be a string")
        
        # Check optional fields
        if 'name' in message and not isinstance(message['name'], str):
            errors.append("Message name must be a string")
        
        if 'metadata' in message and not isinstance(message['metadata'], dict):
            errors.append("Message metadata must be a dictionary")
        
        return errors
    
    @staticmethod
    def prepare_messages(
        system_prompt: str | None,
        conversation_messages: list[dict[str, Any]],
        current_prompt: str,
    ) -> list[dict[str, Any]]:
        # Prepare messages for LLM execution
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
    
    @staticmethod
    def format_message(
        role: str,
        content: str,
        tool_calls: Any | None = None,
        tool_call_id: str | None = None,
    ) -> dict[str, Any]:
        # Format a single message with optional tool information
        message = {
            "role": role,
            "content": content,
        }
        
        if tool_calls is not None:
            message["tool_calls"] = tool_calls
            
        if tool_call_id is not None:
            message["tool_call_id"] = tool_call_id
            
        return message
    
    @staticmethod
    def validate_messages(
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        # Validate and clean messages for LLM
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
    
    @staticmethod
    def merge_conversation_states(
        states: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        # Merge multiple conversation states into a single message list
        merged = []
        
        for state in states:
            if isinstance(state, dict) and "messages" in state:
                messages = state["messages"]
                if isinstance(messages, list):
                    merged.extend(messages)
        
        return merged