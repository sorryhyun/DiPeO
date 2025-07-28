"""Execution resolver using UnifiedServiceRegistry."""

import logging
from typing import Optional, List

from dipeo.application.unified_service_registry import UnifiedServiceRegistry, ServiceKey
from dipeo.diagram_generated.domain_models import ExecutionID, ExecutionState
from dipeo.core.ports import StateStorePort

from ..types.inputs import ExecutionFilterInput

logger = logging.getLogger(__name__)

# Service keys
STATE_STORE = ServiceKey[StateStorePort]("state_store")


class ExecutionResolver:
    """Resolver for execution-related queries using service registry."""
    
    def __init__(self, registry: UnifiedServiceRegistry):
        self.registry = registry
    
    async def get_execution(self, id: ExecutionID) -> Optional[ExecutionState]:
        """Get a single execution by ID."""
        try:
            state_store = self.registry.require(STATE_STORE)
            execution = await state_store.get_execution(id)
            
            if not execution:
                return None
            
            # Strawberry will handle the conversion to GraphQL type
            return execution
            
        except Exception as e:
            logger.error(f"Error fetching execution {id}: {e}")
            return None
    
    async def list_executions(
        self,
        filter: Optional[ExecutionFilterInput] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ExecutionState]:
        """List executions with optional filtering."""
        try:
            state_store = self.registry.require(STATE_STORE)
            
            # Build filter criteria
            criteria = {}
            if filter:
                if filter.diagram_id:
                    criteria["diagram_id"] = filter.diagram_id
                if filter.status:
                    criteria["status"] = filter.status
                if filter.started_after:
                    criteria["started_after"] = filter.started_after
                if filter.started_before:
                    criteria["started_before"] = filter.started_before
            
            # Get executions from state store
            executions = await state_store.list_executions(
                limit=limit,
                offset=offset,
                **criteria
            )
            
            return executions
            
        except Exception as e:
            logger.error(f"Error listing executions: {e}")
            return []