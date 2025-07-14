# Iterator pattern implementation for diagram execution flow control

import asyncio
from collections.abc import AsyncIterator, Callable, Iterator
from dataclasses import dataclass
from typing import Any

from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution
from dipeo.core.static.executable_diagram import ExecutableNode
from dipeo.models import NodeExecutionStatus, NodeID


@dataclass
class ExecutionStep:
    # Represents a single step in the execution flow
    nodes: list[ExecutableNode]  # Nodes to execute in this step
    is_parallel: bool = False  # Whether nodes can be executed in parallel
    
    @property
    def node_ids(self) -> list[NodeID]:
        return [node.id for node in self.nodes]


class ExecutionIterator(Iterator[ExecutionStep]):
    """Synchronous iterator for step-by-step diagram execution.
    
    This iterator provides a way to execute diagrams one step at a time,
    where each step may contain multiple nodes that can be executed in parallel.
    """
    
    def __init__(
        self,
        stateful_execution: TypedStatefulExecution,
        max_parallel_nodes: int = 1,
        node_executor: Callable[[ExecutableNode], dict[str, Any]] | None = None
    ):
        """Initialize the execution iterator.
        
        Args:
            stateful_execution: The stateful execution to iterate over
            max_parallel_nodes: Maximum nodes to execute in parallel
            node_executor: Optional function to execute nodes (for convenience)
        """
        self._execution = stateful_execution
        self._max_parallel = max_parallel_nodes
        self._node_executor = node_executor
        self._cancelled = False
        self._current_step = 0
    
    def __iter__(self) -> Iterator[ExecutionStep]:
        """Return the iterator."""
        return self
    
    def __next__(self) -> ExecutionStep:
        """Get the next execution step.
        
        Returns:
            ExecutionStep containing nodes ready for execution
            
        Raises:
            StopIteration: When execution is complete or cancelled
        """
        if self._cancelled:
            raise StopIteration("Execution cancelled")
        
        # Check if execution is complete
        if self._execution.is_complete():
            raise StopIteration("Execution complete")
        
        # Get ready nodes
        ready_nodes = self._execution.get_ready_nodes()
        
        if not ready_nodes:
            # No nodes ready - check for deadlock
            if not self._has_running_nodes():
                raise StopIteration("No nodes ready and none running - possible deadlock")
            
            # Return empty step to indicate waiting
            return ExecutionStep(nodes=[], is_parallel=False)
        
        # Determine if nodes can run in parallel using domain service
        can_parallel = len(ready_nodes) > 1 and self._max_parallel > 1
        
        # Use domain service for smarter parallelization if available
        if hasattr(self, '_execution_domain_service') and self._execution_domain_service:
            # Convert ready nodes to format expected by domain service
            node_list = [{"id": node.id, "node_type": node.node_type} for node in ready_nodes]
            execution_plan = self._execution_domain_service.determine_parallelization(node_list)
            
            # Get current step's parallel group
            if execution_plan.parallel_groups:
                ready_node_ids = {node.id for node in ready_nodes}
                # Find which parallel group these nodes belong to
                for group_nodes in execution_plan.parallel_groups.values():
                    if group_nodes.intersection(ready_node_ids):
                        # These nodes are in a parallel group
                        can_parallel = True
                        break
        
        # Limit nodes based on max parallel setting
        if can_parallel and len(ready_nodes) > self._max_parallel:
            ready_nodes = ready_nodes[:self._max_parallel]
        
        # Mark nodes as running
        for node in ready_nodes:
            self._execution.mark_node_running(node.id)
        
        self._current_step += 1
        
        return ExecutionStep(
            nodes=ready_nodes,
            is_parallel=can_parallel
        )
    
    def advance_node(self, node_id: NodeID, result: dict[str, Any] | None = None) -> None:
        """Mark a node as completed with its result.
        
        Args:
            node_id: The ID of the completed node
            result: Optional execution result
        """
        self._execution.mark_node_complete(node_id)
        if result:
            self._execution.set_node_output(node_id, result.get('value', result))
    
    def fail_node(self, node_id: NodeID, error: Exception) -> None:
        """Mark a node as failed.
        
        Args:
            node_id: The ID of the failed node
            error: The exception that caused the failure
        """
        self._execution.mark_node_failed(node_id, str(error))
    
    def cancel(self) -> None:
        """Cancel the execution."""
        self._cancelled = True
    
    def get_progress(self) -> dict[str, Any]:
        """Get execution progress information.
        
        Returns:
            Dictionary with progress metrics
        """
        progress = self._execution.get_progress()
        progress.update({
            "current_step": self._current_step,
            "is_cancelled": self._cancelled
        })
        return progress
    
    def _has_running_nodes(self) -> bool:
        """Check if any nodes are currently running."""
        for node in self._execution.diagram.nodes:
            state = self._execution.get_node_state(node.id)
            if state.status == NodeExecutionStatus.RUNNING:
                return True
        return False


class AsyncExecutionIterator(AsyncIterator[ExecutionStep]):
    """Asynchronous iterator for step-by-step diagram execution with parallel support.
    
    This iterator provides async iteration over execution steps, with built-in
    support for parallel node execution within each step.
    """
    
    def __init__(
        self,
        stateful_execution: TypedStatefulExecution,
        max_parallel_nodes: int = 10,
        node_executor: Callable[[ExecutableNode], Any] | None = None,  # Can be sync or async
        node_ready_poll_interval: float = 0.01,  # Reduced from 0.1 for more responsive execution
        max_poll_retries: int = 100  # Increased to maintain same total wait time (1s)
    ):
        """Initialize the async execution iterator.
        
        Args:
            stateful_execution: The stateful execution to iterate over
            max_parallel_nodes: Maximum nodes to execute in parallel
            node_executor: Optional async function to execute nodes
            node_ready_poll_interval: How long to wait between polling for ready nodes (seconds)
            max_poll_retries: Maximum number of polling attempts before giving up
        """
        self._execution = stateful_execution
        self._max_parallel = max_parallel_nodes
        self._node_executor = node_executor
        self._cancelled = False
        self._current_step = 0
        self._running_tasks: set[asyncio.Task] = set()
        self._node_ready_poll_interval = node_ready_poll_interval
        self._max_poll_retries = max_poll_retries
    
    def __aiter__(self) -> AsyncIterator[ExecutionStep]:
        """Return the async iterator."""
        return self
    
    async def __anext__(self) -> ExecutionStep:
        """Get the next execution step asynchronously.
        
        Returns:
            ExecutionStep containing nodes ready for execution
            
        Raises:
            StopAsyncIteration: When execution is complete or cancelled
        """
        if self._cancelled:
            await self._cleanup_tasks()
            raise StopAsyncIteration("Execution cancelled")
        
        # Check if execution is complete
        if self._execution.is_complete():
            await self._cleanup_tasks()
            raise StopAsyncIteration("Execution complete")
        
        # Poll for ready nodes with configurable interval
        retry_count = 0
        while retry_count < self._max_poll_retries:
            ready_nodes = self._execution.get_ready_nodes()
            
            if ready_nodes:
                break
            
            if not self._has_running_nodes() and not self._running_tasks:
                # No nodes ready and none running - possible deadlock
                await self._cleanup_tasks()
                raise StopAsyncIteration("No nodes ready and none running - possible deadlock")
            
            # Use shorter poll interval for more responsive execution
            if self._node_ready_poll_interval > 0:
                await asyncio.sleep(self._node_ready_poll_interval)
            else:
                # If interval is 0, yield control without sleeping
                await asyncio.sleep(0)
            retry_count += 1
        
        if not ready_nodes:
            # Still no ready nodes after retries
            return ExecutionStep(nodes=[], is_parallel=False)
        
        # Determine if nodes can run in parallel
        can_parallel = len(ready_nodes) > 1 and self._max_parallel > 1
        
        # Limit nodes based on max parallel setting
        if can_parallel and len(ready_nodes) > self._max_parallel:
            ready_nodes = ready_nodes[:self._max_parallel]
        
        # Mark nodes as running
        for node in ready_nodes:
            self._execution.mark_node_running(node.id)
        
        self._current_step += 1
        
        return ExecutionStep(
            nodes=ready_nodes,
            is_parallel=can_parallel
        )
    
    async def execute_step(self, step: ExecutionStep) -> dict[NodeID, dict[str, Any]]:
        """Execute all nodes in a step, handling parallelism.
        
        Args:
            step: The execution step containing nodes to execute
            
        Returns:
            Dictionary mapping node IDs to their results
        """
        if not self._node_executor:
            raise ValueError("No node executor provided")
        
        results = {}
        
        if step.is_parallel and len(step.nodes) > 1:
            # Execute nodes in parallel
            tasks = []
            for node in step.nodes:
                task = asyncio.create_task(self._execute_node(node))
                self._running_tasks.add(task)
                tasks.append((node.id, task))
            
            # Wait for all tasks to complete
            for node_id, task in tasks:
                try:
                    result = await task
                    results[node_id] = result
                    self.advance_node(node_id, result)
                except Exception as e:
                    self.fail_node(node_id, e)
                    results[node_id] = {"error": str(e)}
                finally:
                    self._running_tasks.discard(task)
        else:
            # Execute nodes sequentially
            for node in step.nodes:
                try:
                    result = await self._execute_node(node)
                    results[node.id] = result
                    self.advance_node(node.id, result)
                except Exception as e:
                    self.fail_node(node.id, e)
                    results[node.id] = {"error": str(e)}
        
        return results
    
    async def _execute_node(self, node: ExecutableNode) -> dict[str, Any]:
        """Execute a single node.
        
        Args:
            node: The node to execute
            
        Returns:
            The execution result
        """
        if asyncio.iscoroutinefunction(self._node_executor):
            return await self._node_executor(node)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._node_executor, node)
    
    def advance_node(self, node_id: NodeID, result: dict[str, Any] | None = None) -> None:
        """Mark a node as completed with its result.
        
        Args:
            node_id: The ID of the completed node
            result: Optional execution result
        """
        self._execution.mark_node_complete(node_id)
        if result:
            self._execution.set_node_output(node_id, result.get('value', result))
    
    def fail_node(self, node_id: NodeID, error: Exception) -> None:
        """Mark a node as failed.
        
        Args:
            node_id: The ID of the failed node
            error: The exception that caused the failure
        """
        self._execution.mark_node_failed(node_id, str(error))
    
    async def cancel(self) -> None:
        """Cancel the execution and clean up tasks."""
        self._cancelled = True
        await self._cleanup_tasks()
    
    async def _cleanup_tasks(self) -> None:
        """Cancel and await all running tasks."""
        if self._running_tasks:
            for task in self._running_tasks:
                task.cancel()
            
            # Wait for all tasks to complete cancellation
            await asyncio.gather(*self._running_tasks, return_exceptions=True)
            self._running_tasks.clear()
    
    def get_progress(self) -> dict[str, Any]:
        """Get execution progress information.
        
        Returns:
            Dictionary with progress metrics
        """
        progress = self._execution.get_progress()
        progress.update({
            "current_step": self._current_step,
            "is_cancelled": self._cancelled,
            "running_tasks": len(self._running_tasks)
        })
        return progress
    
    def _has_running_nodes(self) -> bool:
        """Check if any nodes are currently running."""
        for node in self._execution.diagram.nodes:
            state = self._execution.get_node_state(node.id)
            if state.status == NodeExecutionStatus.RUNNING:
                return True
        return False