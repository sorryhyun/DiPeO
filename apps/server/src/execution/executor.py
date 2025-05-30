"""Main diagram executor that orchestrates the execution flow."""

import uuid
import asyncio
import json
import re
import structlog
from datetime import datetime
from collections import deque, Counter
from typing import Any, Dict, List, Tuple, Optional, Callable, Awaitable, Set

from .state import ExecutionState
from .scheduler import ExecutionScheduler
from .node_executor import NodeExecutor
from ..constants import NodeType
from ..services.llm_service import LLMService
from ..services.api_key_service import APIKeyService
from ..services.memory_service import MemoryService
from ..utils.dynamic_executor import DynamicExecutor
from ..utils.resolve_utils import resolve_inputs
from ..utils.output_processor import OutputProcessor

logger = structlog.get_logger(__name__)


class DiagramExecutor:
    """Executes a block diagram and returns (context, total_cost).
    
    Supports streaming node status updates via callback for real-time
    monitoring of execution progress.
    """

    def __init__(self,
                 diagram: dict,
                 memory_service: MemoryService = None,
                 status_callback: Optional[Callable[[dict], Awaitable[None]]] = None):
        """Initialize diagram executor.
        
        Args:
            diagram: Diagram configuration with nodes, arrows, and persons
            memory_service: Service for managing conversation memory
            status_callback: Optional async callback for status updates
        """
        self.diagram = diagram
        self.nodes: List[dict] = diagram.get("nodes", [])
        self.arrows: List[dict] = diagram.get("arrows", [])
        persons_list = diagram.get("persons", [])
        self.persons: Dict[str, dict] = {p["id"]: p for p in persons_list}

        self.status_callback = status_callback
        self.execution_id = str(uuid.uuid4())

        # Initialize services
        api_key_service = APIKeyService()
        self.llm_service = LLMService(api_key_service)
        self.memory_service = memory_service or MemoryService()

        # Build node lookup structures
        self.nodes_by_id: Dict[str, dict] = {n["id"]: n for n in self.nodes}
        self.node_types: Dict[str, str] = {nid: n["type"] for nid, n in self.nodes_by_id.items()}
        
        logger.debug(
            "diagram_executor_initialized",
            execution_id=self.execution_id,
            num_nodes=len(self.nodes),
            num_arrows=len(self.arrows),
            node_types=self.node_types
        )

        # Initialize execution state
        self.state = ExecutionState.create_initial(
            node_max_iterations=self._extract_max_iterations()
        )
        
        # Initialize node executor
        self.node_executor = NodeExecutor(
            nodes=self.nodes_by_id,
            persons=self.persons,
            llm_service=self.llm_service,
            memory_service=self.memory_service,
            execution_id=self.execution_id,
            send_status_update_fn=self._send_status_update
        )

    def _extract_max_iterations(self) -> Dict[str, int]:
        """Extract iterationCount for nodes that need it."""
        node_max_iterations = {}
        for node in self.nodes:
            data = node.get("data", {})
            if "iterationCount" in data and data["iterationCount"] is not None:
                try:
                    max_iter = int(data["iterationCount"])
                    if max_iter > 0:
                        node_max_iterations[node["id"]] = max_iter
                except (ValueError, TypeError):
                    pass
        return node_max_iterations

    async def _send_status_update(self, update_type: str, node_id: str, **extra_data):
        """Send status update via callback if available."""
        if self.status_callback:
            update = {
                "type": update_type,
                "nodeId": node_id,
                "timestamp": datetime.now().isoformat(),
                **extra_data
            }
            try:
                await self.status_callback(update)
            except Exception as e:
                logger.debug(
                    "status_update_failed",
                    error=str(e),
                    update_type=update_type,
                    node_id=node_id
                )

    async def run(self) -> Tuple[Dict[str, Any], float]:
        """Execute the diagram with dynamic execution order based on condition results.
        
        Returns:
            Tuple of (execution_context, total_cost_in_usd)
        """
        # Initialize dynamic executor for dependency management
        dynamic_executor = DynamicExecutor(self.nodes, self.arrows)
        execution_plan = dynamic_executor.create_execution_plan()

        if execution_plan["has_cycles"]:
            logger.warning(
                "cycles_detected",
                cycle_nodes=execution_plan['cycle_nodes']
            )

        # Initialize scheduler and execution queue
        scheduler = ExecutionScheduler(dynamic_executor, self.state)
        execution_queue = deque(execution_plan["start_nodes"])
        executed_in_iteration = set()

        # Main execution loop
        while execution_queue:
            node_id = execution_queue.popleft()
            logger.debug(
                "processing_node",
                node_id=node_id,
                queue_length=len(execution_queue)
            )
            
            # Skip if already executed in this iteration
            execution_key = f"{node_id}_{self.state.counts[node_id]}"
            if execution_key in executed_in_iteration:
                continue

            # Check if node should be skipped
            should_skip, skip_reason = scheduler.should_skip_node(node_id)
            if should_skip:
                self.state.context[node_id] = {"skipped_max_iter": True}
                await self._send_status_update("node_skipped", node_id, reason=skip_reason)
                
                next_nodes = scheduler.get_next_nodes(node_id)
                execution_queue.extend(n for n in next_nodes if n not in execution_queue)
                continue

            # Check dependencies
            deps_met, valid_incoming = scheduler.check_dependencies(node_id)
            if not deps_met:
                if not scheduler.handle_requeue(node_id):
                    break
                execution_queue.append(node_id)
                continue

            # Skip nodes with no valid incoming arrows (except start nodes)
            node = self.nodes_by_id[node_id]
            if node.get("type") not in ["startNode", "start"] and not valid_incoming:
                logger.debug(
                    "skipping_no_incoming",
                    node_id=node_id
                )
                continue

            # Execute the node
            await self._execute_node_with_tracking(
                node_id, node, valid_incoming, executed_in_iteration
            )
            
            # Reset requeue count after successful execution
            scheduler.reset_requeue_count(node_id)
            
            # Queue next nodes
            next_nodes = scheduler.get_next_nodes(node_id)
            dynamic_executor.mark_first_only_consumed(node_id)
            execution_queue.extend(n for n in next_nodes if n not in execution_queue)

            # Check for endpoint
            try:
                current_type = NodeType.from_legacy(node.get("type", ""))
                if current_type == NodeType.ENDPOINT:
                    logger.info(
                        "endpoint_reached",
                        node_id=node_id
                    )
                    break
            except Exception:
                pass

        # Log unexecuted nodes
        self._log_unexecuted_nodes(executed_in_iteration, dynamic_executor)
        
        logger.info(
            "execution_complete",
            execution_id=self.execution_id,
            total_cost=self.state.total_cost,
            nodes_executed=len(executed_in_iteration)
        )
        
        return self.state.context, self.state.total_cost

    async def _execute_node_with_tracking(
            self, 
            node_id: str, 
            node: dict, 
            valid_incoming: List[dict],
            executed_in_iteration: Set[str]
    ):
        """Execute a single node with status tracking."""
        iteration_count = self.state.counts[node_id] + 1
        logger.debug(
            "executing_node_iteration",
            node_id=node_id,
            iteration=iteration_count
        )
        
        self.state.counts[node_id] += 1
        execution_key = f"{node_id}_{self.state.counts[node_id] - 1}"
        executed_in_iteration.add(execution_key)

        await self._send_status_update("node_start", node_id)
        
        # Add small delay to make visual feedback visible
        await asyncio.sleep(0.1)

        try:
            # Resolve inputs from incoming arrows
            vars_map, inputs = resolve_inputs(node_id, valid_incoming, self.state.context)
            
            # Execute the node
            output, cost = await self.node_executor.execute_node(
                node, vars_map, inputs, valid_incoming, self.state
            )
            
            # Update state
            self.state.context[node_id] = output
            self.state.update_cost(cost)

            # Prepare output preview for status update
            output_preview = self._get_output_preview(output)
            
            await self._send_status_update(
                "node_complete", 
                node_id,
                output_preview=output_preview,
                cost=cost
            )

        except Exception as e:
            await self._send_status_update("node_error", node_id, error=str(e))
            raise

    def _get_output_preview(self, output: Any) -> Optional[str]:
        """Get a preview of node output for status updates."""
        if output is None:
            return None
            
        # Handle PersonJob output specially
        if OutputProcessor.is_personjob_output(output):
            return str(OutputProcessor.extract_value(output))[:100]
        
        # Default preview
        return str(output)[:100]

    def _log_unexecuted_nodes(self, executed_in_iteration: Set[str], 
                             dynamic_executor: DynamicExecutor):
        """Log any nodes that were not executed."""
        executed_node_ids = {key.split('_')[0] for key in executed_in_iteration}
        unexecuted = set(self.nodes_by_id.keys()) - executed_node_ids

        if unexecuted:
            legitimate_skips = set()
            for node_id in unexecuted:
                deps_met, _ = dynamic_executor.check_dependencies_met(
                    node_id,
                    set(self.state.context.keys()),
                    self.state.condition_values,
                    self.state.context
                )
                if not deps_met:
                    legitimate_skips.add(node_id)

            actually_unexecuted = unexecuted - legitimate_skips
            if actually_unexecuted:
                logger.warning(
                    "unexecuted_nodes",
                    nodes=list(actually_unexecuted)
                )

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics from the memory service."""
        return self.memory_service.get_memory_stats()

    @staticmethod
    def extract_from_object(obj: Any, path: str) -> Any:
        """Extract a value from an object using dot notation or array indexing.
        
        Examples:
            - "user.name" extracts obj['user']['name']
            - "items[0].value" extracts obj['items'][0]['value']
            - "nested.deep.value" extracts obj['nested']['deep']['value']
            
        Args:
            obj: Object to extract from
            path: Dot-notation path with optional array indices
            
        Returns:
            Extracted value or None if path not found
        """
        if obj is None:
            return None
            
        # Handle JSON strings
        if isinstance(obj, str):
            try:
                obj = json.loads(obj)
            except json.JSONDecodeError:
                return None
        
        # Split the path by dots, but handle array indices specially
        parts = re.split(r'\.', path)
        
        current = obj
        for part in parts:
            if current is None:
                return None
                
            # Check if this part contains array indexing
            array_match = re.match(r'^(\w+)\[(\d+)\]$', part)
            if array_match:
                key = array_match.group(1)
                index = int(array_match.group(2))
                
                # First get the array
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
                
                # Then get the item at index
                if isinstance(current, list) and 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                # Regular property access
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
        
        return current