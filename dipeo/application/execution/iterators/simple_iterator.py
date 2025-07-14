"""
Simplified execution iterator that focuses on the essentials.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable

from dipeo.application.execution.simple_execution import SimpleExecution
from dipeo.core.static.executable_diagram import ExecutableNode
from dipeo.models import NodeID

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
    
    def __init__(self, execution: SimpleExecution):
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
            running = any(
                state.status == "RUNNING"
                for state in self.execution.state.node_states.values()
            )
            if not running:
                raise StopIteration("No progress possible")
            
            # Wait for running nodes
            return ExecutionStep(nodes=[])
        
        # Mark nodes as running
        for node in ready_nodes:
            self.execution.mark_node_running(node.id)
        
        return ExecutionStep(nodes=ready_nodes)
    
    def cancel(self):
        """Cancel the iteration."""
        self._cancelled = True


class SimpleAsyncIterator:
    """Simple async iterator for diagram execution."""
    
    def __init__(
        self,
        execution: SimpleExecution,
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
            logger.debug("Execution completed or cancelled")
            raise StopAsyncIteration()
        
        # Poll for ready nodes
        retries = 0
        while retries < 100:  # 1 second timeout
            ready_nodes = self.execution.get_ready_nodes()
            if ready_nodes:
                logger.debug(f"Found {len(ready_nodes)} ready nodes: {[n.id for n in ready_nodes]}")
                break
            
            # Check if we're stuck
            running = any(
                state.status == "RUNNING"
                for state in self.execution.state.node_states.values()
            )
            if not running and not ready_nodes:
                logger.debug("No running nodes and no ready nodes - execution stuck")
                raise StopAsyncIteration("No progress possible")
            
            await asyncio.sleep(0.01)
            retries += 1
        
        if not ready_nodes:
            logger.debug("No ready nodes after polling")
            return ExecutionStep(nodes=[])
        
        # Mark nodes as running
        for node in ready_nodes:
            logger.debug(f"Marking node {node.id} as RUNNING")
            self.execution.mark_node_running(node.id)
        
        return ExecutionStep(nodes=ready_nodes)
    
    async def execute_step(self, step: ExecutionStep) -> dict[NodeID, Any]:
        """Execute all nodes in a step."""
        if not self.node_executor:
            raise ValueError("No node executor provided")
        
        logger.debug(f"Executing step with {len(step.nodes)} nodes")
        results = {}
        
        # Execute nodes in parallel if multiple
        if len(step.nodes) > 1:
            logger.debug(f"Executing nodes in parallel: {[n.id for n in step.nodes]}")
            tasks = []
            for node in step.nodes:
                task = asyncio.create_task(self._execute_node(node))
                tasks.append((node.id, task))
            
            for node_id, task in tasks:
                try:
                    result = await task
                    results[node_id] = result
                    logger.debug(f"Node {node_id} completed successfully")
                    self.execution.mark_node_complete(node_id, result)
                except Exception as e:
                    logger.error(f"Node {node_id} failed: {str(e)}")
                    self.execution.mark_node_failed(node_id, str(e))
                    results[node_id] = {"error": str(e)}
        else:
            # Execute single node
            for node in step.nodes:
                logger.debug(f"Executing single node: {node.id}")
                try:
                    result = await self._execute_node(node)
                    results[node.id] = result
                    logger.debug(f"Node {node.id} completed successfully")
                    self.execution.mark_node_complete(node.id, result)
                except Exception as e:
                    logger.error(f"Node {node.id} failed: {str(e)}")
                    self.execution.mark_node_failed(node.id, str(e))
                    results[node.id] = {"error": str(e)}
        
        return results
    
    async def _execute_node(self, node: ExecutableNode) -> Any:
        """Execute a single node."""
        node_type = type(node).__name__
        logger.debug(f"Starting execution of node {node.id} (type: {node_type})")
        if asyncio.iscoroutinefunction(self.node_executor):
            return await self.node_executor(node)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.node_executor, node)
    
    def get_progress(self) -> dict[str, Any]:
        """Get execution progress."""
        total = len(self.execution.diagram.nodes)
        completed = sum(
            1 for state in self.execution.state.node_states.values()
            if state.status in ["COMPLETED", "FAILED", "SKIPPED"]
        )
        return {
            "total_nodes": total,
            "completed_nodes": completed,
            "progress_percentage": (completed / total * 100) if total > 0 else 0
        }
    
    async def cancel(self):
        """Cancel the execution."""
        self._cancelled = True