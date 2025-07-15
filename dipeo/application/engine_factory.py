# Factory for creating execution engines with standard observer configurations.

from typing import Any

from dipeo.core.ports import ExecutionObserver

from .engine.typed_execution_engine import TypedExecutionEngine


class EngineFactory:
    # Factory for creating ExecutionEngine instances with standard configurations.

    
    @staticmethod
    def create_engine(
        service_registry: Any,
        state_store: Any | None = None,
        message_router: Any | None = None,
        include_state_observer: bool = True,
        include_streaming_observer: bool = True,
        custom_observers: list[ExecutionObserver] | None = None,
    ) -> TypedExecutionEngine:
        # Create a TypedExecutionEngine with standard observers.
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
        
        # Create the TypedExecutionEngine
        return TypedExecutionEngine(
            service_registry=service_registry,
            observers=observers,
        )
