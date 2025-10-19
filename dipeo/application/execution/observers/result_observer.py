"""Result observer for persisting execution state changes to database."""

from typing import TYPE_CHECKING

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.enums import Status
from dipeo.domain.events import DomainEvent, EventBus, EventType

if TYPE_CHECKING:
    from dipeo.domain.execution.state.ports import ExecutionStateRepository

logger = get_module_logger(__name__)


class ResultObserver(EventBus):
    """Observer that persists execution state changes to database.

    This observer has a single responsibility: ensure all execution state
    changes are persisted to the database, including timeout and error states.

    Subscribes to:
    - EXECUTION_STARTED: Create initial execution state
    - EXECUTION_COMPLETED: Update to completed status
    - EXECUTION_ERROR: Update to failed status (handles timeouts)
    """

    def __init__(
        self,
        state_store: "ExecutionStateRepository",
    ):
        """Initialize result observer.

        Args:
            state_store: Repository for persisting execution state
        """
        self.state_store = state_store
        self._running = False

    async def start(self) -> None:
        """Start the result observer."""
        if self._running:
            return
        self._running = True
        logger.info("ResultObserver started")

    async def stop(self) -> None:
        """Stop the result observer."""
        self._running = False
        logger.info("ResultObserver stopped")

    async def handle(self, event: DomainEvent) -> None:
        """Handle domain events (EventHandler protocol)."""
        await self.consume(event)

    async def consume(self, event: DomainEvent) -> None:
        """Process domain events related to execution state persistence."""
        try:
            if event.type == EventType.EXECUTION_STARTED:
                await self._handle_execution_started(event)
            elif event.type == EventType.EXECUTION_COMPLETED:
                await self._handle_execution_completed(event)
            elif event.type == EventType.EXECUTION_ERROR:
                await self._handle_execution_error(event)
        except Exception as e:
            logger.error(f"[ResultObserver] Error processing event: {e}", exc_info=True)

    async def _handle_execution_started(self, event: DomainEvent) -> None:
        """Handle execution start event.

        Creates initial execution state in database with RUNNING status.
        """
        execution_id = event.scope.execution_id

        try:
            # Create execution state is already handled by the execution engine
            # We just log for tracking purposes
            logger.debug(f"[ResultObserver] Execution started: {execution_id}")
        except Exception as e:
            logger.error(
                f"[ResultObserver] Failed to handle execution start for {execution_id}: {e}",
                exc_info=True,
            )

    async def _handle_execution_completed(self, event: DomainEvent) -> None:
        """Handle execution completion event.

        Updates execution status to COMPLETED in database.
        """
        execution_id = event.scope.execution_id

        try:
            await self.state_store.update_status(
                execution_id=execution_id, status=Status.COMPLETED, error=None
            )
            logger.info(f"[ResultObserver] Persisted COMPLETED status for {execution_id}")
        except Exception as e:
            logger.error(
                f"[ResultObserver] Failed to persist completion for {execution_id}: {e}",
                exc_info=True,
            )

    async def _handle_execution_error(self, event: DomainEvent) -> None:
        """Handle execution error event.

        Updates execution status to FAILED in database. This handles both
        explicit errors and timeout scenarios.
        """
        execution_id = event.scope.execution_id

        # Extract error message from payload
        error_message = "Unknown error"
        if event.payload:
            if hasattr(event.payload, "error_message"):
                error_message = event.payload.error_message
            elif isinstance(event.payload, dict):
                error_message = event.payload.get("error_message", error_message)

        try:
            # Update status in cache
            await self.state_store.update_status(
                execution_id=execution_id, status=Status.FAILED, error=error_message
            )

            # Force immediate database persistence
            # update_status doesn't persist final states by design, so we must force it
            if hasattr(self.state_store, "_persistence_manager") and hasattr(
                self.state_store, "_cache_manager"
            ):
                # Get the cache entry
                entry = await self.state_store._cache_manager.get_entry(execution_id)
                if entry and entry.is_dirty:
                    # Persist immediately to database with full sync (commit)
                    await self.state_store._persistence_manager.persist_entry(
                        execution_id, entry, use_full_sync=True
                    )
                    # Mark as persisted and no longer dirty
                    entry.is_persisted = True
                    entry.is_dirty = False
                    logger.info(
                        f"[ResultObserver] Persisted FAILED status to database for {execution_id}: {error_message}"
                    )
                else:
                    logger.warning(
                        f"[ResultObserver] No dirty cache entry found for {execution_id}"
                    )
            else:
                logger.info(
                    f"[ResultObserver] Updated FAILED status in cache for {execution_id}: {error_message}"
                )
        except Exception as e:
            logger.error(
                f"[ResultObserver] Failed to persist error status for {execution_id}: {e}",
                exc_info=True,
            )
