# Factory for creating execution engines with standard observer configurations.

import warnings
from typing import Any, Optional

from dipeo.application.execution.protocols import ExecutionObserver
from .engine.stateful_execution_engine import StatefulExecutionEngine


class EngineFactory:
    # Factory for creating ExecutionEngine instances with standard configurations.

    
    @staticmethod
    def create_engine(
        service_registry: Any,
        state_store: Optional[Any] = None,
        message_router: Optional[Any] = None,
        include_state_observer: bool = True,
        include_streaming_observer: bool = True,
        custom_observers: Optional[list[ExecutionObserver]] = None,
    ) -> StatefulExecutionEngine:
        # Create a StatefulExecutionEngine with standard observers.
        observers = []
        
        # Add state store observer if requested and available
        if include_state_observer and state_store is not None:
            from dipeo.application.execution.observers import StateStoreObserver
            observers.append(StateStoreObserver(state_store))
            
        # Add streaming observer if requested and available
        if include_streaming_observer and message_router is not None:
            from dipeo.application.execution.observers import StreamingObserver
            observers.append(StreamingObserver(message_router))
            
        # Add any custom observers
        if custom_observers:
            observers.extend(custom_observers)
        
        # Create the StatefulExecutionEngine
        return StatefulExecutionEngine(
            service_registry=service_registry,
            observers=observers,
        )
