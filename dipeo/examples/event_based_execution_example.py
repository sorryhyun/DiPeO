"""Example of using the TypedExecutionEngine with event-based monitoring.

This demonstrates how to:
1. Create event consumers for monitoring
2. Wire up the event bus
3. Execute diagrams with decoupled event handling
"""

import asyncio
import logging
from dipeo.core.events import EventType, ExecutionEvent, EventConsumer
from dipeo.infrastructure.events import AsyncEventBus
from dipeo.application.execution.typed_engine import TypedExecutionEngine


class MetricsCollector(EventConsumer):
    """Collects execution metrics without blocking execution."""
    
    def __init__(self):
        self.node_durations = {}
        self.failed_nodes = []
    
    async def consume(self, event: ExecutionEvent) -> None:
        if event.type == EventType.NODE_COMPLETED:
            metrics = event.data.get("metrics", {})
            if "duration_ms" in metrics:
                self.node_durations[event.data["node_id"]] = metrics["duration_ms"]
        
        elif event.type == EventType.NODE_FAILED:
            self.failed_nodes.append({
                "node_id": event.data["node_id"],
                "error": event.data["error"]
            })


class RealtimeMonitor(EventConsumer):
    """Streams execution updates to UI or logs."""
    
    async def consume(self, event: ExecutionEvent) -> None:
        if event.type == EventType.NODE_STARTED:
            print(f"▶ Started: {event.data['node_name']} ({event.data['node_type']})")
        
        elif event.type == EventType.NODE_COMPLETED:
            duration = event.data.get("metrics", {}).get("duration_ms", 0)
            print(f"✓ Completed: {event.data['node_name']} in {duration:.1f}ms")
        
        elif event.type == EventType.NODE_FAILED:
            print(f"✗ Failed: {event.data['node_name']} - {event.data['error']}")


async def run_with_monitoring(diagram, execution_state, service_registry):
    """Execute a diagram with event-based monitoring."""
    
    # Create event bus
    event_bus = AsyncEventBus()
    
    # Create and subscribe consumers
    metrics = MetricsCollector()
    monitor = RealtimeMonitor()
    
    event_bus.subscribe(EventType.NODE_STARTED, monitor)
    event_bus.subscribe(EventType.NODE_COMPLETED, monitor)
    event_bus.subscribe(EventType.NODE_COMPLETED, metrics)
    event_bus.subscribe(EventType.NODE_FAILED, monitor)
    event_bus.subscribe(EventType.NODE_FAILED, metrics)
    
    # Start event bus
    await event_bus.start()
    
    # Create engine with event bus
    engine = TypedExecutionEngine(
        service_registry=service_registry,
        runtime_resolver=runtime_resolver,
        event_bus=event_bus
    )
    
    # Execute diagram
    async for step in engine.execute(diagram, execution_state, {}):
        if step["type"] == "execution_complete":
            print(f"\n📊 Metrics Summary:")
            print(f"Total nodes executed: {len(metrics.node_durations)}")
            print(f"Failed nodes: {len(metrics.failed_nodes)}")
            if metrics.node_durations:
                avg_duration = sum(metrics.node_durations.values()) / len(metrics.node_durations)
                print(f"Average node duration: {avg_duration:.1f}ms")
    
    # Cleanup
    await event_bus.stop()


# Usage:
# await run_with_monitoring(diagram, execution_state, service_registry)