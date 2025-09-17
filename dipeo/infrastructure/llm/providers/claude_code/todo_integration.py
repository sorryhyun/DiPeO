"""Integration helpers for TODO collection with Claude Code."""

import logging
from typing import Any

from .todo_collector import TodoTaskCollector
from .unified_client import UnifiedClaudeCodeClient

logger = logging.getLogger(__name__)


class TodoCollectorMetrics:
    """Metrics collector for TODO operations."""

    def __init__(self):
        self.total_snapshots = 0
        self.total_todos = 0
        self.hook_invocations = 0
        self.parse_errors = 0
        self.persistence_errors = 0

    def log_summary(self):
        """Log metrics summary."""
        logger.info(
            f"[TodoMetrics] snapshots={self.total_snapshots}, "
            f"todos={self.total_todos}, hooks={self.hook_invocations}, "
            f"parse_errors={self.parse_errors}, persist_errors={self.persistence_errors}"
        )


# Global metrics instance
todo_metrics = TodoCollectorMetrics()


class TodoIntegratedClient:
    """
    Wrapper that integrates TodoTaskCollector with UnifiedClaudeCodeClient.

    This provides a convenient way to enable TODO collection for Claude Code sessions.
    """

    def __init__(
        self,
        client: UnifiedClaudeCodeClient,
        session_id: str,
        trace_id: str | None = None,
        enable_todo_collection: bool = True,
    ):
        """
        Initialize integrated client.

        Args:
            client: UnifiedClaudeCodeClient instance
            session_id: Session identifier for TODO tracking
            trace_id: Optional execution trace ID
            enable_todo_collection: Whether to enable TODO collection
        """
        self.client = client
        self.session_id = session_id
        self.trace_id = trace_id
        self.enable_todo_collection = enable_todo_collection

        self.collector: TodoTaskCollector | None = None
        if enable_todo_collection:
            self.collector = TodoTaskCollector(session_id, trace_id)
            logger.info(f"[TodoIntegration] Enabled TODO collection for session={session_id}")

    async def async_chat_with_todos(
        self,
        messages: list,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list | None = None,
        response_format: Any | None = None,
        execution_phase: Any | None = None,
        **kwargs,
    ):
        """
        Execute chat with automatic TODO collection.

        This wraps async_chat and automatically adds TodoWrite hook configuration.
        """
        # Prepare hooks_config if collection is enabled
        hooks_config = None
        if self.enable_todo_collection and self.collector:
            # Create wrapper for metrics
            original_handler = self.collector.handle_todo_write_hook

            async def metrics_wrapper(input_data, tool_use_id, context):
                todo_metrics.hook_invocations += 1
                try:
                    result = await original_handler(input_data, tool_use_id, context)
                    # Count todos if successful
                    if self.collector.current_snapshot:
                        todo_metrics.total_snapshots += 1
                        todo_metrics.total_todos += len(self.collector.current_snapshot.todos)
                    return result
                except Exception as e:
                    todo_metrics.parse_errors += 1
                    raise

            hooks_config = {"PostToolUse": [{"matcher": "TodoWrite", "hooks": [metrics_wrapper]}]}

            logger.debug("[TodoIntegration] Added TodoWrite hook for async_chat")

        # Call client with hooks_config
        return await self.client.async_chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            response_format=response_format,
            execution_phase=execution_phase,
            hooks_config=hooks_config,
            **kwargs,
        )

    async def stream_with_todos(
        self,
        messages: list,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list | None = None,
        response_format: Any | None = None,
        execution_phase: Any | None = None,
        **kwargs,
    ):
        """
        Stream chat with automatic TODO collection.

        This wraps stream and automatically adds TodoWrite hook configuration.
        """
        # Prepare hooks_config if collection is enabled
        hooks_config = None
        if self.enable_todo_collection and self.collector:
            # Create wrapper for metrics
            original_handler = self.collector.handle_todo_write_hook

            async def metrics_wrapper(input_data, tool_use_id, context):
                todo_metrics.hook_invocations += 1
                try:
                    result = await original_handler(input_data, tool_use_id, context)
                    # Count todos if successful
                    if self.collector.current_snapshot:
                        todo_metrics.total_snapshots += 1
                        todo_metrics.total_todos += len(self.collector.current_snapshot.todos)
                    return result
                except Exception as e:
                    todo_metrics.parse_errors += 1
                    raise

            hooks_config = {"PostToolUse": [{"matcher": "TodoWrite", "hooks": [metrics_wrapper]}]}

            logger.debug("[TodoIntegration] Added TodoWrite hook for stream")

        # Call client with hooks_config
        async for chunk in self.client.stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            response_format=response_format,
            execution_phase=execution_phase,
            hooks_config=hooks_config,
            **kwargs,
        ):
            yield chunk

    def get_current_todos(self):
        """Get current TODO snapshot if available."""
        if self.collector:
            return self.collector.get_current_snapshot()
        return None

    async def load_previous_todos(self):
        """Load previous TODO snapshot from disk if available."""
        if self.collector:
            return await self.collector.load_snapshot()
        return None

    def log_metrics(self):
        """Log TODO collection metrics."""
        todo_metrics.log_summary()


def create_todo_integrated_client(
    config: Any, session_id: str, trace_id: str | None = None, enable_todo_collection: bool = True
) -> TodoIntegratedClient:
    """
    Factory function to create a TODO-integrated Claude Code client.

    Args:
        config: AdapterConfig for the client
        session_id: Session identifier for TODO tracking
        trace_id: Optional execution trace ID
        enable_todo_collection: Whether to enable TODO collection

    Returns:
        TodoIntegratedClient instance
    """
    base_client = UnifiedClaudeCodeClient(config)
    return TodoIntegratedClient(
        client=base_client,
        session_id=session_id,
        trace_id=trace_id,
        enable_todo_collection=enable_todo_collection,
    )
