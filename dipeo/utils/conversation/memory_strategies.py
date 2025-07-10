"""Memory management strategies for conversations."""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import json
from datetime import datetime


class MemoryStrategy(ABC):
    """Base class for memory strategies."""
    
    @abstractmethod
    def apply(self, messages: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply the memory strategy to a list of messages."""
        pass
    
    @abstractmethod
    def get_summary(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Get a summary of the messages if applicable."""
        pass


class FullMemoryStrategy(MemoryStrategy):
    """Keep all messages in memory."""
    
    def apply(self, messages: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return all messages unchanged."""
        return messages
    
    def get_summary(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """No summary needed for full memory."""
        return None


class WindowMemoryStrategy(MemoryStrategy):
    """Keep only the last N messages."""
    
    def apply(self, messages: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Keep only the last window_size messages."""
        window_size = config.get('window_size', 10)
        if len(messages) <= window_size:
            return messages
        
        # Always keep the first message (usually system prompt)
        first_message = messages[0] if messages else None
        recent_messages = messages[-window_size+1:] if first_message else messages[-window_size:]
        
        result = []
        if first_message:
            result.append(first_message)
        result.extend(recent_messages)
        
        return result
    
    def get_summary(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Get summary of dropped messages."""
        window_size = config.get('window_size', 10)
        if len(messages) <= window_size:
            return None
        
        dropped_count = len(messages) - window_size
        return f"[{dropped_count} previous messages omitted]"


class SummaryMemoryStrategy(MemoryStrategy):
    """Summarize older messages and keep recent ones."""
    
    def apply(self, messages: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Summarize older messages and keep recent ones."""
        summary_threshold = config.get('summary_threshold', 20)
        keep_recent = config.get('keep_recent', 5)
        
        if len(messages) <= summary_threshold:
            return messages
        
        # Split messages
        to_summarize = messages[:-keep_recent]
        recent = messages[-keep_recent:]
        
        # Create summary message
        summary = self.get_summary(to_summarize)
        summary_message = {
            "role": "system",
            "content": f"Previous conversation summary:\n{summary}",
            "metadata": {
                "type": "summary",
                "message_count": len(to_summarize),
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
        return [summary_message] + recent
    
    def get_summary(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Create a summary of messages."""
        if not messages:
            return None
        
        # Simple summary implementation
        summary_parts = []
        
        # Count messages by role
        role_counts = {}
        for msg in messages:
            role = msg.get('role', 'unknown')
            role_counts[role] = role_counts.get(role, 0) + 1
        
        summary_parts.append(f"Total messages: {len(messages)}")
        for role, count in role_counts.items():
            summary_parts.append(f"{role}: {count} messages")
        
        # Extract key topics (simplified)
        topics = set()
        for msg in messages[-5:]:  # Look at last 5 messages
            content = msg.get('content', '')
            # Simple keyword extraction
            words = content.lower().split()
            for word in words:
                if len(word) > 5 and word.isalpha():
                    topics.add(word)
        
        if topics:
            summary_parts.append(f"Recent topics: {', '.join(list(topics)[:5])}")
        
        return "\n".join(summary_parts)


class TokenLimitMemoryStrategy(MemoryStrategy):
    """Keep messages within a token limit."""
    
    def apply(self, messages: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Keep messages within token limit."""
        max_tokens = config.get('max_tokens', 4000)
        
        # Simple token estimation (4 chars = 1 token)
        def estimate_tokens(message: Dict[str, Any]) -> int:
            content = message.get('content', '')
            return len(content) // 4
        
        # Calculate total tokens
        total_tokens = sum(estimate_tokens(msg) for msg in messages)
        
        if total_tokens <= max_tokens:
            return messages
        
        # Remove messages from the middle, keeping first and last
        result = []
        current_tokens = 0
        
        # Always keep first message
        if messages:
            result.append(messages[0])
            current_tokens += estimate_tokens(messages[0])
        
        # Add messages from the end
        for msg in reversed(messages[1:]):
            msg_tokens = estimate_tokens(msg)
            if current_tokens + msg_tokens <= max_tokens:
                result.insert(1, msg)  # Insert after first message
                current_tokens += msg_tokens
            else:
                break
        
        return result
    
    def get_summary(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Get summary of token usage."""
        total_tokens = sum(len(msg.get('content', '')) // 4 for msg in messages)
        return f"Total estimated tokens: {total_tokens}"


class MemoryStrategyFactory:
    """Factory for creating memory strategies."""
    
    STRATEGIES = {
        'full': FullMemoryStrategy,
        'window': WindowMemoryStrategy,
        'summary': SummaryMemoryStrategy,
        'token_limit': TokenLimitMemoryStrategy,
    }
    
    @classmethod
    def create(cls, strategy_type: str) -> MemoryStrategy:
        """Create a memory strategy instance."""
        strategy_class = cls.STRATEGIES.get(strategy_type, FullMemoryStrategy)
        return strategy_class()
    
    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """Get list of available strategy types."""
        return list(cls.STRATEGIES.keys())