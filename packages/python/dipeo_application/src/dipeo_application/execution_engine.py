"""Core execution engine that can be used by both server and CLI."""

from typing import AsyncIterator, Optional, Protocol, Any
from dataclasses import dataclass
from collections import deque
import asyncio
import logging
import json

from dipeo_core import RuntimeContext, get_global_registry
from dipeo_domain import NodeOutput
from .execution_view import LocalExecutionView
from .execution_flow_controller import ExecutionFlowController

log = logging.getLogger(__name__)


class ExecutionObserver(Protocol):
    """Observers for execution events."""

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
    """Core execution engine with observer pattern."""

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

        max_concurrent_nodes = options.get("max_parallel_nodes", 10)
        self._concurrency_semaphore = asyncio.Semaphore(max_concurrent_nodes)
        for observer in self.observers:
            await observer.on_execution_start(
                execution_id, diagram.metadata.id if diagram.metadata else None
            )

        execution_view = LocalExecutionView(diagram)
        registry = get_global_registry()
        for node_id, node_view in execution_view.node_views.items():
            node_def = registry.get(node_view.node.type)
            if not node_def:
                raise ValueError(f"No handler for node type: {node_view.node.type}")
            node_view.handler = node_def.handler
            node_view._handler_def = node_def

        try:
            flow_controller = ExecutionFlowController(execution_view)
            
            # Execute initial topological levels
            for i, level in enumerate(execution_view.execution_order):
                await self._execute_level(
                    level, execution_id, options, execution_view, interactive_handler
                )
                
                if flow_controller.has_endpoint_executed():
                    log.info("Endpoint node executed, terminating execution early")
                    break
            
            # Execute iterations if no endpoint was executed
            if not flow_controller.has_endpoint_executed():
                await self._execute_iterations_with_controller(
                    flow_controller, execution_id, options, interactive_handler
                )
            
            # Store flow controller for later access
            self._last_flow_controller = flow_controller
            
            # Log final visualization if enabled
            if flow_controller.enable_visualization:
                visualization = flow_controller.get_flow_visualization()
                log.info(f"Execution flow visualization: {json.dumps(visualization, indent=2)}")

            for observer in self.observers:
                await observer.on_execution_complete(execution_id)

        except Exception as e:
            for observer in self.observers:
                await observer.on_execution_error(execution_id, str(e))
            raise

        return
        yield

    async def _execute_level(
        self, nodes, execution_id, options, execution_view, interactive_handler
    ):
        """Execute nodes in level concurrently."""
        tasks = []
        for node_view in nodes:
            can_exec = self._can_execute(node_view)
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
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    log.error(f"Node execution failed: {result}")
                    raise result

    async def _execute_node(
        self, node_view, execution_id, options, execution_view, interactive_handler
    ):
        """Execute single node with observer notifications."""
        async with self._concurrency_semaphore:
            # Record node start for visualization
            if hasattr(self, '_flow_controller'):
                self._flow_controller.record_node_execution(
                    node_view.id, "started", {"inputs": list(inputs.keys()) if inputs else []}
                )
            
            for observer in self.observers:
                await observer.on_node_start(execution_id, node_view.id)

            try:
                context = self._create_runtime_context(
                    node_view, execution_id, options, execution_view
                )
                inputs = node_view.get_active_inputs()
                services = self.service_registry.get_handler_services(
                    node_view._handler_def.requires_services
                )

                services["diagram"] = execution_view.diagram
                services["execution_context"] = {
                    "interactive_handler": interactive_handler
                }

                node_data = node_view.data.copy() if node_view.data else {}
                if node_view.node.type == "person_job" and "first_only_prompt" not in node_data:
                    node_data["first_only_prompt"] = ""
                
                # Check if we should skip execution due to max iterations
                flow_controller = ExecutionFlowController(execution_view)
                should_skip = flow_controller.should_skip_node_execution(node_view)
                
                if should_skip:
                    output = self._create_skipped_output(node_view, inputs)
                else:
                    output = await node_view.handler(
                        props=node_view._handler_def.node_schema.model_validate(
                            node_data
                        ),
                        context=context,
                        inputs=inputs,
                        services=services,
                    )

                node_view.output = output
                if not should_skip:
                    node_view.exec_count += 1

                if node_view.node.type in ["job", "person_job", "loop"]:
                    if not hasattr(node_view, "output_history"):
                        node_view.output_history = []
                    node_view.output_history.append(output)

                    max_iter = node_view.data.get("max_iteration", 1)
                    if node_view.exec_count < max_iter:
                        node_view.output = None

                for observer in self.observers:
                    await observer.on_node_complete(execution_id, node_view.id, output)

            except Exception as e:
                log.error(f"Node {node_view.id} failed: {e}")
                for observer in self.observers:
                    await observer.on_node_error(execution_id, node_view.id, str(e))
                raise

    def _has_dependency_output(self, edge):
        """Check if dependency has output available."""
        source = edge.source_view
        
        if source.node.type == "condition" and source.output is not None:
            branch = edge.source_handle
            return branch in source.output.value and source.output.value[branch] is not None
        
        if source.output is not None:
            return True
            
        if source.node.type in ["job", "person_job", "loop"]:
            return hasattr(source, "output_history") and len(source.output_history) > 0
            
        return False

    def _can_execute(self, node_view):
        """Check if node can execute."""
        if node_view.output is not None:
            return False

        if node_view.node.type == "person_job":
            if node_view.exec_count == 0:
                first_edges = [
                    e for e in node_view.incoming_edges if e.target_handle == "first"
                ]
                if first_edges:
                    return all(
                        edge.source_view.output is not None for edge in first_edges
                    )
            else:
                default_edges = [
                    e for e in node_view.incoming_edges if e.target_handle == "default"
                ]
                if default_edges:
                    return all(
                        self._has_dependency_output(edge) for edge in default_edges
                    )

        return all(
            self._has_dependency_output(edge) for edge in node_view.incoming_edges
        )

    def _create_runtime_context(self, node_view, execution_id, options, execution_view):
        """Create runtime context for node execution."""
        edges = execution_view.static_edges_list
        nodes = execution_view.static_nodes_list

        outputs = {}
        for nv in execution_view.node_views.values():
            if nv.output is not None:
                outputs[nv.id] = nv.output
            elif (
                nv.id == node_view.id
                and hasattr(nv, "output_history")
                and nv.output_history
            ):
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

    async def _execute_iterations_with_controller(
        self, flow_controller, execution_id, options, interactive_handler
    ):
        """Execute iterative nodes using the flow controller."""
        max_iterations = options.get("max_iterations", 100)
        execution_view = flow_controller.execution_view
        
        # Initialize queue with iterative nodes
        iterative_nodes = flow_controller.get_iterative_nodes()
        ready_nodes = [node for node in iterative_nodes if self._can_execute(node)]
        flow_controller.add_to_queue(ready_nodes)
        
        # Main iteration loop
        while flow_controller.should_continue_iterations(max_iterations):
            current_batch = self._prepare_execution_batch(flow_controller)
            
            if not current_batch:
                break
            
            # Execute the batch
            await self._execute_level(
                current_batch,
                execution_id,
                options,
                execution_view,
                interactive_handler,
            )
            
            # Check for early termination
            if flow_controller.has_endpoint_executed():
                log.info("Endpoint node executed during iterations, terminating early")
                break
            
            # Queue successors for execution
            self._queue_successors(current_batch, flow_controller)
            
            flow_controller.increment_iteration()
        
        # Execute any remaining non-iterative nodes
        if not flow_controller.has_endpoint_executed():
            await self._execute_final_batch(flow_controller, execution_id, options, interactive_handler)
    
    def _prepare_execution_batch(self, flow_controller):
        """Prepare the next batch of nodes for execution."""
        batch = []
        candidates = flow_controller.get_next_batch()
        
        for node_view in candidates:
            if self._can_execute(node_view):
                batch.append(node_view)
        
        return batch
    
    def _queue_successors(self, executed_nodes, flow_controller):
        """Queue successor nodes that are ready for execution."""
        for node in executed_nodes:
            successors = flow_controller.get_executable_successors(
                node, self._can_execute
            )
            flow_controller.add_to_queue(successors)
    
    async def _execute_final_batch(self, flow_controller, execution_id, options, interactive_handler):
        """Execute final batch of non-iterative nodes."""
        final_batch = flow_controller.get_final_batch_nodes(self._can_execute)
        
        if final_batch:
            await self._execute_level(
                final_batch,
                execution_id,
                options,
                flow_controller.execution_view,
                interactive_handler,
            )
    
    def _create_skipped_output(self, node_view, inputs):
        """Create output for nodes that are skipped due to max iterations."""
        from dipeo_core.execution import create_node_output
        
        # Start with previous output values if available
        if hasattr(node_view, 'output_history') and node_view.output_history:
            last_output = node_view.output_history[-1]
            output_value = last_output.value.copy() if last_output.value else {}
        else:
            output_value = {}
        
        # Merge with current inputs
        if inputs:
            output_value.update(inputs)
            if 'default' not in output_value and inputs:
                first_key = next(iter(inputs.keys()), None)
                if first_key:
                    output_value['default'] = inputs[first_key]
        
        return create_node_output(
            output_value, 
            {"skipped": True, "reason": "max_iterations_reached"}
        )
    
    def get_last_flow_visualization(self) -> Optional[dict]:
        """Get flow visualization data from the last execution."""
        if hasattr(self, '_last_flow_controller') and self._last_flow_controller:
            return self._last_flow_controller.get_flow_visualization()
        return None
