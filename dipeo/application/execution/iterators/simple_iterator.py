"""
Simplified execution iterator that focuses on the essentials.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable

from dipeo.application.execution.execution_runtime import ExecutionRuntime
from dipeo.core.compilation.executable_diagram import ExecutableNode
from dipeo.models import NodeID, NodeExecutionStatus

logger = logging.getLogger(__name__)


@dataclass
class ExecutionStep:
    """A single execution step."""
    nodes: list[ExecutableNode]
    
    @property
    def node_ids(self) -> list[NodeID]:
        return [node.id for node in self.nodes]


class SimpleExecutionIterator:
    """Simple synchronous iterator for diagram execution."""
    
    def __init__(self, execution: ExecutionRuntime):
        self.execution = execution
        self._cancelled = False
    
    def __iter__(self):
        return self
    
    def __next__(self) -> ExecutionStep:
        """Get next nodes to execute."""
        if self._cancelled or self.execution.is_complete():
            raise StopIteration()
        
        ready_nodes = self.execution.get_ready_nodes()
        if not ready_nodes:
            # Check if we're stuck
            running = self.execution.has_running_nodes()
            if not running:
                raise StopIteration("No progress possible")
            
            # Wait for running nodes
            return ExecutionStep(nodes=[])
        
        # Mark nodes as running
        for node in ready_nodes:
            self.execution.transition_node_to_running(node.id)
        
        return ExecutionStep(nodes=ready_nodes)
    
    def cancel(self):
        """Cancel the iteration."""
        self._cancelled = True


class SimpleAsyncIterator:
    """Simple async iterator for diagram execution."""
    
    def __init__(
        self,
        execution: ExecutionRuntime,
        node_executor: Callable[[ExecutableNode], Any] | None = None
    ):
        self.execution = execution
        self.node_executor = node_executor
        self._cancelled = False
    
    def __aiter__(self):
        return self
    
    async def __anext__(self) -> ExecutionStep:
        """Get next nodes to execute."""
        if self._cancelled or self.execution.is_complete():
            raise StopAsyncIteration()
        
        # Poll for ready nodes
        retries = 0
        while retries < 100:  # 1 second timeout
            ready_nodes = self.execution.get_ready_nodes()
            if ready_nodes:
                break
            
            # Check if we're stuck
            running = self.execution.has_running_nodes()
            if not running and not ready_nodes:
                raise StopAsyncIteration("No progress possible")
            
            await asyncio.sleep(0.01)
            retries += 1
        
        if not ready_nodes:
            return ExecutionStep(nodes=[])
        
        # Mark nodes as running
        for node in ready_nodes:
            self.execution.transition_node_to_running(node.id)
        
        return ExecutionStep(nodes=ready_nodes)
    
    async def execute_step(self, step: ExecutionStep) -> dict[NodeID, Any]:
        """Execute all nodes in a step."""
        if not self.node_executor:
            raise ValueError("No node executor provided")
        
        results = {}
        
        # Execute nodes in parallel if multiple
        if len(step.nodes) > 1:
            tasks = []
            for node in step.nodes:
                task = asyncio.create_task(self._execute_node(node))
                tasks.append((node.id, task))
            
            for node_id, task in tasks:
                try:
                    result = await task
                    results[node_id] = result
                    # Node executor already handles marking nodes complete
                except Exception as e:
                    logger.error(f"Node {node_id} failed: {str(e)}")
                    # Node executor handles failure too, just capture the error
                    results[node_id] = {"error": str(e)}
        else:
            # Execute single node
            for node in step.nodes:
                try:
                    result = await self._execute_node(node)
                    results[node.id] = result
                    # Node executor already handles marking nodes complete
                except Exception as e:
                    logger.error(f"Node {node.id} failed: {str(e)}")
                    # Node executor handles failure too, just capture the error
                    results[node.id] = {"error": str(e)}
        
        return results
    
    async def _execute_node(self, node: ExecutableNode) -> Any:
        """Execute a single node."""
        node_type = type(node).__name__
        if asyncio.iscoroutinefunction(self.node_executor):
            return await self.node_executor(node)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.node_executor, node)
    
    def get_progress(self) -> dict[str, Any]:
        """Get execution progress."""
        total = len(self.execution.diagram.nodes)
        completed = self.execution.count_nodes_by_status(
            ["COMPLETED", "FAILED", "SKIPPED", "MAXITER_REACHED"]
        )
        return {
            "total_nodes": total,
            "completed_nodes": completed,
            "progress_percentage": (completed / total * 100) if total > 0 else 0
        }
    
    async def cancel(self):
        """Cancel the execution."""
        self._cancelled = True