"""GraphQL subscriptions for real-time updates."""

import asyncio
import logging
from typing import AsyncGenerator, Optional

import strawberry

from dipeo.application.unified_service_registry import UnifiedServiceRegistry, ServiceKey
from dipeo.core.ports import MessageRouterPort, StateStorePort
from strawberry.scalars import JSON as JSONScalar
from dipeo.diagram_generated.domain_models import ExecutionID
from dipeo.diagram_generated.enums import EventType

logger = logging.getLogger(__name__)

# Service keys
MESSAGE_ROUTER = ServiceKey[MessageRouterPort]("message_router")
STATE_STORE = ServiceKey[StateStorePort]("state_store")


@strawberry.type
class ExecutionUpdate:
    """Real-time execution update."""
    execution_id: str
    event_type: str
    data: JSONScalar
    timestamp: str


def create_subscription_type(registry: UnifiedServiceRegistry) -> type:
    """Create a Subscription type with injected service registry."""
    
    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def execution_updates(
            self, execution_id: strawberry.ID
        ) -> AsyncGenerator[ExecutionUpdate, None]:
            """Subscribe to real-time updates for an execution."""
            message_router = registry.get(MESSAGE_ROUTER.name)
            state_store = registry.get(STATE_STORE.name)
            
            if not message_router:
                logger.error("Message router not available for subscriptions")
                return
            
            exec_id = ExecutionID(str(execution_id))
            
            try:
                # Verify execution exists
                if state_store:
                    execution = await state_store.get_execution(exec_id)
                    if not execution:
                        logger.warning(f"Execution not found: {exec_id}")
                        return
                
                # Subscribe to execution events
                async for event in message_router.subscribe_to_execution(exec_id):
                    yield ExecutionUpdate(
                        execution_id=str(exec_id),
                        event_type=event.get("type", "unknown"),
                        data=event.get("data", {}),
                        timestamp=event.get("timestamp", ""),
                    )
                    
            except asyncio.CancelledError:
                logger.info(f"Subscription cancelled for execution: {exec_id}")
                raise
            except Exception as e:
                logger.error(f"Error in execution subscription: {e}")
                raise
        
        @strawberry.subscription
        async def node_updates(
            self, execution_id: strawberry.ID, node_id: Optional[str] = None
        ) -> AsyncGenerator[JSONScalar, None]:
            """Subscribe to node-specific updates within an execution."""
            message_router = registry.get(MESSAGE_ROUTER.name)
            
            if not message_router:
                logger.error("Message router not available for subscriptions")
                return
            
            exec_id = ExecutionID(str(execution_id))
            
            try:
                async for event in message_router.subscribe_to_execution(exec_id):
                    # Filter for node updates
                    if event.get("type") == EventType.node_update.value:
                        data = event.get("data", {})
                        # If node_id specified, filter for that node
                        if node_id and data.get("node_id") != node_id:
                            continue
                        yield data
                        
            except asyncio.CancelledError:
                logger.info(f"Node subscription cancelled for execution: {exec_id}")
                raise
            except Exception as e:
                logger.error(f"Error in node subscription: {e}")
                raise
        
        @strawberry.subscription
        async def interactive_prompts(
            self, execution_id: strawberry.ID
        ) -> AsyncGenerator[JSONScalar, None]:
            """Subscribe to interactive prompt requests."""
            message_router = registry.get(MESSAGE_ROUTER.name)
            
            if not message_router:
                logger.error("Message router not available for subscriptions")
                return
            
            exec_id = ExecutionID(str(execution_id))
            
            try:
                async for event in message_router.subscribe_to_execution(exec_id):
                    # Filter for interactive prompts
                    if event.get("type") == EventType.interactive_prompt.value:
                        yield event.get("data", {})
                        
            except asyncio.CancelledError:
                logger.info(f"Interactive prompt subscription cancelled: {exec_id}")
                raise
            except Exception as e:
                logger.error(f"Error in interactive prompt subscription: {e}")
                raise
    
    return Subscription