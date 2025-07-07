"""Factory for creating execution engines with standard observer configurations."""

import warnings
from typing import Any, Optional

from dipeo.domain.domains.execution.protocols import ExecutionObserver
from .engine import ExecutionEngine


class EngineFactory:
    """Factory for creating ExecutionEngine instances with standard configurations."""

    
    @staticmethod
    def create_engine(
        service_registry: Any,
        state_store: Optional[Any] = None,
        message_router: Optional[Any] = None,
        include_state_observer: bool = True,
        include_streaming_observer: bool = True,
        custom_observers: Optional[list[ExecutionObserver]] = None,
    ) -> ExecutionEngine:
        """Create a UnifiedExecutionEngine with standard observers.
        
        Args:
            service_registry: Service registry for handler dependencies
            state_store: State store for persistence (optional)
            message_router: Message router for streaming (optional)
            include_state_observer: Whether to include StateStoreObserver
            include_streaming_observer: Whether to include StreamingObserver
            custom_observers: Additional custom observers to include
            
        Returns:
            UnifiedExecutionEngine configured with appropriate observers
        """
        observers = []
        
        # Add state store observer if requested and available
        if include_state_observer and state_store is not None:
            from dipeo.domain.domains.execution.observers import StateStoreObserver
            observers.append(StateStoreObserver(state_store))
            
        # Add streaming observer if requested and available
        if include_streaming_observer and message_router is not None:
            from dipeo.domain.domains.execution.observers import StreamingObserver
            observers.append(StreamingObserver(message_router))
            
        # Add any custom observers
        if custom_observers:
            observers.extend(custom_observers)
            
        return ExecutionEngine(
            service_registry=service_registry,
            observers=observers,
        )
