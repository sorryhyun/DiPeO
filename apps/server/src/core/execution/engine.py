from typing import Dict, List, Set, Optional, Any, AsyncIterator
import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field

from ...exceptions import DiagramExecutionError
from .resolver import DependencyResolver
from .planner import ExecutionPlanner
from .controllers import LoopController, SkipManager
from .executors.base_executor import BaseExecutor, ExecutorFactory

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
        self.executor_factory = ExecutorFactory()
        self.llm_service = llm_service
        self.file_service = file_service
        self.executors = self._register_executors()
        self._execution_lock = asyncio.Lock()
        
    def _register_executors(self) -> Dict[str, 'BaseExecutor']:
        """Register all available executors by node type"""
        self.executor_factory.register_all_executors(
            llm_service=self.llm_service,
            file_service=self.file_service
        )
        return self.executor_factory.create_executors()
    
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
                        if self._can_execute_node(node_id, context, pending_nodes):
                            ready_nodes.append(node_id)
                    
                    if not ready_nodes:
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
                
                # Yield completion
                yield {
                    "type": "execution_completed",
                    "summary": {
                        "total_nodes": len(context.nodes_by_id),
                        "executed_nodes": len(context.execution_order),
                        "skipped_nodes": len(context.skipped_nodes),
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
        
        # Index nodes by ID
        for node in diagram.get("nodes", []):
            context.nodes_by_id[node["id"]] = node
        
        # Index arrows by source and target
        for arrow in diagram.get("arrows", []):
            source = arrow["source"]
            target = arrow["target"]
            context.outgoing_arrows[source].append(arrow)
            context.incoming_arrows[target].append(arrow)
        
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
            return False
        
        # Check if dependencies are met
        can_execute, _ = self.dependency_resolver.check_dependencies_met(
            node_id, context
        )
        
        return can_execute
    
    async def _execute_node(
        self,
        node_id: str,
        context: ExecutionContext,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single node and update context"""
        node = context.nodes_by_id[node_id]
        node_type = node["type"]
        
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
            
            # Update context
            context.node_outputs[node_id] = result.output
            context.node_execution_counts[node_id] += 1
            context.execution_order.append(node_id)
            context.total_cost += result.cost
            
            # Handle condition nodes
            if node_type == "condition" and isinstance(result.output, bool):
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


