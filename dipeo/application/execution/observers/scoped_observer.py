"""Scoped observer implementation for sub-diagram execution filtering."""

from dataclasses import dataclass, field
from typing import Optional, List
import logging

from dipeo.application.execution.observer_protocol import ExecutionObserver
from dipeo.diagram_generated import NodeState

logger = logging.getLogger(__name__)


@dataclass
class ObserverMetadata:
    """Metadata for observer behavior in sub-diagram execution."""
    propagate_to_sub: bool = True
    scope_to_execution: bool = False
    filter_events: Optional[List[str]] = None


class ScopedObserver(ExecutionObserver):
    """
    Observer wrapper that filters events based on execution scope.
    
    This allows parent observers to control which events they receive
    from sub-diagram executions.
    """
    
    def __init__(
        self, 
        base_observer: ExecutionObserver, 
        scope: str,
        metadata: Optional[ObserverMetadata] = None
    ):
        """
        Initialize scoped observer.
        
        Args:
            base_observer: The underlying observer to wrap
            scope: Execution scope (usually parent execution ID)
            metadata: Observer behavior configuration
        """
        self.base_observer = base_observer
        self.scope = scope
        self.metadata = metadata or ObserverMetadata()
        
    def should_propagate(self, execution_id: str, event_type: str) -> bool:
        """
        Check if observer should handle events from the given execution context.
        
        Args:
            execution_id: The execution ID generating the event
            event_type: Type of event (e.g., 'node_start', 'node_complete')
            
        Returns:
            True if the event should be propagated to the base observer
        """
        # Check if observer is scoped to specific execution
        if self.metadata.scope_to_execution:
            # Only handle events from the scoped execution (not sub-executions)
            if not execution_id.startswith(self.scope):
                logger.debug(
                    f"Filtering out event {event_type} from {execution_id} "
                    f"(not in scope {self.scope})"
                )
                return False
                
        # Check event type filtering
        if self.metadata.filter_events:
            if event_type not in self.metadata.filter_events:
                logger.debug(
                    f"Filtering out event {event_type} from {execution_id} "
                    f"(not in filter list)"
                )
                return False
                
        return True
    
    async def on_execution_start(
        self, execution_id: str, diagram_id: str | None
    ) -> None:
        """Forward execution start event if in scope."""
        if self.should_propagate(execution_id, 'execution_start'):
            await self.base_observer.on_execution_start(execution_id, diagram_id)
    
    async def on_node_start(self, execution_id: str, node_id: str) -> None:
        """Forward node start event if in scope."""
        if self.should_propagate(execution_id, 'node_start'):
            await self.base_observer.on_node_start(execution_id, node_id)
    
    async def on_node_complete(
        self, execution_id: str, node_id: str, state: NodeState
    ) -> None:
        """Forward node complete event if in scope."""
        if self.should_propagate(execution_id, 'node_complete'):
            await self.base_observer.on_node_complete(execution_id, node_id, state)
    
    async def on_node_error(
        self, execution_id: str, node_id: str, error: str
    ) -> None:
        """Forward node error event if in scope."""
        if self.should_propagate(execution_id, 'node_error'):
            await self.base_observer.on_node_error(execution_id, node_id, error)
    
    async def on_execution_complete(self, execution_id: str) -> None:
        """Forward execution complete event if in scope."""
        if self.should_propagate(execution_id, 'execution_complete'):
            await self.base_observer.on_execution_complete(execution_id)
    
    async def on_execution_error(self, execution_id: str, error: str) -> None:
        """Forward execution error event if in scope."""
        if self.should_propagate(execution_id, 'execution_error'):
            await self.base_observer.on_execution_error(execution_id, error)


def create_scoped_observers(
    observers: List[ExecutionObserver],
    parent_execution_id: str,
    sub_execution_id: str,
    inherit_all: bool = True
) -> List[ExecutionObserver]:
    """
    Create scoped observers for sub-diagram execution.
    
    Args:
        observers: List of parent observers
        parent_execution_id: Parent execution ID (for scoping)
        sub_execution_id: Sub-diagram execution ID
        inherit_all: If True, all observers are inherited; if False, only those 
                    with propagate_to_sub=True
    
    Returns:
        List of observers appropriate for the sub-diagram execution
    """
    scoped_observers = []
    
    for observer in observers:
        # Check if observer has metadata
        metadata = getattr(observer, 'metadata', None)
        if metadata is None:
            metadata = ObserverMetadata()
            
        # Check if observer should propagate to sub-diagrams
        if not inherit_all and not metadata.propagate_to_sub:
            logger.debug(
                f"Observer {observer.__class__.__name__} not propagating to sub-diagram"
            )
            continue
            
        # If observer is already scoped, use its base observer
        if isinstance(observer, ScopedObserver):
            base_observer = observer.base_observer
            # Preserve original metadata but update scope
            scoped_observer = ScopedObserver(
                base_observer=base_observer,
                scope=parent_execution_id,
                metadata=observer.metadata
            )
        else:
            # Create new scoped observer
            scoped_observer = ScopedObserver(
                base_observer=observer,
                scope=parent_execution_id,
                metadata=metadata
            )
            
        scoped_observers.append(scoped_observer)
        
    return scoped_observers