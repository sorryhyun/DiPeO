"""PersonJob node executor for LLM agent interactions."""

import structlog
from typing import Any, Dict, List, Tuple

from .base import BaseNodeExecutor
from ..state import ExecutionState
from ...utils.personjob_utils import execute_personjob

logger = structlog.get_logger(__name__)


class PersonJobNodeExecutor(BaseNodeExecutor):
    """Executes PersonJob nodes which represent LLM agent interactions.
    
    PersonJob nodes handle conversations with LLM agents, maintaining
    memory and context throughout the execution.
    """
    
    async def execute(
        self, 
        node: dict, 
        vars_map: Dict[str, Any], 
        inputs: List[Any],
        state: ExecutionState,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute a PersonJob node.
        
        Args:
            node: Node configuration with personId in data
            vars_map: Variable mappings for prompt rendering
            inputs: Input values from incoming arrows
            state: Current execution state
            **kwargs: Must include 'person' and 'incoming_arrows'
            
        Returns:
            Tuple of (llm_response, cost_in_usd)
        """
        person = kwargs.get('person', {})
        incoming_arrows = kwargs.get('incoming_arrows', [])
        
        if not person:
            node_id = self.get_node_id(node)
            data = self.get_node_data(node)
            person_id = data.get("personId")
            logger.warning(
                "person_not_found",
                node_id=node_id,
                person_id=person_id
            )
            return None, 0.0
        
        try:
            # The original execute_personjob function expects different parameters
            from ...utils.arrow_utils import ArrowUtils
            
            result, cost = await execute_personjob(
                node=node,
                person=person,
                vars_map=vars_map,
                incoming_arrows=incoming_arrows,
                counts=state.counts,
                context=state.context,
                memory_service=self.memory_service,
                llm_service=self.llm_service,
                execution_id=self.execution_id,
                arrow_src_fn=ArrowUtils.get_source,
                send_status_update_fn=kwargs.get('send_status_update'),
                get_all_person_ids_fn=kwargs.get('get_all_person_ids_fn', lambda: [])
            )
            
            logger.info(
                "personjob_executed",
                node_id=self.get_node_id(node),
                cost=cost,
                has_result=result is not None
            )
            
            return result, cost
            
        except Exception as e:
            logger.error(
                "personjob_execution_failed",
                node_id=self.get_node_id(node),
                error=str(e),
                exc_info=True
            )
            raise