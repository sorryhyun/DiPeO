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
            endpoint_executed = False
            for i, level in enumerate(execution_view.execution_order):
                await self._execute_level(
                    level, execution_id, options, execution_view, interactive_handler
                )
                for node_view in execution_view.node_views.values():
                    if node_view.node.type == "endpoint" and node_view.output is not None:
                        endpoint_executed = True
                        break
                
                if endpoint_executed:
                    log.info(f"Endpoint node executed, terminating execution early")
                    break
            if not endpoint_executed:
                await self._execute_iterations(
                    execution_view, execution_id, options, interactive_handler
                )

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

                was_skipped = hasattr(node_view, '_skip_execution') and node_view._skip_execution
                node_data = node_view.data.copy() if node_view.data else {}
                if node_view.node.type == "person_job" and "first_only_prompt" not in node_data:
                    node_data["first_only_prompt"] = ""
                
                if was_skipped:
                    from dipeo_core.execution import create_node_output
                    if hasattr(node_view, 'output_history') and node_view.output_history:
                        last_output = node_view.output_history[-1]
                        output_value = last_output.value.copy() if last_output.value else {}
                    else:
                        output_value = {}
                    
                    if inputs:
                        output_value.update(inputs)
                        if 'default' not in output_value and inputs:
                            first_key = next(iter(inputs.keys()), None)
                            if first_key:
                                output_value['default'] = inputs[first_key]
                    
                    output = create_node_output(output_value, {"skipped": True, "reason": "max_iterations_reached"})
                    node_view._skip_execution = False
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
                if not was_skipped:
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

    async def _execute_iterations(
        self, execution_view, execution_id, options, interactive_handler
    ):
        """Execute iterative nodes using breadth-first queue."""
        max_iterations = options.get("max_iterations", 100)
        iteration_count = 0

        ready_queue = deque()

        for node_view in execution_view.node_views.values():
            if node_view.node.type in ["job", "person_job", "loop"]:
                max_iter = node_view.data.get("max_iteration", 1)
                if node_view.exec_count < max_iter and node_view.output is None:
                    if self._can_execute(node_view):
                        ready_queue.append(node_view)

        while ready_queue and iteration_count < max_iterations:
            endpoint_executed = False
            for node_view in execution_view.node_views.values():
                if node_view.node.type == "endpoint" and node_view.output is not None:
                    endpoint_executed = True
                    log.info(f"Endpoint node executed, terminating iterations early")
                    break
            
            if endpoint_executed:
                break
            current_batch = []
            batch_size = len(ready_queue)

            for _ in range(batch_size):
                node_view = ready_queue.popleft()

                if node_view.node.type in ["job", "person_job", "loop"]:
                    max_iter = node_view.data.get("max_iteration", 1)
                    if node_view.exec_count >= max_iter:
                        if self._can_execute(node_view):
                            node_view._skip_execution = True
                            current_batch.append(node_view)
                        continue

                if self._can_execute(node_view):
                    current_batch.append(node_view)

            if not current_batch:
                break

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

            for executed_node in current_batch:
                for edge in executed_node.outgoing_edges:
                    target = edge.target_view

                    if target.node.type in ["job", "person_job", "loop"]:
                        max_iter = target.data.get("max_iteration", 1)
                        if target.exec_count < max_iter and target.output is None:
                            if self._can_execute(target):
                                if target not in ready_queue:
                                    ready_queue.append(target)
                    elif target.output is None and self._can_execute(target):
                        if target not in ready_queue:
                            ready_queue.append(target)
                    elif target.node.type == "condition" and target.data.get("condition_type") == "detect_max_iterations":
                        target.output = None
                        if self._can_execute(target) and target not in ready_queue:
                            ready_queue.append(target)

            iteration_count += 1
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
