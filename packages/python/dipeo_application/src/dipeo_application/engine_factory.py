"""Factory for creating execution engines with standard observer configurations."""

from typing import Any, Optional

from .execution_engine import ExecutionEngine, ExecutionObserver


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
        """Create an ExecutionEngine with standard observers.

        Args:
            service_registry: Service registry for handler dependencies
            state_store: State store for persistence (optional)
            message_router: Message router for streaming (optional)
            include_state_observer: Whether to include StateStoreObserver
            include_streaming_observer: Whether to include StreamingObserver
            custom_observers: Additional custom observers to include

        Returns:
            ExecutionEngine configured with appropriate observers
        """
        observers = []

        # Add state store observer if requested and available
        if include_state_observer and state_store is not None:
            # Import here to avoid circular dependencies
            from dipeo_domain.domains.execution.observers import StateStoreObserver

            observers.append(StateStoreObserver(state_store))

        # Add streaming observer if requested and available
        if include_streaming_observer and message_router is not None:
            from dipeo_domain.domains.execution.observers import StreamingObserver

            observers.append(StreamingObserver(message_router))

        # Add any custom observers
        if custom_observers:
            observers.extend(custom_observers)

        return ExecutionEngine(
            service_registry=service_registry,
            observers=observers,
        )

    @staticmethod
    def create_cli_engine(service_registry: Any) -> ExecutionEngine:
        """Create a minimal engine for CLI usage without persistence or streaming."""
        return ExecutionEngine(
            service_registry=service_registry,
            observers=[],  # No observers for CLI
        )

    @staticmethod
    def create_server_engine(
        service_registry: Any,
        state_store: Any,
        message_router: Any,
    ) -> ExecutionEngine:
        """Create a full-featured engine for server usage with all standard observers."""
        return EngineFactory.create_engine(
            service_registry=service_registry,
            state_store=state_store,
            message_router=message_router,
            include_state_observer=True,
            include_streaming_observer=True,
        )

    @staticmethod
    def create_test_engine(
        service_registry: Any,
        observers: Optional[list[ExecutionObserver]] = None,
    ) -> ExecutionEngine:
        """Create an engine for testing with custom observers."""
        return ExecutionEngine(
            service_registry=service_registry,
            observers=observers or [],
        )
