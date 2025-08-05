import asyncio
import pytest
from dipeo.core.events import EventType, ExecutionEvent, EventConsumer
from dipeo.infrastructure.events import AsyncEventBus


class MockConsumer(EventConsumer):
    def __init__(self):
        self.events = []
    
    async def consume(self, event: ExecutionEvent) -> None:
        self.events.append(event)


@pytest.mark.asyncio
async def test_event_emission():
    bus = AsyncEventBus()
    consumer = MockConsumer()
    bus.subscribe(EventType.NODE_STARTED, consumer)
    
    await bus.start()
    
    event = ExecutionEvent(
        type=EventType.NODE_STARTED,
        execution_id="test-123",
        timestamp=1234567890,
        data={"node_id": "node-1"}
    )
    
    await bus.emit(event)
    await asyncio.sleep(0.01)  # Allow processing
    
    assert len(consumer.events) == 1
    assert consumer.events[0].execution_id == "test-123"
    
    await bus.stop()


@pytest.mark.asyncio
async def test_multiple_subscribers():
    bus = AsyncEventBus()
    consumer1 = MockConsumer()
    consumer2 = MockConsumer()
    
    bus.subscribe(EventType.NODE_COMPLETED, consumer1)
    bus.subscribe(EventType.NODE_COMPLETED, consumer2)
    
    await bus.start()
    
    event = ExecutionEvent(
        type=EventType.NODE_COMPLETED,
        execution_id="test-456",
        timestamp=1234567890,
        data={"node_id": "node-2"}
    )
    
    await bus.emit(event)
    await asyncio.sleep(0.01)
    
    assert len(consumer1.events) == 1
    assert len(consumer2.events) == 1
    
    await bus.stop()


@pytest.mark.asyncio
async def test_event_filtering():
    bus = AsyncEventBus()
    consumer = MockConsumer()
    
    bus.subscribe(EventType.NODE_FAILED, consumer)
    
    await bus.start()
    
    # Emit different event type
    event = ExecutionEvent(
        type=EventType.NODE_STARTED,
        execution_id="test-789",
        timestamp=1234567890,
        data={}
    )
    
    await bus.emit(event)
    await asyncio.sleep(0.01)
    
    assert len(consumer.events) == 0
    
    await bus.stop()


@pytest.mark.asyncio
async def test_queue_overflow():
    bus = AsyncEventBus(queue_size=2)
    
    class SlowConsumer(EventConsumer):
        async def consume(self, event: ExecutionEvent) -> None:
            await asyncio.sleep(1)  # Simulate slow processing
    
    consumer = SlowConsumer()
    bus.subscribe(EventType.NODE_STARTED, consumer)
    
    await bus.start()
    
    # Emit more events than queue can handle
    for i in range(5):
        event = ExecutionEvent(
            type=EventType.NODE_STARTED,
            execution_id=f"test-{i}",
            timestamp=1234567890,
            data={}
        )
        await bus.emit(event)
    
    # No exception should be raised
    await bus.stop()