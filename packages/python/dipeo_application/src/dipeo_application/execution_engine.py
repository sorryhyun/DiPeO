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
            # Track if endpoint has been executed
            endpoint_executed = False
            
            # Execute topological levels
            # Execution order computed
            for i, level in enumerate(execution_view.execution_order):
                # Execute level
                await self._execute_level(
                    level, execution_id, options, execution_view, interactive_handler
                )
                
                # Check if any endpoint nodes have been executed
                for node_view in execution_view.node_views.values():
                    if node_view.node.type == "endpoint" and node_view.output is not None:
                        endpoint_executed = True
                        break
                
                # If endpoint executed, stop processing further levels
                if endpoint_executed:
                    log.info(f"Endpoint node executed, terminating execution early")
                    break

            # Only handle iterative nodes if no endpoint has been executed
            if not endpoint_executed:
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

                # Check if we should skip execution (node at max iterations)
                was_skipped = hasattr(node_view, '_skip_execution') and node_view._skip_execution
                
                # Handle missing firstOnlyPrompt for person_job nodes
                node_data = node_view.data.copy() if node_view.data else {}
                if node_view.node.type == "person_job" and "firstOnlyPrompt" not in node_data:
                    # Default to empty string if firstOnlyPrompt is missing
                    node_data["firstOnlyPrompt"] = ""
                
                if was_skipped:
                    # Pass through inputs as outputs
                    from dipeo_core.execution import create_node_output
                    # Use last output's value but update with new inputs if any
                    if hasattr(node_view, 'output_history') and node_view.output_history:
                        last_output = node_view.output_history[-1]
                        output_value = last_output.value.copy() if last_output.value else {}
                    else:
                        output_value = {}
                    
                    # If we have new inputs, pass them through
                    if inputs:
                        output_value.update(inputs)
                        # Ensure we have a default output
                        if 'default' not in output_value and inputs:
                            first_key = next(iter(inputs.keys()), None)
                            if first_key:
                                output_value['default'] = inputs[first_key]
                    
                    output = create_node_output(output_value, {"skipped": True, "reason": "max_iterations_reached"})
                    # Clear the skip flag
                    node_view._skip_execution = False
                else:
                    # Execute handler normally
                    output = await node_view.handler(
                        props=node_view._handler_def.node_schema.model_validate(
                            node_data
                        ),
                        context=context,
                        inputs=inputs,
                        services=services,
                    )

                # Store output
                node_view.output = output
                # Only increment exec_count if we actually executed (not skipped)
                if not was_skipped:
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

    def _has_dependency_output(self, edge):
        """Check if a dependency has output available (current or from history)."""
        source = edge.source_view
        
        # For condition nodes, check if the specific branch has output
        if source.node.type == "condition" and source.output is not None:
            # Extract the branch from the edge source handle (e.g., "node_nL9Q:True" -> "True")
            branch = edge.source_handle
            # Only satisfied if this specific branch has a value
            return branch in source.output.value and source.output.value[branch] is not None
        
        # If source has current output, dependency is satisfied
        if source.output is not None:
            return True
            
        # For iterative nodes, check if they have executed at least once
        if source.node.type in ["job", "person_job", "loop"]:
            return hasattr(source, "output_history") and len(source.output_history) > 0
            
        return False

    def _can_execute(self, node_view):
        """Check if node can execute."""
        if node_view.output is not None:
            return False

        # Special handling for person_job nodes based on execution count
        if node_view.node.type == "person_job":
            # On first execution (exec_count == 0), only check "first" inputs if they exist
            if node_view.exec_count == 0:
                first_edges = [
                    e for e in node_view.incoming_edges if e.target_handle == "first"
                ]
                if first_edges:
                    return all(
                        edge.source_view.output is not None for edge in first_edges
                    )
            else:
                # On subsequent executions, only check "default" inputs
                default_edges = [
                    e for e in node_view.incoming_edges if e.target_handle == "default"
                ]
                if default_edges:
                    return all(
                        self._has_dependency_output(edge) for edge in default_edges
                    )

        # Standard check: all dependencies must be satisfied
        return all(
            self._has_dependency_output(edge) for edge in node_view.incoming_edges
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
                    # Check if dependencies are satisfied using the same logic as _can_execute
                    if self._can_execute(node_view):
                        ready_queue.append(node_view)

        # Process queue
        while ready_queue and iteration_count < max_iterations:
            # Check if any endpoint nodes have been executed
            endpoint_executed = False
            for node_view in execution_view.node_views.values():
                if node_view.node.type == "endpoint" and node_view.output is not None:
                    endpoint_executed = True
                    log.info(f"Endpoint node executed, terminating iterations early")
                    break
            
            if endpoint_executed:
                break
            # Get current batch of ready nodes
            current_batch = []
            batch_size = len(ready_queue)

            for _ in range(batch_size):
                node_view = ready_queue.popleft()

                # Double-check the node can still execute
                if node_view.node.type in ["job", "person_job", "loop"]:
                    max_iter = node_view.data.get("maxIteration", 1)
                    if node_view.exec_count >= max_iter:
                        # Skip execution but check if we need to pass through data
                        if self._can_execute(node_view):
                            # Node has new inputs but is at max iterations
                            # Add to batch to pass through data
                            node_view._skip_execution = True
                            current_batch.append(node_view)
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
            
            # Check if any endpoint nodes have been executed after this batch
            endpoint_executed = False
            for node_view in execution_view.node_views.values():
                if node_view.node.type == "endpoint" and node_view.output is not None:
                    endpoint_executed = True
                    log.info(f"Endpoint node executed during iterations, terminating early")
                    break
            
            if endpoint_executed:
                break

            # Add newly unblocked nodes to queue
            for executed_node in current_batch:
                # Check downstream nodes that might now be ready
                for edge in executed_node.outgoing_edges:
                    target = edge.target_view

                    # Check if target can iterate or is newly unblocked
                    if target.node.type in ["job", "person_job", "loop"]:
                        max_iter = target.data.get("maxIteration", 1)
                        if target.exec_count < max_iter and target.output is None:
                            if self._can_execute(target):
                                if target not in ready_queue:
                                    ready_queue.append(target)
                    elif target.output is None and self._can_execute(target):
                        if target not in ready_queue:
                            ready_queue.append(target)
                    # Special case: condition nodes with detect_max_iterations can re-execute
                    elif target.node.type == "condition" and target.data.get("conditionType") == "detect_max_iterations":
                        # Clear output to allow re-evaluation when upstream nodes change
                        target.output = None
                        if self._can_execute(target) and target not in ready_queue:
                            ready_queue.append(target)

            iteration_count += 1
        
        # Final pass: After all iterations complete, check for any remaining
        # non-iterative nodes that might now be executable (e.g., endpoint nodes
        # that depend on nodes executed during iterations)
        
        # But first check if endpoint has already been executed
        endpoint_executed = False
        for node_view in execution_view.node_views.values():
            if node_view.node.type == "endpoint" and node_view.output is not None:
                endpoint_executed = True
                break
        
        if not endpoint_executed:
            final_batch = []
            for node_view in execution_view.node_views.values():
                if (node_view.output is None and 
                    node_view.node.type not in ["job", "person_job", "loop"] and
                    self._can_execute(node_view)):
                    final_batch.append(node_view)
            
            if final_batch:
                await self._execute_level(
                    final_batch,
                    execution_id,
                    options,
                    execution_view,
                    interactive_handler,
                )
