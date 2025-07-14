"""Advanced forgetting strategies for the global conversation model."""

from typing import Protocol, Optional, Dict, Any
from abc import abstractmethod
from dipeo.models import ForgettingMode, PersonID, MemoryConfig
from .memory_filters import MemoryView
from .person import Person

class ForgettingStrategy(Protocol):
    """Protocol for forgetting strategies."""
    
    @abstractmethod
    def apply(self, person: "Person", memory_config: MemoryConfig, execution_count: int) -> int:
        """Apply the forgetting strategy to a person's memory.
        
        Returns:
            Number of messages affected
        """
        ...
    
    @abstractmethod
    def describe(self) -> str:
        """Return a human-readable description of this strategy."""
        ...


class NoForgetStrategy:
    """Never forget anything - maintain full memory."""
    
    def apply(self, person: "Person", memory_config: MemoryConfig, execution_count: int) -> int:
        # Ensure person uses full view with no limits
        person.set_memory_view(MemoryView.ALL_INVOLVED)
        if person._memory_limiter:
            person._memory_limiter = None
        return 0
    
    def describe(self) -> str:
        return "Keep all messages - never forget"


class OnEveryTurnStrategy:
    """Forget messages after each turn, keeping only recent context."""
    
    def __init__(
        self, 
        keep_last_n_exchanges: int = 2,
        preserve_system: bool = True,
        context_window: int = 10
    ):
        self.keep_last_n_exchanges = keep_last_n_exchanges
        self.preserve_system = preserve_system
        self.context_window = context_window
    
    def apply(self, person: "Person", memory_config: MemoryConfig, execution_count: int) -> int:
        if execution_count == 0:
            # First execution - no forgetting needed
            return 0
        
        original_count = person.get_message_count()
        
        # Switch to conversation pairs view to see exchanges
        person.set_memory_view(MemoryView.CONVERSATION_PAIRS)
        
        # Apply memory limit based on configuration
        max_messages = memory_config.max_messages or self.context_window
        person.set_memory_limit(int(max_messages), preserve_system=self.preserve_system)
        
        return original_count - person.get_message_count()
    
    def describe(self) -> str:
        return f"Keep last {self.keep_last_n_exchanges} exchanges on every turn"


class UponRequestStrategy:
    """Forget messages only when explicitly requested."""
    
    def __init__(self, minimal_view: MemoryView = MemoryView.SYSTEM_AND_ME):
        self.minimal_view = minimal_view
    
    def apply(self, person: "Person", memory_config: MemoryConfig, execution_count: int) -> int:
        # This strategy is typically triggered externally
        # When applied, switch to minimal view
        original_count = person.get_message_count()
        
        person.set_memory_view(self.minimal_view)
        
        # Apply strict memory limit
        max_messages = memory_config.max_messages or 5
        person.set_memory_limit(int(max_messages), preserve_system=True)
        
        return original_count - person.get_message_count()
    
    def describe(self) -> str:
        return "Forget only when explicitly requested"


class ForgettingStrategyFactory:
    """Factory for creating forgetting strategies."""
    
    _strategies: Dict[ForgettingMode, type[ForgettingStrategy]] = {
        ForgettingMode.no_forget: NoForgetStrategy,
        ForgettingMode.on_every_turn: OnEveryTurnStrategy,
        ForgettingMode.upon_request: UponRequestStrategy,
    }
    
    
    @classmethod
    def create(
        cls, 
        mode: ForgettingMode,
        **kwargs
    ) -> ForgettingStrategy:
        """Create a forgetting strategy for the specified mode."""
        strategy_class = cls._strategies.get(mode)
        if not strategy_class:
            raise ValueError(f"Unknown forgetting mode: {mode}")
        
        # Pass any kwargs to the strategy constructor
        return strategy_class(**kwargs)
    
