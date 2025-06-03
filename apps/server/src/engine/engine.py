from typing import Dict, List, Set, Optional, Any, AsyncIterator
import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from .executors.token_utils import TokenUsage
from ..exceptions import DiagramExecutionError
from .resolver import DependencyResolver
from .planner import ExecutionPlanner
from .controllers import LoopController, SkipManager
from .executors.base_executor import BaseExecutor
from .executors import create_executors
from ..utils.node_type_utils import normalize_node_type_to_backend
from ..api.routers.monitor import broadcast_to_monitors

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
    total_tokens: TokenUsage = field(default_factory=TokenUsage)
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

    def _find_loop_nodes(self, condition_node_id: str, context: ExecutionContext) -> Set[str]:
        """
        Find all nodes that are part of a loop cycle containing the condition node.
        Uses bidirectional graph traversal to identify loop participants.
        """
        loop_nodes = set()

        # Method 1: Find nodes that can reach back to themselves through the condition
        visited_forward = set()
        visited_backward = set()

        # Forward pass: Find all nodes reachable from condition
        def traverse_forward(node_id: str, visited: Set[str]):
            if node_id in visited:
                return
            visited.add(node_id)

            for arrow in context.outgoing_arrows.get(node_id, []):
                target_id = arrow["target"]
                if target_id in context.nodes_by_id:
                    traverse_forward(target_id, visited)

        # Backward pass: Find all nodes that can reach the condition
        def traverse_backward(node_id: str, visited: Set[str]):
            if node_id in visited:
                return
            visited.add(node_id)

            for arrow in context.incoming_arrows.get(node_id, []):
                source_id = arrow["source"]
                if source_id in context.nodes_by_id:
                    traverse_backward(source_id, visited)

        traverse_forward(condition_node_id, visited_forward)
        traverse_backward(condition_node_id, visited_backward)

        # Nodes in a loop with the condition are in both sets
        loop_candidates = visited_forward.intersection(visited_backward)

        # Verify these nodes can actually form a cycle
        for node_id in loop_candidates:
            if self._can_reach_from_node(node_id, condition_node_id, context):
                loop_nodes.add(node_id)

        return loop_nodes

    def _can_reach_from_node(self, start_node: str, target_node: str, context: ExecutionContext) -> bool:
        """Check if we can reach target_node from start_node following arrows."""
        visited = set()
        queue = [start_node]

        while queue:
            current = queue.pop(0)
            if current == target_node:
                return True

            if current in visited:
                continue
            visited.add(current)

            for arrow in context.outgoing_arrows.get(current, []):
                next_node = arrow["target"]
                if next_node not in visited and next_node in context.nodes_by_id:
                    queue.append(next_node)

        return False

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
                event = {
                    "type": "execution_started",
                    "plan": {
                        "execution_order": plan.execution_order,
                        "parallel_groups": plan.parallel_groups,
                        "estimated_cost": plan.estimated_cost
                    }
                }
                yield event
                # Broadcast to monitors
                await broadcast_to_monitors(event)
                
                # Execute nodes according to plan
                pending_nodes = set(plan.execution_order)
                
                while pending_nodes:
                    # Find nodes ready to execute
                    ready_nodes = []
                    for node_id in pending_nodes:
                        can_exec = self._can_execute_node(node_id, context, pending_nodes)
                        node_type = normalize_node_type_to_backend(context.nodes_by_id[node_id]["type"])
                        
                        # Additional debug for condition nodes
                        if node_type == "condition":
                            node = context.nodes_by_id[node_id]
                            properties = node.get("properties", {})
                            condition_type = properties.get("conditionType", "expression")
                            incoming = context.incoming_arrows.get(node_id, [])
                            logger.debug(f"Condition node {node_id} (type: {condition_type}) has {len(incoming)} incoming arrows")
                            for arrow in incoming:
                                source_id = arrow["source"]
                                source_executed = source_id in context.node_outputs
                                logger.debug(f"  - Source {source_id}: executed={source_executed}")
                        
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
                            event = {
                                "type": "node_error",
                                "node_id": node_id,
                                "error": error_msg
                            }
                            yield event
                            # Broadcast to monitors
                            await broadcast_to_monitors(event)
                            
                            if not options.get("continue_on_error", False):
                                raise result
                        else:
                            yield result
                            # Broadcast to monitors
                            await broadcast_to_monitors(result)
                            
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
                event = {
                    "type": "execution_complete",
                    "data": {
                        "context": {
                            "node_outputs": context.node_outputs,
                            "node_execution_counts": context.node_execution_counts,
                            "condition_values": context.condition_values,
                            "execution_order": context.execution_order,
                            "tokens": context.total_tokens.to_dict(),
                        },
                        "total_token_count": context.total_tokens.total
                    }
                }
                yield event
                # Broadcast to monitors
                await broadcast_to_monitors(event)
                
            except Exception as e:
                logger.error(f"Diagram execution failed: {str(e)}")
                event = {
                    "type": "execution_failed",
                    "error": str(e)
                }
                yield event
                # Broadcast to monitors
                await broadcast_to_monitors(event)
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
        # For nodes with iteration count, allow re-execution up to the limit
        node = context.nodes_by_id.get(node_id)
        if node:
            properties = node.get("properties", {})
            max_iterations = properties.get("iterationCount")
            if max_iterations:
                current_count = context.node_execution_counts.get(node_id, 0)
                if current_count >= max_iterations:
                    logger.debug(f"Node {node_id} reached max iterations: {current_count}/{max_iterations}")
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
        # Get type from node properties (data) which contains the actual node type
        # Frontend sends: {type: "startNode", data: {type: "start", ...}}
        properties = node.get("properties", {})
        node_type = normalize_node_type_to_backend(properties.get("type", node["type"]))
        
        # Check if should skip
        if self.skip_manager.should_skip(node, context):
            reason = self.skip_manager.get_skip_reason(node_id)
            context.skipped_nodes.add(node_id)
            context.skip_reasons[node_id] = reason
            
            event = {
                "type": "node_skipped",
                "node_id": node_id,
                "reason": reason
            }
            # Broadcast to monitors
            await broadcast_to_monitors(event)
            return event
        
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
                event = {
                    "type": "node_skipped",
                    "node_id": node_id,
                    "reason": result.metadata.get("reason", "executor_skipped"),
                    "metadata": result.metadata,
                    "output": result.output
                }
                # Broadcast to monitors
                await broadcast_to_monitors(event)
                return event
            
            # Update context for successful execution
            context.node_outputs[node_id] = result.output
            context.node_execution_counts[node_id] += 1
            context.execution_order.append(node_id)
            context.total_tokens.input += result.tokens.input
            context.total_tokens.output += result.tokens.output
            context.total_tokens.cached += result.tokens.cached
            
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
            
            event = {
                "type": "node_completed",
                "node_id": node_id,
                "output": result.output,
                "metadata": result.metadata,
                "token_count": result.tokens.input + result.tokens.output
            }
            # Broadcast to monitors
            await broadcast_to_monitors(event)
            return event
            
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
        """Handle conditional re-queuing of nodes for loop execution."""
        requeued_nodes = set()

        # Only re-queue if condition says to continue (false = continue loop)
        if not condition_result:
            # Find all nodes in the loop
            loop_nodes = self._find_loop_nodes(condition_node_id, context)
            logger.debug(f"Found {len(loop_nodes)} nodes in loop with condition {condition_node_id}")

            for node_id in loop_nodes:
                # Skip the condition node itself
                if node_id == condition_node_id:
                    continue

                node = context.nodes_by_id.get(node_id)
                if not node:
                    continue

                # Check if node can be re-executed
                properties = node.get("properties", {})
                max_iterations = properties.get("iterationCount")

                if max_iterations:
                    current_count = context.node_execution_counts.get(node_id, 0)
                    if current_count < max_iterations:
                        requeued_nodes.add(node_id)
                        logger.debug(
                            f"Re-queuing {node_id} for iteration {current_count + 1}/{max_iterations}"
                        )
                    else:
                        logger.debug(
                            f"Not re-queuing {node_id}: reached max iterations {max_iterations}"
                        )
                else:
                    # Nodes without iterationCount can also be re-queued if part of loop
                    node_type = node.get("type", "").lower()
                    if node_type not in ["condition", "conditionnode"]:
                        requeued_nodes.add(node_id)
                        logger.debug(f"Re-queuing {node_id} (no iteration limit)")
        
        # Also re-queue the condition node itself so it can check again after nodes execute
        if not condition_result:
            requeued_nodes.add(condition_node_id)
            logger.debug(f"Re-queuing condition node {condition_node_id} for next iteration check")

        return requeued_nodes