"""Claude Code client wrapper using claude-code-sdk."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

from dipeo.config.llm import DEFAULT_TEMPERATURE
from ...core.client import AsyncBaseClientWrapper, BaseClientWrapper
from ...core.types import AdapterConfig

logger = logging.getLogger(__name__)


class ClaudeCodeClientWrapper(BaseClientWrapper):
    """Synchronous Claude Code client wrapper using claude-code-sdk."""
    
    def __init__(self, config: AdapterConfig):
        """Initialize Claude Code client wrapper."""
        super().__init__(config)
        self.logs_dir = Path(".logs")
        self.logs_dir.mkdir(exist_ok=True)
    
    def _create_client(self) -> None:
        """Claude Code SDK doesn't use a traditional client initialization."""
        return None
    
    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Execute synchronous chat completion using async wrapper."""
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, use nest_asyncio
                import nest_asyncio
                nest_asyncio.apply()
                return asyncio.run(self._async_chat_completion(
                    messages, model, temperature, max_tokens, tools, 
                    response_format, system, **kwargs
                ))
            except RuntimeError:
                # No running loop, use asyncio.run normally
                return asyncio.run(self._async_chat_completion(
                    messages, model, temperature, max_tokens, tools,
                    response_format, system, **kwargs
                ))
        except Exception as e:
            logger.error(f"Error in chat_completion: {e}")
            raise
    
    def _format_messages_as_jsonl_sync(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages in JSON Lines format for sync methods."""
        import json
        jsonl_lines = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Handle content that might already be structured
            if isinstance(content, list):
                content_blocks = content
            else:
                # Convert string content to content block format
                content_blocks = [{"type": "text", "text": str(content)}]
            
            # Create JSON Line entry
            # Map 'system' role to 'user' type with system indicator in content
            if role == "system":
                json_entry = {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": [{"type": "text", "text": f"[SYSTEM]: {content_blocks[0]['text']}"}]
                    }
                }
            else:
                json_entry = {
                    "type": role,
                    "message": {
                        "role": role,
                        "content": content_blocks
                    }
                }
            
            jsonl_lines.append(json.dumps(json_entry, ensure_ascii=False))
        
        # Join with newlines to create JSON Lines format
        return "\n".join(jsonl_lines)
    
    async def _async_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Internal async chat completion implementation."""
        try:
            from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
        except ImportError as e:
            logger.error("claude-code-sdk not installed. Install with: pip install claude-code-sdk")
            raise ImportError("claude-code-sdk is required for Claude Code support") from e
        
        # Prepare query in JSON Lines format
        use_jsonl = kwargs.get("use_jsonl_format", True)  # Default to new format
        
        if use_jsonl:
            # Use structured JSON Lines format
            query = self._format_messages_as_jsonl_sync(messages)
        else:
            # Fallback to old concatenation method
            query = "\n\n".join([
                msg.get("content", "") for msg in messages 
                if msg.get("role") != "system"
            ])
        
        # Prepare options
        options_dict = {}
        if system:
            options_dict["system_prompt"] = system
        options_dict["max_turns"] = kwargs.get("max_turns", 1)
        
        options = ClaudeCodeOptions(**options_dict)
        
        # Execute with Claude Code SDK
        full_text = ""
        metadata = {}
        
        async with ClaudeSDKClient(options=options) as client:
            await client.query(query)
            
            async for message in client.receive_messages():
                # Extract content
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            full_text += block.text
                
                # Capture metadata from ResultMessage
                if type(message).__name__ == "ResultMessage":
                    if hasattr(message, 'total_cost_usd'):
                        metadata["cost"] = message.total_cost_usd
                    if hasattr(message, 'duration_ms'):
                        metadata["duration_ms"] = message.duration_ms
                    if hasattr(message, 'num_turns'):
                        metadata["num_turns"] = message.num_turns
                    break
        
        # Return response in a format compatible with response processor
        return {
            "content": full_text,
            "metadata": metadata,
            "model": model,
            "usage": {
                "prompt_tokens": len(query) // 4,  # Rough estimate
                "completion_tokens": len(full_text) // 4,
                "total_tokens": (len(query) + len(full_text)) // 4
            }
        }
    
    def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> Iterator[Any]:
        """Stream chat completion (not supported in sync mode)."""
        raise NotImplementedError("Synchronous streaming not supported for Claude Code SDK")
    
    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens (approximation for Claude Code)."""
        return len(text) // 4
    
    def validate_connection(self) -> bool:
        """Validate Claude Code SDK connection."""
        try:
            # Try to import the SDK
            from claude_code_sdk import ClaudeSDKClient
            return True
        except ImportError:
            logger.error("claude-code-sdk not available")
            return False


class AsyncClaudeCodeClientWrapper(AsyncBaseClientWrapper):
    """Asynchronous Claude Code client wrapper using claude-code-sdk."""
    
    def __init__(self, config: AdapterConfig):
        """Initialize async Claude Code client wrapper."""
        super().__init__(config)
        self.logs_dir = Path(".logs")
        self.logs_dir.mkdir(exist_ok=True)
    
    async def _create_client(self) -> None:
        """Claude Code SDK doesn't use a traditional client initialization."""
        return None
    
    @asynccontextmanager
    async def _create_claude_code_client(self, system_prompt: Optional[str] = None, max_turns: int = 1):
        """Create Claude Code SDK client with async context manager."""
        try:
            from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
        except ImportError as e:
            logger.error("claude-code-sdk not installed. Install with: pip install claude-code-sdk")
            raise ImportError("claude-code-sdk is required for Claude Code support") from e
        
        # Prepare options
        options_dict = {}
        if system_prompt:
            options_dict["system_prompt"] = system_prompt
        options_dict["max_turns"] = max_turns
        
        options = ClaudeCodeOptions(**options_dict)
        
        # Create and yield client
        async with ClaudeSDKClient(options=options) as client:
            yield client
    
    def _format_messages_as_jsonl(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages in JSON Lines format similar to Claude CLI.
        
        Each message becomes a JSON object with structure:
        {"type":"<role>","message":{"role":"<role>","content":[{"type":"text","text":"<content>"}]}}
        
        System messages are included as user messages with [SYSTEM] prefix.
        """
        import json
        jsonl_lines = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Handle content that might already be structured
            if isinstance(content, list):
                content_blocks = content
            else:
                # Convert string content to content block format
                content_blocks = [{"type": "text", "text": str(content)}]
            
            # Create JSON Line entry
            # Map 'system' role to 'user' type with system indicator in content
            if role == "system":
                json_entry = {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": [{"type": "text", "text": f"[SYSTEM]: {content_blocks[0]['text']}"}]
                    }
                }
            else:
                json_entry = {
                    "type": role,
                    "message": {
                        "role": role,
                        "content": content_blocks
                    }
                }
            
            jsonl_lines.append(json.dumps(json_entry, ensure_ascii=False))
        
        # Join with newlines to create JSON Lines format
        return "\n".join(jsonl_lines)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Execute async chat completion request."""
        # Prepare query in JSON Lines format
        use_jsonl = kwargs.get("use_jsonl_format", True)  # Default to new format
        
        if use_jsonl:
            # Use structured JSON Lines format
            query = self._format_messages_as_jsonl(messages)
        else:
            # Fallback to old concatenation method
            query = "\n\n".join([
                msg.get("content", "") for msg in messages 
                if msg.get("role") != "system"
            ])
        
        if not query:
            return {
                "content": "",
                "metadata": {},
                "model": model,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
        
        # Execute with Claude Code SDK
        full_text = ""
        metadata = {}
        input_tokens = 0
        output_tokens = 0
        
        async with self._create_claude_code_client(
            system_prompt=system,
            max_turns=kwargs.get("max_turns", 1)
        ) as client:
            await client.query(query)
            
            async for message in client.receive_messages():
                # Extract content
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            full_text += block.text
                
                # Try to extract token usage
                if hasattr(message, 'usage'):
                    if hasattr(message.usage, 'input_tokens'):
                        input_tokens = message.usage.input_tokens
                    if hasattr(message.usage, 'output_tokens'):
                        output_tokens = message.usage.output_tokens
                
                # Capture metadata from ResultMessage
                if type(message).__name__ == "ResultMessage":
                    if hasattr(message, 'total_cost_usd'):
                        metadata["cost"] = message.total_cost_usd
                    if hasattr(message, 'duration_ms'):
                        metadata["duration_ms"] = message.duration_ms
                    if hasattr(message, 'num_turns'):
                        metadata["num_turns"] = message.num_turns
                    if hasattr(message, 'session_id'):
                        metadata["session_id"] = str(message.session_id) if message.session_id else None
                    break
        
        # Save log
        self._save_json_log({
            "timestamp": datetime.utcnow().isoformat(),
            "model": model,
            "query_length": len(query),
            "response_length": len(full_text),
            "metadata": metadata
        })
        
        # Return response in a format compatible with response processor
        return {
            "content": full_text,
            "metadata": metadata,
            "model": model,
            "usage": {
                "prompt_tokens": input_tokens or len(query) // 4,
                "completion_tokens": output_tokens or len(full_text) // 4,
                "total_tokens": (input_tokens + output_tokens) if (input_tokens and output_tokens) else (len(query) + len(full_text)) // 4
            }
        }
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[Any]:
        """Stream async chat completion response."""
        # Prepare query in JSON Lines format
        use_jsonl = kwargs.get("use_jsonl_format", True)  # Default to new format
        
        if use_jsonl:
            # Use structured JSON Lines format
            query = self._format_messages_as_jsonl(messages)
        else:
            # Fallback to old concatenation method
            query = "\n\n".join([
                msg.get("content", "") for msg in messages 
                if msg.get("role") != "system"
            ])
        
        if not query:
            return
        
        async with self._create_claude_code_client(
            system_prompt=system,
            max_turns=kwargs.get("max_turns", 1)
        ) as client:
            await client.query(query)
            
            async for message in client.receive_messages():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            # Yield chunks in a format compatible with streaming handler
                            yield {"delta": {"content": block.text}}
                
                # Stop on ResultMessage
                if type(message).__name__ == "ResultMessage":
                    break
    
    async def count_tokens(self, text: str, model: str) -> int:
        """Count tokens (approximation for Claude Code)."""
        return len(text) // 4
    
    async def validate_connection(self) -> bool:
        """Validate Claude Code SDK connection."""
        try:
            from claude_code_sdk import ClaudeSDKClient
            return True
        except ImportError:
            logger.error("claude-code-sdk not available")
            return False
    
    def _save_json_log(self, data: dict) -> None:
        """Save interaction data as JSON log."""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            filename = self.logs_dir / f"claude_code_chat_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.debug(f"Saved Claude Code interaction log to {filename}")
        except Exception as e:
            logger.debug(f"Skipped saving JSON log: {e}")