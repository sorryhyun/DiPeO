"""Parallel execution management for sub-diagrams with configurable limits and queuing."""

import asyncio
import logging
import os
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

logger = get_module_logger(__name__)


@dataclass
class SubDiagramTask:
    """Represents a sub-diagram execution task."""

    node_id: str
    diagram_name: str
    executor_func: Any  # Callable returning Envelope
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Envelope | None = None
    error: Exception | None = None


class ParallelExecutionManager:
    """Manages parallel execution of sub-diagrams with configurable limits and queuing."""

    def __init__(self, max_parallel: int | None = None):
        """Initialize the parallel execution manager.

        Args:
            max_parallel: Maximum number of parallel sub-diagrams.
                         Defaults to DIPEO_MAX_PARALLEL_SUBDIAGRAMS env var or 10.
        """
        self.max_parallel = max_parallel or int(os.getenv("DIPEO_MAX_PARALLEL_SUBDIAGRAMS", "10"))

        # Queue for tasks waiting to execute
        self.pending_queue: deque[SubDiagramTask] = deque()

        # Currently executing tasks
        self.executing_tasks: dict[str, SubDiagramTask] = {}

        # Completed tasks
        self.completed_tasks: list[SubDiagramTask] = []

        # Failed tasks
        self.failed_tasks: list[SubDiagramTask] = []

        # Execution semaphore
        self.semaphore = asyncio.Semaphore(self.max_parallel)

        # Track if queue warning has been logged
        self.queue_warning_logged = False

        # Lock for thread-safe operations
        self.lock = asyncio.Lock()

        logger.info(f"Initialized ParallelExecutionManager with max_parallel={self.max_parallel}")

    async def submit_task(
        self, node_id: str, diagram_name: str, executor_func: Any
    ) -> SubDiagramTask:
        """Submit a sub-diagram task for execution.

        Args:
            node_id: ID of the sub-diagram node
            diagram_name: Name of the diagram being executed
            executor_func: Async function that executes the sub-diagram

        Returns:
            The created task object
        """
        task = SubDiagramTask(
            node_id=node_id,
            diagram_name=diagram_name,
            executor_func=executor_func,
            created_at=datetime.now(UTC),
        )

        async with self.lock:
            # Check if we're at capacity
            if len(self.executing_tasks) >= self.max_parallel:
                # Add to queue
                self.pending_queue.append(task)

                # Log warning if this is the first queued task
                if not self.queue_warning_logged:
                    logger.warning(
                        f"Parallel execution limit ({self.max_parallel}) reached. "
                        f"Queuing sub-diagram '{diagram_name}' (node: {node_id}). "
                        f"Queue size: {len(self.pending_queue)}"
                    )
                    self.queue_warning_logged = True
                else:
                    logger.debug(
                        f"Queuing sub-diagram '{diagram_name}' (node: {node_id}). "
                        f"Queue size: {len(self.pending_queue)}"
                    )
            else:
                # Execute immediately
                await self._start_task(task)

        return task

    async def _start_task(self, task: SubDiagramTask) -> None:
        """Start executing a task."""
        task.started_at = datetime.now(UTC)
        self.executing_tasks[task.node_id] = task

        # Start execution in background
        task.task_handle = asyncio.create_task(self._execute_task(task))

    async def _execute_task(self, task: SubDiagramTask) -> None:
        """Execute a task with semaphore control."""
        try:
            async with self.semaphore:
                logger.debug(
                    f"Starting execution of sub-diagram '{task.diagram_name}' "
                    f"(node: {task.node_id})"
                )

                # Execute the sub-diagram
                result = await task.executor_func()

                task.result = result
                task.completed_at = datetime.now(UTC)

                logger.debug(
                    f"Completed execution of sub-diagram '{task.diagram_name}' "
                    f"(node: {task.node_id}) in "
                    f"{(task.completed_at - task.started_at).total_seconds():.2f}s"
                )

        except Exception as e:
            task.error = e
            task.completed_at = datetime.now(UTC)

            logger.error(
                f"Failed execution of sub-diagram '{task.diagram_name}' "
                f"(node: {task.node_id}): {e}",
                exc_info=True,
            )

        finally:
            async with self.lock:
                # Remove from executing
                if task.node_id in self.executing_tasks:
                    del self.executing_tasks[task.node_id]

                # Add to appropriate completed list
                if task.error:
                    self.failed_tasks.append(task)
                else:
                    self.completed_tasks.append(task)

                # Process next queued task if any
                if self.pending_queue:
                    next_task = self.pending_queue.popleft()
                    logger.info(
                        f"Processing queued sub-diagram '{next_task.diagram_name}' "
                        f"(node: {next_task.node_id}). "
                        f"Remaining queue size: {len(self.pending_queue)}"
                    )
                    await self._start_task(next_task)

    async def wait_for_task(self, node_id: str) -> Envelope | None:
        """Wait for a specific task to complete and return its result.

        Args:
            node_id: The node ID to wait for

        Returns:
            The task result envelope, or None if not found
        """
        # Check if already completed
        for task in self.completed_tasks:
            if task.node_id == node_id:
                return task.result

        # Check if failed
        for task in self.failed_tasks:
            if task.node_id == node_id:
                if task.error:
                    # Return error envelope
                    return EnvelopeFactory.create(
                        body={"error": str(task.error)},
                        produced_by=node_id,
                        error=type(task.error).__name__,
                        meta={"execution_status": "failed"},
                    )
                return None

        # Wait for completion
        while True:
            async with self.lock:
                # Check if in queue
                for task in self.pending_queue:
                    if task.node_id == node_id:
                        logger.debug(f"Task {node_id} is still queued")
                        break

                # Check if executing
                if node_id in self.executing_tasks:
                    logger.debug(f"Task {node_id} is executing")

                # Check completed again
                for task in self.completed_tasks:
                    if task.node_id == node_id:
                        return task.result

                for task in self.failed_tasks:
                    if task.node_id == node_id:
                        if task.error:
                            return EnvelopeFactory.create(
                                body={"error": str(task.error)},
                                produced_by=node_id,
                                error=type(task.error).__name__,
                                meta={"execution_status": "failed"},
                            )
                        return None

            # Wait a bit before checking again
            await asyncio.sleep(0.1)

    async def wait_all(self) -> dict[str, Any]:
        """Wait for all tasks to complete and return results.

        Returns:
            Dictionary mapping node_id to result envelope
        """
        # Wait for all tasks to complete
        while True:
            async with self.lock:
                if not self.pending_queue and not self.executing_tasks:
                    break
            await asyncio.sleep(0.1)

        # Collect all results
        results = {}

        for task in self.completed_tasks:
            if task.result:
                results[task.node_id] = task.result

        for task in self.failed_tasks:
            if task.error:
                results[task.node_id] = EnvelopeFactory.create(
                    body={"error": str(task.error)},
                    produced_by=task.node_id,
                    error=type(task.error).__name__,
                    meta={"execution_status": "failed"},
                )

        return results

    def get_execution_summary(self) -> dict[str, Any]:
        """Get a summary of the execution.

        Returns:
            Dictionary with execution statistics and errors
        """
        summary = {
            "total_tasks": len(self.completed_tasks) + len(self.failed_tasks),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "max_parallel": self.max_parallel,
            "queue_used": self.queue_warning_logged,
        }

        if self.failed_tasks:
            summary["errors"] = [
                {
                    "node_id": task.node_id,
                    "diagram_name": task.diagram_name,
                    "error": str(task.error) if task.error else "Unknown error",
                }
                for task in self.failed_tasks
            ]

        # Calculate timing statistics
        if self.completed_tasks or self.failed_tasks:
            all_tasks = self.completed_tasks + self.failed_tasks
            durations = [
                (task.completed_at - task.started_at).total_seconds()
                for task in all_tasks
                if task.started_at and task.completed_at
            ]
            if durations:
                summary["timing"] = {
                    "avg_duration": sum(durations) / len(durations),
                    "max_duration": max(durations),
                    "min_duration": min(durations),
                }

        return summary
