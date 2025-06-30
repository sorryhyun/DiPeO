"""Core execution engine that can be used by both server and CLI."""

from typing import AsyncIterator, Optional, Protocol, Any
from dataclasses import dataclass
from collections import deque
import asyncio
import logging

from dipeo_core import RuntimeContext, get_global_registry
from dipeo_domain import NodeOutput
from .execution_view import LocalExecutionView

log = logging.getLogger(__name__)


class ExecutionObserver(Protocol):
    """Protocol for execution observers (e.g., state persistence, streaming)."""

    async def on_execution_start(
        self, execution_id: str, diagram_id: Optional[str]
    ) -> None: ...
    async def on_node_start(self, execution_id: str, node_id: str) -> None: ...
    async def on_node_complete(
        self, execution_id: str, node_id: str, output: NodeOutput
    ) -> None: ...
    async def on_node_error(
        self, execution_id: str, node_id: str, error: str
    ) -> None: ...
    async def on_execution_complete(self, execution_id: str) -> None: ...
    async def on_execution_error(self, execution_id: str, error: str) -> None: ...


@dataclass
class ExecutionEngine:
    """Core execution engine with observer pattern for extensibility."""

    service_registry: Any
    observers: list[ExecutionObserver]

    async def execute(
        self,
        diagram: Any,
        execution_id: str,
        options: dict[str, Any],
        interactive_handler: Optional[Any] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute diagram with observer notifications."""

        # Create concurrency semaphore
        max_concurrent_nodes = options.get("max_parallel_nodes", 10)
        self._concurrency_semaphore = asyncio.Semaphore(max_concurrent_nodes)

        # Notify observers of start
        for observer in self.observers:
            await observer.on_execution_start(
                execution_id, diagram.metadata.id if diagram.metadata else None
            )

        # Build execution view
        execution_view = LocalExecutionView(diagram)

        # Get handler registry
        registry = get_global_registry()

        # Assign handlers to nodes
        for node_id, node_view in execution_view.node_views.items():
            node_def = registry.get(node_view.node.type)
            if not node_def:
                raise ValueError(f"No handler for node type: {node_view.node.type}")
            node_view.handler = node_def.handler
            node_view._handler_def = node_def

        try:
            # Execute topological levels
            # Execution order computed
            for i, level in enumerate(execution_view.execution_order):
                # Execute level
                await self._execute_level(
                    level, execution_id, options, execution_view, interactive_handler
                )

            # Handle iterative nodes
            await self._execute_iterations(
                execution_view, execution_id, options, interactive_handler
            )

            # Notify completion
            for observer in self.observers:
                await observer.on_execution_complete(execution_id)

        except Exception as e:
            # Notify error
            for observer in self.observers:
                await observer.on_execution_error(execution_id, str(e))
            raise

        # Empty generator - observers handle all updates
        return
        yield  # Make this a generator

    async def _execute_level(
        self, nodes, execution_id, options, execution_view, interactive_handler
    ):
        """Execute all nodes in a level concurrently."""
        tasks = []
        for node_view in nodes:
            can_exec = self._can_execute(node_view)
            # Check node execution
            if can_exec:
                tasks.append(
                    self._execute_node(
                        node_view,
                        execution_id,
                        options,
                        execution_view,
                        interactive_handler,
                    )
                )

        if tasks:
            # Execute tasks and check for exceptions
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for any exceptions and raise the first one
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Log all exceptions before raising
                    log.error(f"Node execution failed: {result}")
                    raise result

    async def _execute_node(
        self, node_view, execution_id, options, execution_view, interactive_handler
    ):
        """Execute a single node with observer notifications."""
        # Acquire semaphore to limit concurrency
        async with self._concurrency_semaphore:
            # Notify start
            for observer in self.observers:
                await observer.on_node_start(execution_id, node_view.id)

            try:
                # Create runtime context
                context = self._create_runtime_context(
                    node_view, execution_id, options, execution_view
                )

                # Get inputs and services
                inputs = node_view.get_active_inputs()
                services = self.service_registry.get_handler_services(
                    node_view._handler_def.requires_services
                )

                # Add special services
                services["diagram"] = execution_view.diagram
                services["execution_context"] = {
                    "interactive_handler": interactive_handler
                }

                # Execute handler
                output = await node_view.handler(
                    props=node_view._handler_def.node_schema.model_validate(
                        node_view.data
                    ),
                    context=context,
                    inputs=inputs,
                    services=services,
                )

                # Store output
                node_view.output = output
                node_view.exec_count += 1

                # For iterative nodes, store output in history and clear current output
                # to allow re-execution
                if node_view.node.type in ["job", "person_job", "loop"]:
                    # Store in output history (if not already present)
                    if not hasattr(node_view, "output_history"):
                        node_view.output_history = []
                    node_view.output_history.append(output)

                    # Check if we can iterate again
                    max_iter = node_view.data.get("maxIteration", 1)
                    if node_view.exec_count < max_iter:
                        # Clear output to allow re-execution
                        node_view.output = None

                # Notify completion
                for observer in self.observers:
                    await observer.on_node_complete(execution_id, node_view.id, output)

            except Exception as e:
                log.error(f"Node {node_view.id} failed: {e}")
                for observer in self.observers:
                    await observer.on_node_error(execution_id, node_view.id, str(e))
                raise

    def _can_execute(self, node_view):
        """Check if node can execute."""
        if node_view.output is not None:
            return False

        # Special handling for person_job nodes on first execution
        if node_view.node.type == "person_job" and node_view.exec_count == 0:
            # Check if at least "first" inputs are ready
            first_edges = [
                e for e in node_view.incoming_edges if e.target_handle == "first"
            ]
            if first_edges:
                return all(edge.source_view.output is not None for edge in first_edges)

        # Standard check: all dependencies must be satisfied
        return all(
            edge.source_view.output is not None for edge in node_view.incoming_edges
        )

    def _create_runtime_context(self, node_view, execution_id, options, execution_view):
        """Create runtime context for node execution."""
        # Use cached static lists instead of rebuilding them
        edges = execution_view.static_edges_list
        nodes = execution_view.static_nodes_list

        # Collect all node outputs including current node's output history
        outputs = {}
        for nv in execution_view.node_views.values():
            if nv.output is not None:
                outputs[nv.id] = nv.output
            # Include output history for the current node if it exists
            elif (
                nv.id == node_view.id
                and hasattr(nv, "output_history")
                and nv.output_history
            ):
                # Provide the last output from history for handlers that need it
                outputs[nv.id] = nv.output_history[-1]

        return RuntimeContext(
            execution_id=execution_id,
            current_node_id=node_view.id,
            edges=edges,
            nodes=nodes,
            variables=options.get("variables", {}),
            outputs=outputs,
            exec_cnt={
                nv.id: nv.exec_count for nv in execution_view.node_views.values()
            },
            diagram_id=execution_view.diagram.metadata.id
            if execution_view.diagram.metadata
            else None,
        )

    async def _execute_iterations(
        self, execution_view, execution_id, options, interactive_handler
    ):
        """Execute iterative nodes using breadth-first queue approach."""
        max_iterations = options.get("max_iterations", 100)
        iteration_count = 0

        # Initialize queue with nodes that might be ready after initial execution
        ready_queue = deque()

        # Find nodes that might iterate
        for node_view in execution_view.node_views.values():
            if node_view.node.type in ["job", "person_job", "loop"]:
                max_iter = node_view.data.get("maxIteration", 1)
                if node_view.exec_count < max_iter and node_view.output is None:
                    # Check if dependencies are satisfied
                    if all(
                        edge.source_view.output is not None
                        for edge in node_view.incoming_edges
                    ):
                        ready_queue.append(node_view)

        # Process queue
        while ready_queue and iteration_count < max_iterations:
            # Get current batch of ready nodes
            current_batch = []
            batch_size = len(ready_queue)

            for _ in range(batch_size):
                node_view = ready_queue.popleft()

                # Double-check the node can still execute
                if node_view.node.type in ["job", "person_job", "loop"]:
                    max_iter = node_view.data.get("maxIteration", 1)
                    if node_view.exec_count >= max_iter:
                        continue

                if self._can_execute(node_view):
                    current_batch.append(node_view)

            if not current_batch:
                break

            # Execute current batch
            await self._execute_level(
                current_batch,
                execution_id,
                options,
                execution_view,
                interactive_handler,
            )

            # Add newly unblocked nodes to queue
            for executed_node in current_batch:
                # Check downstream nodes that might now be ready
                for edge in executed_node.outgoing_edges:
                    target = edge.target_view

                    # Check if target can iterate or is newly unblocked
                    if target.node.type in ["job", "person_job", "loop"]:
                        max_iter = target.data.get("maxIteration", 1)
                        if target.exec_count < max_iter and target.output is None:
                            if all(
                                e.source_view.output is not None
                                for e in target.incoming_edges
                            ):
                                if target not in ready_queue:
                                    ready_queue.append(target)
                    elif target.output is None and all(
                        e.source_view.output is not None for e in target.incoming_edges
                    ):
                        if target not in ready_queue:
                            ready_queue.append(target)

            iteration_count += 1
