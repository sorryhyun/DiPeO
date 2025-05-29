"""Mock utilities for testing."""

from typing import Dict, List, Tuple, Any, Optional
from unittest.mock import AsyncMock

from ...src.llm_adapters import ChatResult


class MockLLMService:
    """Mock LLM service for testing."""
    
    def __init__(self, responses: Dict[str, str] = None):
        self.responses = responses or {"default": "Test response"}
        self.call_history: List[Tuple[Any, ...]] = []
    
    async def call_llm(
        self,
        service: Optional[str],
        api_key_id: str,
        model: str,
        messages: Any,
        system_prompt: str = ""
    ) -> Tuple[str, float]:
        """Mock LLM call that records history and returns configured responses."""
        self.call_history.append((service, api_key_id, model, messages, system_prompt))
        
        # Return response based on service or default
        response_key = service or "default"
        response = self.responses.get(response_key, self.responses["default"])
        
        return response, 0.01  # Fixed cost for testing


class MockAPIKeyService:
    """Mock API key service for testing."""
    
    def __init__(self, api_keys: List[Dict[str, Any]] = None):
        self.api_keys = api_keys or [
            {
                "id": "test-key-1",
                "name": "Test OpenAI Key",
                "service": "chatgpt",
                "key": "sk-test123"
            }
        ]
    
    def list_api_keys(self) -> List[Dict[str, Any]]:
        """Return list of API keys without raw secrets."""
        return [
            {
                "id": key["id"],
                "name": key["name"],
                "service": key["service"]
            }
            for key in self.api_keys
        ]
    
    def get_api_key(self, api_key_id: str) -> Dict[str, Any]:
        """Get a specific API key."""
        for key in self.api_keys:
            if key["id"] == api_key_id:
                return key
        raise ValueError(f"API key not found: {api_key_id}")
    
    def create_api_key(self, name: str, service: str, raw_key: str) -> Dict[str, Any]:
        """Create a new API key."""
        new_key = {
            "id": f"test-key-{len(self.api_keys) + 1}",
            "name": name,
            "service": service,
            "key": raw_key
        }
        self.api_keys.append(new_key)
        return {"id": new_key["id"], "name": name, "service": service}
    
    def delete_api_key(self, api_key_id: str) -> None:
        """Delete an API key."""
        self.api_keys = [key for key in self.api_keys if key["id"] != api_key_id]


class MockMemoryService:
    """Mock memory service for testing."""
    
    def __init__(self):
        self.memory_data = {}
        self.execution_memories = {}
        
    def get_or_create_person_memory(self, person_id: str):
        """Get or create memory for a person."""
        if person_id not in self.memory_data:
            self.memory_data[person_id] = MockPersonMemory(person_id)
        return self.memory_data[person_id]
    
    async def save_conversation_log(self, execution_id: str, log_dir: str) -> str:
        """Mock save conversation log."""
        return f"{log_dir}/test_conversation_{execution_id}.json"
    
    def clear_execution_memory(self, execution_id: str) -> None:
        """Clear memory for an execution."""
        if execution_id in self.execution_memories:
            del self.execution_memories[execution_id]
    
    def clear_all_memory(self) -> None:
        """Clear all memory."""
        self.memory_data.clear()
        self.execution_memories.clear()


class MockPersonMemory:
    """Mock person memory for testing."""
    
    def __init__(self, person_id: str):
        self.person_id = person_id
        self.messages = []
        self.forgotten_message_ids = set()
    
    def add_message(self, content: str, role: str = "user", **kwargs):
        """Add a message to memory."""
        message = MockMessage(
            id=f"msg-{len(self.messages)}",
            content=content,
            role=role,
            **kwargs
        )
        self.messages.append(message)
        return message


class MockMessage:
    """Mock message for testing."""
    
    def __init__(self, id: str, content: str, role: str, **kwargs):
        self.id = id
        self.content = content
        self.role = role
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "role": self.role
        }


class MockDiagramExecutor:
    """Mock diagram executor for testing."""
    
    def __init__(self, diagram: Dict[str, Any], **kwargs):
        self.diagram = diagram
        self.execution_id = "test-exec-123"
        self.memory_stats = {"total_messages": 2, "total_cost": 0.02}
        
    async def run(self) -> Tuple[Dict[str, Any], float]:
        """Mock diagram execution."""
        context = {
            "nodes_executed": len(self.diagram.get("nodes", [])),
            "final_output": "Test execution completed"
        }
        total_cost = 0.05
        return context, total_cost
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return self.memory_stats


class MockAdapter:
    """Mock LLM adapter for testing."""
    
    def __init__(self, model: str, api_key: str, response: str = "Mock response"):
        self.model = model
        self.api_key = api_key
        self.response = response
        self.call_count = 0
    
    async def chat(self, system_prompt: str = "", user_prompt: str = "") -> ChatResult:
        """Mock chat method."""
        self.call_count += 1
        return ChatResult(
            text=f"{self.response} (call #{self.call_count})",
            usage={"input_tokens": 10, "output_tokens": 5}
        )