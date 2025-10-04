"""State initialization for diagram execution."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram


async def initialize_execution_state(
    state_store,
    execution_id: str,
    diagram: "ExecutableDiagram",
    options: dict[str, Any],
) -> None:
    """Initialize execution state for typed diagram.

    Args:
        state_store: State store for persistence
        execution_id: Unique execution identifier
        diagram: Executable diagram to execute
        options: Execution options containing variables
    """
    from dipeo.diagram_generated import ExecutionState, LLMUsage, Status

    # Create initial execution state
    initial_state = ExecutionState(
        id=execution_id,
        status=Status.PENDING,
        diagram_id=diagram.metadata.get("id") if diagram.metadata else None,
        started_at=datetime.now().isoformat(),
        node_states={},
        node_outputs={},
        variables=options.get("variables", {}),
        is_active=True,
        llm_usage=LLMUsage(input=0, output=0),
        exec_counts={},
        executed_nodes=[],
    )

    # Store initial state
    await state_store.save_state(initial_state)
