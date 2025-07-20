"""GraphQL resolvers for execution operations."""

import logging
from datetime import datetime

from ..context import GraphQLContext
from ..types import (
    ExecutionFilterInput,
    ExecutionID,
)
from ..types import (
    ExecutionStateType as ExecutionState,
)

logger = logging.getLogger(__name__)


class ExecutionResolver:
    """Handles execution queries and state retrieval."""

    async def get_execution(
        self, execution_id: ExecutionID, info
    ) -> ExecutionState | None:
        """Returns execution by ID."""
        try:
            context: GraphQLContext = info.context
            state_store = context.get_service("state_store")

            execution_state = await state_store.get_state(execution_id)

            if not execution_state:
                logger.debug(f"No execution found with ID: {execution_id}")
                return None

            return execution_state

        except Exception as e:
            logger.error(f"Failed to get execution {execution_id}: {e}")
            return None

    async def list_executions(
        self, filter: ExecutionFilterInput | None, limit: int, offset: int, info
    ) -> list[ExecutionState]:
        """Returns filtered execution list."""
        try:
            context: GraphQLContext = info.context
            state_store = context.get_service("state_store")

            executions = await state_store.list_executions(limit=limit + offset)

            filtered_executions = executions
            if filter:
                if filter.status:
                    filtered_executions = [
                        e
                        for e in filtered_executions
                        if e["status"] == filter.status.value
                    ]

                if filter.diagram_id:
                    filtered_executions = [
                        e
                        for e in filtered_executions
                        if e.get("diagram_id") == filter.diagram_id
                    ]

                if filter.started_after:
                    filtered_executions = [
                        e
                        for e in filtered_executions
                        if datetime.fromisoformat(e["started_at"])
                        >= filter.started_after
                    ]

                if filter.started_before:
                    filtered_executions = [
                        e
                        for e in filtered_executions
                        if datetime.fromisoformat(e["started_at"])
                        <= filter.started_before
                    ]

            paginated_executions = filtered_executions[offset : offset + limit]

            result = []
            for exec_summary in paginated_executions:
                execution_state = await state_store.get_state(
                    exec_summary["execution_id"]
                )
                if execution_state:
                    result.append(execution_state)

            return result

        except Exception as e:
            logger.error(f"Failed to list executions: {e}")
            return []


execution_resolver = ExecutionResolver()
