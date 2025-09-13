"""Execution resolver using ServiceRegistry."""

import logging

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import STATE_STORE
from dipeo.diagram_generated.domain_models import ExecutionID, ExecutionState
from dipeo.diagram_generated.graphql_backups.inputs import ExecutionFilterInput

logger = logging.getLogger(__name__)


class ExecutionResolver:
    """Resolver for execution-related queries using service registry."""

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry

    async def get_execution(self, id: ExecutionID) -> ExecutionState | None:
        try:
            state_store = self.registry.resolve(STATE_STORE)
            execution = await state_store.get_state(str(id))

            if not execution:
                return None

            return execution

        except Exception as e:
            logger.error(f"Error fetching execution {id}: {e}")
            return None

    async def list_executions(
        self, filter: ExecutionFilterInput | None = None, limit: int = 100, offset: int = 0
    ) -> list[ExecutionState]:
        try:
            state_store = self.registry.resolve(STATE_STORE)
            executions = await state_store.list_executions(
                diagram_id=filter.diagram_id if filter else None,
                status=filter.status if filter else None,
                limit=limit,
                offset=offset,
            )

            return executions

        except Exception as e:
            logger.error(f"Error listing executions: {e}")
            return []
