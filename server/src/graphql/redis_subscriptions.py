"""Redis-based subscription helpers for GraphQL."""
import asyncio
import json
import logging
from typing import AsyncGenerator, Optional, Dict, Any
import redis.asyncio as redis
from redis.asyncio.client import PubSub

from .types.domain import ExecutionEvent
from .types.enums import EventType

logger = logging.getLogger(__name__)


class RedisSubscriptionManager:
    """Manages Redis pub/sub connections for GraphQL subscriptions."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self._pubsub_connections: Dict[str, PubSub] = {}
        self._cleanup_tasks: Dict[str, asyncio.Task] = {}
        
    async def subscribe_to_execution(
        self, 
        execution_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to execution events via Redis pub/sub."""
        if not self.redis_client:
            logger.warning("Redis client not available, falling back to polling")
            return
            
        pubsub = None
        channel = f"execution:{execution_id}"
        
        try:
            # Create pub/sub connection
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel)
            
            # Store the connection
            self._pubsub_connections[execution_id] = pubsub
            
            logger.info(f"Subscribed to Redis channel: {channel}")
            
            # Listen for messages
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        # Parse the event data
                        event_data = json.loads(message["data"])
                        yield event_data
                        
                        # Check if execution is complete
                        event_type = event_data.get("event_type")
                        if event_type in ["execution_completed", "execution_failed", "execution_aborted"]:
                            logger.info(f"Execution {execution_id} completed, closing subscription")
                            break
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Redis message: {e}")
                        continue
                        
        except asyncio.CancelledError:
            logger.info(f"Subscription cancelled for execution {execution_id}")
            raise
        except Exception as e:
            logger.error(f"Error in Redis subscription for {execution_id}: {e}")
            raise
        finally:
            # Clean up
            if pubsub:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
            self._pubsub_connections.pop(execution_id, None)
            
    async def subscribe_to_all_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to all execution events via Redis pub/sub."""
        if not self.redis_client:
            logger.warning("Redis client not available")
            return
            
        pubsub = None
        channel = "events:all"
        
        try:
            # Create pub/sub connection
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel)
            
            logger.info(f"Subscribed to Redis channel: {channel}")
            
            # Listen for messages
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        # Parse the event data
                        event_data = json.loads(message["data"])
                        yield event_data
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Redis message: {e}")
                        continue
                        
        except asyncio.CancelledError:
            logger.info("All events subscription cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in Redis all events subscription: {e}")
            raise
        finally:
            # Clean up
            if pubsub:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
                
    async def cleanup(self):
        """Clean up all active subscriptions."""
        for execution_id, pubsub in list(self._pubsub_connections.items()):
            try:
                await pubsub.close()
            except Exception as e:
                logger.error(f"Error closing pubsub for {execution_id}: {e}")
        self._pubsub_connections.clear()