"""Simplified main execution engine for diagram processing."""

import asyncio
import uuid
from typing import Dict, List, Optional, Tuple, Any
from collections import deque

from .execution_context import ExecutionContext
from .skip_manager import SkipManager
from .loop_controller import LoopController
from ..executors.base_executor import BaseExecutor
from ..executors.person_job_executor import PersonJobExecutor
from ..executors.condition_executor import ConditionExecutor
from ..executors.start_executor import StartExecutor


class ExecutionEngine:
    """Simplified main execution engine that orchestrates diagram execution."""
    
    def __init__(
        self,
        diagram: dict,
        memory_service,
        llm_service,
        streaming_update_callback=None
    ):
        """Initialize the execution engine.
        
        Args:
            diagram: The diagram configuration containing nodes and arrows
            memory_service: Service for memory management
            llm_service: Service for LLM interactions
            streaming_update_callback: Optional callback for streaming updates
        """
        self.diagram = diagram
        self.memory_service = memory_service
        self.llm_service = llm_service
        self.streaming_update_callback = streaming_update_callback
        
        # Initialize components
        self.context = ExecutionContext(execution_id=str(uuid.uuid4()))
        self.skip_manager = SkipManager()
        self.loop_controller = LoopController()
        
        # Create executors
        self.executors = self._create_executors()
        
        # Build node and arrow lookups
        self.nodes = {node['id']: node for node in diagram.get('nodes', [])}
        self.arrows = diagram.get('arrows', [])
        self._build_connections()
    
    def _create_executors(self) -> Dict[str, BaseExecutor]:
        """Create executor instances for each node type.
        
        Returns:
            Dictionary mapping node type to executor instance
        """
        return {
            'personJobNode': PersonJobExecutor(self.llm_service, self.memory_service),
            'conditionNode': ConditionExecutor(),
            'startNode': StartExecutor(),
            # Add more executors as they are implemented
        }
    
    def _build_connections(self) -> None:
        """Build connection mappings for efficient traversal."""
        self.outgoing_arrows: Dict[str, List[dict]] = {}
        self.incoming_arrows: Dict[str, List[dict]] = {}
        
        for arrow in self.arrows:
            source = arrow['source']
            target = arrow['target']
            
            if source not in self.outgoing_arrows:
                self.outgoing_arrows[source] = []
            self.outgoing_arrows[source].append(arrow)
            
            if target not in self.incoming_arrows:
                self.incoming_arrows[target] = []
            self.incoming_arrows[target].append(arrow)
    
    async def execute(self, initial_inputs: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], float]:
        """Main execution loop - simplified and linear.
        
        Args:
            initial_inputs: Optional initial inputs for start nodes
            
        Returns:
            Tuple of (node_outputs, total_cost)
        """
        # Initialize execution queue with start nodes
        execution_queue = deque(self._get_start_nodes())
        
        while execution_queue:
            node_id = execution_queue.popleft()
            
            if node_id not in self.nodes:
                continue
            
            node = self.nodes[node_id]
            
            # Send streaming update
            await self._send_update(node_id, "running")
            
            # Check if we should skip
            if self._should_skip_node(node):
                self.context.set_node_output(node_id, {"skipped": True})
                await self._send_update(node_id, "skipped")
                execution_queue.extend(self._get_next_nodes(node_id))
                continue
            
            # Execute the node
            executor = self.executors.get(node['type'])
            if not executor:
                await self._send_update(node_id, "error", "No executor for node type")
                continue
            
            try:
                # Validate inputs
                error = await executor.validate_inputs(node, self.context)
                if error:
                    raise ValueError(error)
                
                # Execute
                output, cost = await executor.execute(
                    node=node,
                    context=self.context,
                    skip_manager=self.skip_manager,
                    loop_controller=self.loop_controller,
                    initial_inputs=initial_inputs if node['type'] == 'startNode' else None
                )
                
                self.context.set_node_output(node_id, output, cost)
                self.context.increment_execution_count(node_id)
                
                await self._send_update(node_id, "completed", output=output)
                
                # Handle loop completion
                if self.loop_controller.is_loop_node(node_id):
                    self.loop_controller.mark_iteration(node_id)
                    if self.loop_controller.should_restart_loop(node_id):
                        loop_start_nodes = self.loop_controller.get_loop_start_nodes(node_id)
                        execution_queue.extend(loop_start_nodes)
                        continue
                
                # Queue next nodes based on execution result
                next_nodes = self._get_next_nodes(node_id, output)
                execution_queue.extend(next_nodes)
                
            except Exception as e:
                error_msg = str(e)
                self.context.set_error(node_id, error_msg)
                await self._send_update(node_id, "error", error=error_msg)
                # Continue execution with other branches
        
        return self.context.node_outputs, self.context.total_cost
    
    def _get_start_nodes(self) -> List[str]:
        """Get all start nodes in the diagram.
        
        Returns:
            List of start node IDs
        """
        return [
            node_id
            for node_id, node in self.nodes.items()
            if node['type'] == 'startNode'
        ]
    
    def _should_skip_node(self, node: Dict[str, Any]) -> bool:
        """Check if a node should be skipped.
        
        Args:
            node: The node to check
            
        Returns:
            True if node should be skipped
        """
        node_id = node['id']
        execution_count = self.context.get_execution_count(node_id)
        max_iterations = node.get('data', {}).get('maxIterations')
        
        return self.skip_manager.should_skip(node_id, execution_count, max_iterations)
    
    def _get_next_nodes(self, node_id: str, output: Any = None) -> List[str]:
        """Get the next nodes to execute based on current node output.
        
        Args:
            node_id: Current node ID
            output: Output from the current node (used for conditions)
            
        Returns:
            List of next node IDs to execute
        """
        next_nodes = []
        outgoing = self.outgoing_arrows.get(node_id, [])
        
        for arrow in outgoing:
            # Handle conditional arrows
            if arrow.get('label') in ['true', 'false'] and isinstance(output, bool):
                if (arrow['label'] == 'true' and output) or (arrow['label'] == 'false' and not output):
                    next_nodes.append(arrow['target'])
            else:
                # Non-conditional arrow
                next_nodes.append(arrow['target'])
        
        return next_nodes
    
    async def _send_update(self, node_id: str, status: str, output: Any = None, error: str = None) -> None:
        """Send a streaming update if callback is configured.
        
        Args:
            node_id: The node ID
            status: The node status (running, completed, error, skipped)
            output: Optional output data
            error: Optional error message
        """
        if self.streaming_update_callback:
            update = {
                "node_id": node_id,
                "status": status,
                "timestamp": self.context.get_execution_time()
            }
            
            if output is not None:
                update["output"] = output
            
            if error:
                update["error"] = error
            
            await self.streaming_update_callback(update)
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of the execution.
        
        Returns:
            Execution summary dictionary
        """
        return self.context.get_summary()