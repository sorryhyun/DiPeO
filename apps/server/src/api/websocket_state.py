"""WebSocket execution state management."""
import asyncio
from typing import Dict, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .messages import MessageFactory, InteractivePromptTimeoutMessage

logger = logging.getLogger(__name__)


@dataclass
class ExecutionState:
    """State for a single execution."""
    client_id: str
    status: str = "running"
    paused_nodes: Set[str] = field(default_factory=set)
    skipped_nodes: Set[str] = field(default_factory=set)
    aborted: bool = False
    started_at: datetime = field(default_factory=datetime.now)


class ExecutionStateManager:
    """Manages execution states for all active executions."""
    
    def __init__(self):
        self.execution_states: Dict[str, ExecutionState] = {}
        self.interactive_prompts: Dict[str, asyncio.Future] = {}
    
    def create_execution(self, execution_id: str, client_id: str) -> ExecutionState:
        """Create a new execution state."""
        state = ExecutionState(client_id=client_id)
        self.execution_states[execution_id] = state
        return state
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionState]:
        """Get execution state by ID."""
        return self.execution_states.get(execution_id)
    
    def execution_exists(self, execution_id: str) -> bool:
        """Check if execution exists."""
        return execution_id in self.execution_states
    
    def remove_execution(self, execution_id: str) -> None:
        """Remove execution state."""
        if execution_id in self.execution_states:
            del self.execution_states[execution_id]
    
    def abort_execution(self, execution_id: str) -> bool:
        """Mark execution as aborted."""
        if state := self.get_execution(execution_id):
            state.aborted = True
            return True
        return False
    
    def is_execution_aborted(self, execution_id: str) -> bool:
        """Check if execution is aborted."""
        if state := self.get_execution(execution_id):
            return state.aborted
        return False
    
    def pause_node(self, execution_id: str, node_id: str) -> bool:
        """Pause a node in an execution."""
        if state := self.get_execution(execution_id):
            state.paused_nodes.add(node_id)
            return True
        return False
    
    def resume_node(self, execution_id: str, node_id: str) -> bool:
        """Resume a paused node."""
        if state := self.get_execution(execution_id):
            state.paused_nodes.discard(node_id)
            return True
        return False
    
    def is_node_paused(self, execution_id: str, node_id: str) -> bool:
        """Check if a node is paused."""
        if state := self.get_execution(execution_id):
            return node_id in state.paused_nodes
        return False
    
    def skip_node(self, execution_id: str, node_id: str) -> bool:
        """Mark a node for skipping."""
        if state := self.get_execution(execution_id):
            state.skipped_nodes.add(node_id)
            return True
        return False
    
    def is_node_skipped(self, execution_id: str, node_id: str) -> bool:
        """Check if a node should be skipped."""
        if state := self.get_execution(execution_id):
            return node_id in state.skipped_nodes
        return False
    
    def create_interactive_prompt(self, execution_id: str, node_id: str) -> asyncio.Future:
        """Create a future for an interactive prompt."""
        prompt_key = f"{execution_id}:{node_id}"
        future = asyncio.Future()
        self.interactive_prompts[prompt_key] = future
        return future
    
    def resolve_interactive_prompt(self, execution_id: str, node_id: str, response: str) -> bool:
        """Resolve an interactive prompt with a response."""
        prompt_key = f"{execution_id}:{node_id}"
        if prompt_key in self.interactive_prompts:
            future = self.interactive_prompts[prompt_key]
            if not future.done():
                future.set_result(response)
                del self.interactive_prompts[prompt_key]
                return True
        return False
    
    def cancel_interactive_prompt(self, execution_id: str, node_id: str) -> None:
        """Cancel an interactive prompt."""
        prompt_key = f"{execution_id}:{node_id}"
        if prompt_key in self.interactive_prompts:
            future = self.interactive_prompts[prompt_key]
            if not future.done():
                future.cancel()
            del self.interactive_prompts[prompt_key]
    
    def get_execution_duration(self, execution_id: str) -> Optional[float]:
        """Get execution duration in seconds."""
        if state := self.get_execution(execution_id):
            return (datetime.now() - state.started_at).total_seconds()
        return None


class ClientSubscriptionManager:
    """Manages client subscriptions to executions."""
    
    def __init__(self):
        self.client_subscriptions: Dict[str, Set[str]] = {}
    
    def subscribe_client(self, client_id: str, execution_id: str) -> None:
        """Subscribe a client to an execution."""
        if client_id not in self.client_subscriptions:
            self.client_subscriptions[client_id] = set()
        self.client_subscriptions[client_id].add(execution_id)
    
    def unsubscribe_client(self, client_id: str, execution_id: str) -> None:
        """Unsubscribe a client from an execution."""
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].discard(execution_id)
    
    def get_client_subscriptions(self, client_id: str) -> Set[str]:
        """Get all subscriptions for a client."""
        return self.client_subscriptions.get(client_id, set())
    
    def remove_client(self, client_id: str) -> None:
        """Remove all subscriptions for a client."""
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
    
    def is_client_subscribed(self, client_id: str, execution_id: str) -> bool:
        """Check if a client is subscribed to an execution."""
        return execution_id in self.get_client_subscriptions(client_id)


class InteractiveHandlerFactory:
    """Factory for creating interactive prompt handlers."""
    
    def __init__(self, state_manager: ExecutionStateManager, broadcast_func: Callable):
        self.state_manager = state_manager
        self.broadcast_func = broadcast_func
    
    def create_handler(self, execution_id: str) -> Callable:
        """Create an interactive handler for a specific execution."""
        async def interactive_handler(node_id: str, prompt: str, context: Dict[str, Any]) -> str:
            # Create a future for the response
            future = self.state_manager.create_interactive_prompt(execution_id, node_id)
            
            # Send interactive prompt to all clients
            await self.broadcast_func({
                'type': 'interactive_prompt',
                'nodeId': node_id,
                'executionId': execution_id,
                'prompt': prompt,
                'context': context,
                'timestamp': datetime.now().isoformat()
            }, execution_id)
            
            try:
                # Wait for response with timeout
                response = await asyncio.wait_for(future, timeout=300.0)  # 5 minute timeout
                return response
            except asyncio.TimeoutError:
                # Clean up on timeout
                self.state_manager.cancel_interactive_prompt(execution_id, node_id)
                
                await self.broadcast_func(
                    InteractivePromptTimeoutMessage(
                        node_id=node_id,
                        execution_id=execution_id
                    ).to_dict(),
                    execution_id
                )
                
                return ""
            except Exception as e:
                logger.error(f"Error in interactive handler: {e}")
                self.state_manager.cancel_interactive_prompt(execution_id, node_id)
                return ""
        
        return interactive_handler