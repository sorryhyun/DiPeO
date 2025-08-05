import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from datetime import datetime

from dipeo.application.execution.typed_engine import TypedExecutionEngine
from dipeo.core.events import EventType, ExecutionEvent, EventConsumer
from dipeo.core.execution.runtime_resolver import RuntimeResolver
from dipeo.infrastructure.events import AsyncEventBus
from dipeo.diagram_generated import (
    ExecutionState,
    NodeExecutionStatus,
    NodeID,
    NodeState,
    ExecutionStatus,
    TokenUsage,
)
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode


class EventCollector(EventConsumer):
    """Collects all events for testing."""
    
    def __init__(self):
        self.events = []
    
    async def consume(self, event: ExecutionEvent) -> None:
        self.events.append(event)
    
    def get_events_by_type(self, event_type: EventType) -> list[ExecutionEvent]:
        return [e for e in self.events if e.type == event_type]


@pytest.fixture
def mock_service_registry():
    registry = MagicMock()
    registry.get = Mock(return_value=None)
    registry.register = Mock()
    return registry


@pytest.fixture
def mock_runtime_resolver():
    resolver = Mock(spec=RuntimeResolver)
    resolver.resolve_node_inputs = Mock(return_value={})
    return resolver


@pytest.fixture
def simple_diagram():
    """Create a simple test diagram with start and end nodes."""
    # Create mock nodes
    start_node = Mock(spec=ExecutableNode)
    start_node.id = NodeID("start")
    start_node.type = "start"
    start_node.name = "Start Node"
    
    end_node = Mock(spec=ExecutableNode)
    end_node.id = NodeID("end")
    end_node.type = "end"
    end_node.name = "End Node"
    
    # Create diagram
    diagram = Mock(spec=ExecutableDiagram)
    diagram.nodes = [start_node, end_node]
    diagram.edges = []
    diagram.metadata = {"name": "Test Diagram"}
    diagram.get_node = Mock(side_effect=lambda node_id: {
        NodeID("start"): start_node,
        NodeID("end"): end_node
    }.get(node_id))
    diagram.get_outgoing_edges = Mock(return_value=[])
    
    return diagram


@pytest.fixture
def execution_state():
    state = ExecutionState(
        id="test-execution-123",
        status=ExecutionStatus.RUNNING,
        diagram_id="test-diagram-456",
        started_at=datetime.now().isoformat(),
        node_states={},
        node_outputs={},
        token_usage=TokenUsage(input=0, output=0, total=0),
        exec_counts={},
        executed_nodes=[],
        variables={}
    )
    return state


@pytest.mark.asyncio
async def test_engine_emits_lifecycle_events(
    mock_service_registry,
    mock_runtime_resolver,
    simple_diagram,
    execution_state
):
    """Test that the engine emits proper lifecycle events."""
    # Create event bus and collector
    event_bus = AsyncEventBus()
    collector = EventCollector()
    
    # Subscribe to all event types
    for event_type in EventType:
        event_bus.subscribe(event_type, collector)
    
    await event_bus.start()
    
    # Create engine with event bus
    engine = TypedExecutionEngine(
        service_registry=mock_service_registry,
        runtime_resolver=mock_runtime_resolver,
        event_bus=event_bus
    )
    
    # Mock handler factory
    mock_handler = AsyncMock()
    mock_handler.execute = AsyncMock(return_value=Mock(value="result", metadata={}))
    
    mock_registry = MagicMock()
    mock_registry.create_handler = Mock(return_value=mock_handler)
    
    # Patch get_global_registry
    import dipeo.application
    dipeo.application.get_global_registry = Mock(return_value=mock_registry)
    
    # Execute diagram
    results = []
    async for step in engine.execute(simple_diagram, execution_state, {}):
        results.append(step)
    
    # Allow events to propagate
    await asyncio.sleep(0.1)
    
    # Verify lifecycle events
    start_events = collector.get_events_by_type(EventType.EXECUTION_STARTED)
    assert len(start_events) == 1
    assert start_events[0].execution_id == "test-execution-123"
    assert start_events[0].data["diagram_id"] == "test-diagram-456"
    
    node_start_events = collector.get_events_by_type(EventType.NODE_STARTED)
    assert len(node_start_events) >= 2  # Start and end nodes
    
    node_complete_events = collector.get_events_by_type(EventType.NODE_COMPLETED)
    assert len(node_complete_events) >= 2  # Start and end nodes
    
    complete_events = collector.get_events_by_type(EventType.EXECUTION_COMPLETED)
    assert len(complete_events) == 1
    
    # Cleanup
    await event_bus.stop()


@pytest.mark.asyncio
async def test_engine_metrics_in_events(
    mock_service_registry,
    mock_runtime_resolver,
    simple_diagram,
    execution_state
):
    """Test that node completion events include metrics."""
    event_bus = AsyncEventBus()
    collector = EventCollector()
    
    event_bus.subscribe(EventType.NODE_COMPLETED, collector)
    await event_bus.start()
    
    engine = TypedExecutionEngine(
        service_registry=mock_service_registry,
        runtime_resolver=mock_runtime_resolver,
        event_bus=event_bus
    )
    
    # Mock handler with delay
    mock_handler = AsyncMock()
    async def delayed_execute(*args, **kwargs):
        await asyncio.sleep(0.01)  # Small delay
        return Mock(value="result", metadata={})
    
    mock_handler.execute = delayed_execute
    
    mock_registry = MagicMock()
    mock_registry.create_handler = Mock(return_value=mock_handler)
    
    import dipeo.application
    dipeo.application.get_global_registry = Mock(return_value=mock_registry)
    
    # Execute
    async for _ in engine.execute(simple_diagram, execution_state, {}):
        pass
    
    await asyncio.sleep(0.1)
    
    # Check metrics
    for event in collector.events:
        assert "metrics" in event.data
        metrics = event.data["metrics"]
        assert "duration_ms" in metrics
        assert metrics["duration_ms"] >= 10  # At least 10ms due to delay
        assert "start_time" in metrics
        assert "end_time" in metrics
    
    await event_bus.stop()


@pytest.mark.asyncio
async def test_engine_handles_node_failure(
    mock_service_registry,
    mock_runtime_resolver,
    simple_diagram,
    execution_state
):
    """Test that node failures emit proper events."""
    event_bus = AsyncEventBus()
    collector = EventCollector()
    
    event_bus.subscribe(EventType.NODE_FAILED, collector)
    await event_bus.start()
    
    engine = TypedExecutionEngine(
        service_registry=mock_service_registry,
        runtime_resolver=mock_runtime_resolver,
        event_bus=event_bus
    )
    
    # Mock handler that fails
    mock_handler = AsyncMock()
    mock_handler.execute = AsyncMock(side_effect=ValueError("Test error"))
    
    mock_registry = MagicMock()
    mock_registry.create_handler = Mock(return_value=mock_handler)
    
    import dipeo.application
    dipeo.application.get_global_registry = Mock(return_value=mock_registry)
    
    # Execute and expect failure
    with pytest.raises(ValueError):
        async for _ in engine.execute(simple_diagram, execution_state, {}):
            pass
    
    await asyncio.sleep(0.1)
    
    # Verify failure events
    assert len(collector.events) >= 1
    failure_event = collector.events[0]
    assert failure_event.data["error"] == "Test error"
    assert failure_event.data["error_type"] == "ValueError"
    
    await event_bus.stop()


@pytest.mark.asyncio
async def test_engine_parallel_execution_with_events(
    mock_service_registry,
    mock_runtime_resolver,
    execution_state
):
    """Test that parallel node execution emits events correctly."""
    # Create diagram with parallel nodes
    nodes = []
    for i in range(5):
        node = Mock(spec=ExecutableNode)
        node.id = NodeID(f"node_{i}")
        node.type = "test"
        node.name = f"Node {i}"
        nodes.append(node)
    
    diagram = Mock(spec=ExecutableDiagram)
    diagram.nodes = nodes
    diagram.edges = []
    diagram.metadata = {"name": "Parallel Test"}
    diagram.get_node = Mock(side_effect=lambda node_id: {
        node.id: node for node in nodes
    }.get(node_id))
    diagram.get_outgoing_edges = Mock(return_value=[])
    
    # Event tracking
    event_bus = AsyncEventBus()
    collector = EventCollector()
    
    event_bus.subscribe(EventType.NODE_STARTED, collector)
    event_bus.subscribe(EventType.NODE_COMPLETED, collector)
    await event_bus.start()
    
    engine = TypedExecutionEngine(
        service_registry=mock_service_registry,
        runtime_resolver=mock_runtime_resolver,
        event_bus=event_bus
    )
    
    # Mock handler with varying delays
    execution_order = []
    
    async def track_execution(node, *args, **kwargs):
        execution_order.append(str(node.id))
        await asyncio.sleep(0.01)  # Small delay
        return Mock(value=f"result_{node.id}", metadata={})
    
    mock_handler = AsyncMock()
    mock_handler.execute = track_execution
    
    mock_registry = MagicMock()
    mock_registry.create_handler = Mock(return_value=mock_handler)
    
    import dipeo.application
    dipeo.application.get_global_registry = Mock(return_value=mock_registry)
    
    # Execute
    async for _ in engine.execute(diagram, execution_state, {}):
        pass
    
    await asyncio.sleep(0.1)
    
    # Verify parallel execution occurred
    start_events = collector.get_events_by_type(EventType.NODE_STARTED)
    complete_events = collector.get_events_by_type(EventType.NODE_COMPLETED)
    
    assert len(start_events) == 5
    assert len(complete_events) == 5
    
    # Check that all nodes were executed
    executed_nodes = {e.data["node_id"] for e in complete_events}
    expected_nodes = {f"node_{i}" for i in range(5)}
    assert executed_nodes == expected_nodes
    
    await event_bus.stop()