from typing import Dict, List, Set, Optional, Any, AsyncIterator
import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field

from ..exceptions import DiagramExecutionError
from .resolver import DependencyResolver
from .planner import ExecutionPlanner
from .controllers import LoopController, SkipManager
from .executors.base_executor import BaseExecutor
from .executors import create_executors
from ..utils.node_type_utils import normalize_node_type_to_backend

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Execution context maintaining state throughout diagram execution"""
    nodes_by_id: Dict[str, Dict] = field(default_factory=dict)
    incoming_arrows: Dict[str, List[Dict]] = field(default_factory=lambda: defaultdict(list))
    outgoing_arrows: Dict[str, List[Dict]] = field(default_factory=lambda: defaultdict(list))
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    node_execution_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    condition_values: Dict[str, bool] = field(default_factory=dict)
    first_only_consumed: Dict[str, bool] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    total_cost: float = 0.0
    skipped_nodes: Set[str] = field(default_factory=set)
    skip_reasons: Dict[str, str] = field(default_factory=dict)
    api_keys: Dict[str, str] = field(default_factory=dict)
    persons: Dict[str, Dict] = field(default_factory=dict)


class UnifiedExecutionEngine:
    """
    Unified execution engine that consolidates all diagram execution logic.
    Manages the complete execution lifecycle including dependency resolution,
    loop control, skip management, and node execution.
    """
    
    def __init__(self, llm_service=None, file_service=None):
        self.dependency_resolver = DependencyResolver()
        self.execution_planner = ExecutionPlanner()
        self.loop_controller = LoopController()
        self.skip_manager = SkipManager()
        self.llm_service = llm_service
        self.file_service = file_service
        self.executors = create_executors(
            llm_service=self.llm_service,
            file_service=self.file_service
        )
        self._execution_lock = asyncio.Lock()
    
    async def execute_diagram(
        self, 
        diagram: Dict[str, Any], 
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute a diagram with streaming updates.
        
        Args:
            diagram: The diagram definition containing nodes and arrows
            options: Execution options (debug mode, etc.)
            
        Yields:
            Execution updates with node status, outputs, and metadata
        """
        options = options or {}
        async with self._execution_lock:
            try:
                # Initialize execution context
                context = self._build_execution_context(diagram)
                
                # Create execution plan
                plan = self.execution_planner.create_execution_plan(
                    context.nodes_by_id,
                    context.incoming_arrows,
                    context.outgoing_arrows
                )
                
                # Yield initial plan
                yield {
                    "type": "execution_started",
                    "plan": {
                        "execution_order": plan.execution_order,
                        "parallel_groups": plan.parallel_groups,
                        "estimated_cost": plan.estimated_cost
                    }
                }
                
                # Execute nodes according to plan
                pending_nodes = set(plan.execution_order)
                
                while pending_nodes:
                    # Find nodes ready to execute
                    ready_nodes = []
                    for node_id in pending_nodes:
                        can_exec = self._can_execute_node(node_id, context, pending_nodes)
                        node_type = normalize_node_type_to_backend(context.nodes_by_id[node_id]["type"])
                        logger.debug(f"Checking node {node_id} (type: {node_type}): can_execute={can_exec}")
                        if can_exec:
                            ready_nodes.append(node_id)
                    
                    if not ready_nodes:
                        # Log detailed state before failing
                        logger.error(f"No nodes ready to execute. Pending nodes: {pending_nodes}")
                        logger.error(f"Executed nodes: {context.execution_order}")
                        logger.error(f"Skipped nodes: {context.skipped_nodes}")
                        logger.error(f"Node outputs: {list(context.node_outputs.keys())}")
                        logger.error(f"Condition values: {context.condition_values}")
                        
                        # Check for cycles or unmet dependencies
                        if options.get("allow_partial", False):
                            # In debug mode, skip remaining nodes
                            for node_id in pending_nodes:
                                context.skipped_nodes.add(node_id)
                                context.skip_reasons[node_id] = "unmet_dependencies"
                            break
                        else:
                            raise DiagramExecutionError(f"No nodes ready to execute. Pending: {pending_nodes}")
                    
                    # Execute ready nodes (potentially in parallel)
                    execution_tasks = []
                    for node_id in ready_nodes:
                        task = self._execute_node(node_id, context, options)
                        execution_tasks.append(task)
                    
                    # Wait for all parallel executions
                    results = await asyncio.gather(*execution_tasks, return_exceptions=True)
                    
                    # Process results and yield updates
                    for node_id, result in zip(ready_nodes, results):
                        pending_nodes.remove(node_id)
                        
                        if isinstance(result, Exception):
                            error_msg = str(result)
                            yield {
                                "type": "node_error",
                                "node_id": node_id,
                                "error": error_msg
                            }
                            
                            if not options.get("continue_on_error", False):
                                raise result
                        else:
                            yield result
                            
                            # Handle conditional re-queuing for loops
                            if node_id in context.condition_values:
                                condition_result = context.condition_values[node_id]
                                logger.debug(f"Condition node {node_id} evaluated to: {condition_result}")
                                requeued_nodes = self._handle_condition_requeuing(
                                    node_id, condition_result, context, pending_nodes
                                )
                                if requeued_nodes:
                                    logger.debug(f"Re-queuing nodes after condition: {requeued_nodes}")
                                pending_nodes.update(requeued_nodes)
                
                # Yield completion
                yield {
                    "type": "execution_complete",
                    "data": {
                        "context": {
                            "node_outputs": context.node_outputs,
                            "node_execution_counts": context.node_execution_counts,
                            "condition_values": context.condition_values,
                            "execution_order": context.execution_order,
                            "total_cost": context.total_cost
                        },
                        "total_cost": context.total_cost
                    }
                }
                
            except Exception as e:
                logger.error(f"Diagram execution failed: {str(e)}")
                yield {
                    "type": "execution_failed",
                    "error": str(e)
                }
                raise
    
    def _build_execution_context(self, diagram: Dict[str, Any]) -> ExecutionContext:
        """Build execution context from diagram definition"""
        context = ExecutionContext()
        
        # Index nodes by ID, transforming frontend format to backend format
        for node in diagram.get("nodes", []):
            # Transform node: map 'data' field to 'properties' for backend executors
            transformed_node = {
                **node,
                "properties": node.get("data", {})  # Map frontend 'data' to backend 'properties'
            }
            context.nodes_by_id[node["id"]] = transformed_node
        
        # Index arrows by source and target
        for arrow in diagram.get("arrows", []):
            source = arrow["source"]
            target = arrow["target"]
            context.outgoing_arrows[source].append(arrow)
            context.incoming_arrows[target].append(arrow)
        
        # Add persons to context
        for person in diagram.get("persons", []):
            context.persons[person["id"]] = person
        
        # Add API keys to context
        for api_key in diagram.get("apiKeys", []):
            context.api_keys[api_key["id"]] = api_key
        
        return context
    
    def _can_execute_node(
        self, 
        node_id: str, 
        context: ExecutionContext,
        pending_nodes: Set[str]
    ) -> bool:
        """Check if a node can be executed given current context"""
        # Skip if already executed
        if node_id in context.execution_order:
            logger.debug(f"Node {node_id} already executed")
            return False
        
        # Check if dependencies are met
        can_execute, valid_arrows = self.dependency_resolver.check_dependencies_met(
            node_id, context
        )
        
        logger.debug(f"Node {node_id} dependencies check: can_execute={can_execute}, valid_arrows={len(valid_arrows)}")
        return can_execute
    
    async def _execute_node(
        self,
        node_id: str,
        context: ExecutionContext,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single node and update context"""
        node = context.nodes_by_id[node_id]
        node_type = normalize_node_type_to_backend(node["type"])
        
        # Check if should skip
        if self.skip_manager.should_skip(node, context):
            reason = self.skip_manager.get_skip_reason(node_id)
            context.skipped_nodes.add(node_id)
            context.skip_reasons[node_id] = reason
            
            return {
                "type": "node_skipped",
                "node_id": node_id,
                "reason": reason
            }
        
        # Get executor for node type
        executor = self.executors.get(node_type)
        if not executor:
            raise DiagramExecutionError(f"No executor found for node type: {node_type}")
        
        # Validate node
        validation = await executor.validate(node, context)
        if not validation.is_valid:
            raise DiagramExecutionError(f"Node validation failed: {validation.errors}")
        
        # Execute node
        try:
            result = await executor.execute(node, context)
            
            # Check if the executor returned a skip result
            if result.metadata and result.metadata.get("skipped"):
                # Handle skipped execution
                context.skipped_nodes.add(node_id)
                context.skip_reasons[node_id] = result.metadata.get("reason", "executor_skipped")
                
                # If the skip includes a passthrough output, update node outputs
                if result.metadata.get("passthrough") and result.output is not None:
                    context.node_outputs[node_id] = result.output
                    logger.debug(f"Node {node_id} skipped but passed through output: {str(result.output)[:50]}...")
                
                # Don't increment execution count or add to execution order for skipped nodes
                return {
                    "type": "node_skipped",
                    "node_id": node_id,
                    "reason": result.metadata.get("reason", "executor_skipped"),
                    "metadata": result.metadata,
                    "output": result.output
                }
            
            # Update context for successful execution
            context.node_outputs[node_id] = result.output
            context.node_execution_counts[node_id] += 1
            context.execution_order.append(node_id)
            context.total_cost += result.cost
            
            # Handle condition nodes
            if node_type == "condition":
                # Get condition result from metadata (for new format) or output (for backward compatibility)
                condition_result = result.metadata.get("conditionResult")
                if condition_result is not None:
                    context.condition_values[node_id] = condition_result
                elif isinstance(result.output, bool):
                    # Backward compatibility: if output is still a boolean
                    context.condition_values[node_id] = result.output
            
            # Mark iteration complete for loop control
            self.loop_controller.mark_iteration_complete(node_id)
            
            return {
                "type": "node_completed",
                "node_id": node_id,
                "output": result.output,
                "metadata": result.metadata,
                "cost": result.cost
            }
            
        except Exception as e:
            logger.error(f"Node execution failed: {node_id} - {str(e)}")
            raise
    
    def _handle_condition_requeuing(
        self,
        condition_node_id: str,
        condition_result: bool,
        context: ExecutionContext,
        current_pending: Set[str]
    ) -> Set[str]:
        """
        Handle conditional re-queuing of nodes for loop execution.
        When a condition returns false, nodes connected to the false branch
        should be re-queued for execution if they have max_iterations remaining.
        """
        requeued_nodes = set()
        
        # Get outgoing arrows from the condition node
        outgoing_arrows = context.outgoing_arrows.get(condition_node_id, [])
        
        for arrow in outgoing_arrows:
            target_node_id = arrow["target"]
            target_node = context.nodes_by_id.get(target_node_id)
            
            if not target_node:
                continue
            
            # Check if this arrow should be followed based on condition result
            source_handle = arrow.get("sourceHandle", "").lower()
            should_follow = False
            
            if "output-false" in source_handle and not condition_result:
                should_follow = True
            elif "output-true" in source_handle and condition_result:
                should_follow = True
            elif "output-false" not in source_handle and "output-true" not in source_handle:
                # Unlabeled arrows are always followed
                should_follow = True
            
            if should_follow:
                # Check if target node can be re-executed (has remaining iterations)
                target_properties = target_node.get("properties", {})
                max_iterations = target_properties.get("iterationCount")
                
                if max_iterations:
                    current_count = context.node_execution_counts.get(target_node_id, 0)
                    if current_count < max_iterations:
                        # Node can be re-executed
                        requeued_nodes.add(target_node_id)
                        logger.debug(f"Re-queuing node {target_node_id} for loop iteration {current_count + 1}/{max_iterations}")
                
        return requeued_nodes


