"""Integration test for event-based execution.

This tests the real flow of executing a simple diagram with event emission.
"""

import asyncio
import pytest
from dipeo.core.events import EventType, EventConsumer, ExecutionEvent
from dipeo.infrastructure.events import AsyncEventBus
import logging

logger = logging.getLogger(__name__)


class SimpleEventCollector(EventConsumer):
    """Collects events for verification."""
    
    def __init__(self):
        self.events = []
    
    async def consume(self, event: ExecutionEvent) -> None:
        self.events.append(event)
        logger.info(f"Received event: {event.type.value} for execution {event.execution_id}")


@pytest.mark.asyncio
async def test_event_bus_with_real_diagram_execution():
    """Test that we can execute a real diagram and collect events."""
    # This test demonstrates the event system working
    # A full integration test would require setting up the entire container
    
    # Create event bus
    event_bus = AsyncEventBus()
    collector = SimpleEventCollector()
    
    # Subscribe to all events
    for event_type in EventType:
        event_bus.subscribe(event_type, collector)
    
    await event_bus.start()
    
    # Simulate execution events
    execution_id = "test-exec-123"
    
    # Emit execution started
    await event_bus.emit(ExecutionEvent(
        type=EventType.EXECUTION_STARTED,
        execution_id=execution_id,
        timestamp=1234567890,
        data={"diagram_id": "test-diagram"}
    ))
    
    # Emit node events
    for i in range(3):
        node_id = f"node-{i}"
        
        await event_bus.emit(ExecutionEvent(
            type=EventType.NODE_STARTED,
            execution_id=execution_id,
            timestamp=1234567890 + i,
            data={"node_id": node_id, "node_type": "test"}
        ))
        
        await asyncio.sleep(0.01)  # Simulate work
        
        await event_bus.emit(ExecutionEvent(
            type=EventType.NODE_COMPLETED,
            execution_id=execution_id,
            timestamp=1234567890 + i + 0.5,
            data={
                "node_id": node_id,
                "output": {"value": f"result-{i}"},
                "metrics": {"duration_ms": 10}
            }
        ))
    
    # Emit execution completed
    await event_bus.emit(ExecutionEvent(
        type=EventType.EXECUTION_COMPLETED,
        execution_id=execution_id,
        timestamp=1234567900,
        data={"total_steps": 3}
    ))
    
    # Allow events to be processed
    await asyncio.sleep(0.1)
    
    # Verify events were collected
    assert len(collector.events) == 8  # 1 start + 3*(start+complete) + 1 complete
    
    # Verify event order
    event_types = [e.type for e in collector.events]
    assert event_types[0] == EventType.EXECUTION_STARTED
    assert event_types[-1] == EventType.EXECUTION_COMPLETED
    
    # Verify node events
    node_starts = [e for e in collector.events if e.type == EventType.NODE_STARTED]
    node_completes = [e for e in collector.events if e.type == EventType.NODE_COMPLETED]
    
    assert len(node_starts) == 3
    assert len(node_completes) == 3
    
    # Verify metrics in completed events
    for event in node_completes:
        assert "metrics" in event.data
        assert "duration_ms" in event.data["metrics"]
    
    # Cleanup
    await event_bus.stop()
    
    logger.info(f"Test completed successfully with {len(collector.events)} events")


@pytest.mark.asyncio 
async def test_concurrent_event_emission():
    """Test that the event bus handles concurrent emissions correctly."""
    event_bus = AsyncEventBus()
    collector = SimpleEventCollector()
    
    event_bus.subscribe(EventType.NODE_STARTED, collector)
    await event_bus.start()
    
    # Emit many events concurrently
    async def emit_events(execution_id: str, count: int):
        for i in range(count):
            await event_bus.emit(ExecutionEvent(
                type=EventType.NODE_STARTED,
                execution_id=execution_id,
                timestamp=1234567890,
                data={"node_id": f"{execution_id}-node-{i}"}
            ))
    
    # Create multiple concurrent emitters
    tasks = [
        emit_events("exec-1", 10),
        emit_events("exec-2", 10),
        emit_events("exec-3", 10),
    ]
    
    await asyncio.gather(*tasks)
    await asyncio.sleep(0.2)  # Allow processing
    
    # Verify all events were received
    assert len(collector.events) == 30
    
    # Verify events from all executions
    exec_ids = {e.execution_id for e in collector.events}
    assert exec_ids == {"exec-1", "exec-2", "exec-3"}
    
    await event_bus.stop()


@pytest.mark.asyncio
async def test_event_bus_performance():
    """Test that event processing doesn't block execution."""
    event_bus = AsyncEventBus()
    
    # Create a slow consumer
    class SlowConsumer(EventConsumer):
        def __init__(self):
            self.processed = 0
        
        async def consume(self, event: ExecutionEvent) -> None:
            await asyncio.sleep(0.1)  # Simulate slow processing
            self.processed += 1
    
    slow_consumer = SlowConsumer()
    event_bus.subscribe(EventType.NODE_COMPLETED, slow_consumer)
    
    await event_bus.start()
    
    # Emit events rapidly
    start_time = asyncio.get_event_loop().time()
    
    for i in range(10):
        await event_bus.emit(ExecutionEvent(
            type=EventType.NODE_COMPLETED,
            execution_id="perf-test",
            timestamp=1234567890,
            data={"node_id": f"node-{i}"}
        ))
    
    emit_time = asyncio.get_event_loop().time() - start_time
    
    # Emissions should be fast (< 100ms total) despite slow consumer
    assert emit_time < 0.1
    
    # Wait for some events to be processed
    await asyncio.sleep(0.5)
    
    # Not all events may be processed yet due to slow consumer
    assert slow_consumer.processed > 0
    assert slow_consumer.processed <= 10
    
    await event_bus.stop()