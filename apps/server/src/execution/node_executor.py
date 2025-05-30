"""Node executor that dispatches to specific node type executors."""

import time
import structlog
from typing import Any, Dict, List, Tuple, Callable, Optional

from .state import ExecutionState
from .registry import node_executor_registry
from ..constants import NodeType
from ..services.llm_service import LLMService
from ..services.memory_service import MemoryService
from ..services.notion_service import NotionService
from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge

# Metrics
node_executions_total = PrometheusCounter(
    'node_executions_total', 
    'Total node executions', 
    ['node_type', 'status']
)
execution_duration_seconds = Histogram(
    'execution_duration_seconds', 
    'Node execution duration'
)
active_executions = Gauge(
    'active_executions', 
    'Number of active executions'
)
llm_cost_total = PrometheusCounter(
    'llm_cost_total', 
    'Total LLM cost in USD'
)

logger = structlog.get_logger(__name__)


class NodeExecutor:
    """Handles execution of individual nodes using the registry pattern."""
    
    def __init__(self, 
                 nodes: Dict[str, dict],
                 persons: Dict[str, dict],
                 llm_service: LLMService,
                 memory_service: MemoryService,
                 execution_id: str,
                 send_status_update_fn: Callable,
                 diagram: Optional[dict] = None):
        self.nodes_by_id = nodes
        self.persons = persons
        self.llm_service = llm_service
        self.memory_service = memory_service
        self.execution_id = execution_id
        self._send_status_update = send_status_update_fn
        self.diagram = diagram or {'nodes': list(nodes.values())}
        
    async def execute_node(
            self,
            node: dict,
            vars_map: Dict[str, Any],
            inputs: List[Any],
            incoming_arrows: List[dict],
            state: ExecutionState
    ) -> Tuple[Any, float]:
        """Dispatch to the correct node type handler using the registry."""
        node_id = node.get("id")
        node_type = node.get("type")
        
        start_time = time.time()
        active_executions.inc()
        
        logger.info(
            "executing_node",
            node_id=node_id,
            node_type=node_type,
            execution_id=self.execution_id
        )
        
        try:
            # Get executor from registry
            executor = node_executor_registry.create_executor(
                node_type=node_type,
                llm_service=self.llm_service,
                memory_service=self.memory_service,
                execution_id=self.execution_id
            )
            
            if not executor:
                logger.warning("unknown_node_type", node_type=node_type, node_id=node_id)
                node_executions_total.labels(node_type=node_type, status="error").inc()
                active_executions.dec()
                return None, 0.0
            
            # Prepare additional kwargs based on node type
            kwargs = {
                'incoming_arrows': incoming_arrows,
                'send_status_update': self._send_status_update
            }
            
            # Add person for PersonJob nodes
            if NodeType(node_type) == NodeType.PERSON_JOB:
                person_id = node.get("data", {}).get("personId")
                kwargs['person'] = self.persons.get(person_id, {})
                kwargs['get_all_person_ids_fn'] = self._get_all_person_ids_in_diagram
            
            # Add diagram for Condition nodes
            if NodeType(node_type) == NodeType.CONDITION:
                kwargs['diagram'] = self.diagram
            
            # Execute node
            result, cost = await executor.execute(
                node=node,
                vars_map=vars_map,
                inputs=inputs,
                state=state,
                **kwargs
            )
            
            # Record metrics
            execution_duration_seconds.observe(time.time() - start_time)
            node_executions_total.labels(node_type=node_type, status="success").inc()
            if cost > 0:
                llm_cost_total.inc(cost)
            
            logger.info(
                "node_completed", 
                node_id=node_id, 
                duration=time.time() - start_time,
                cost=cost
            )
            
            return result, cost
            
        except Exception as e:
            # Record error metrics
            execution_duration_seconds.observe(time.time() - start_time)
            node_executions_total.labels(node_type=node_type, status="error").inc()
            
            logger.error(
                "node_execution_failed",
                node_id=node_id,
                error=str(e),
                duration=time.time() - start_time,
                exc_info=True
            )
            raise
        finally:
            active_executions.dec()
            
    def _get_all_person_ids_in_diagram(self) -> List[str]:
        """Get all person IDs that have person_job nodes in the current diagram."""
        person_ids = set()
        for node in self.nodes_by_id.values():
            try:
                node_type = NodeType(node.get("type", ""))
                if node_type == NodeType.PERSON_JOB:
                    person_id = node.get("data", {}).get("personId")
                    if person_id:
                        person_ids.add(person_id)
            except ValueError:
                pass
        return list(person_ids)