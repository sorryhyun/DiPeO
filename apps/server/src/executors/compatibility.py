"""Compatibility layer for gradual migration from old executors to unified executor."""

from typing import Dict, Any, Optional
import logging

from .unified_executor import UnifiedExecutor
from .base_executor import BaseExecutor
from .types import ExecutorResult

logger = logging.getLogger(__name__)


class LegacyExecutorWrapper(BaseExecutor):
    """Wrapper that makes unified executor behave like old executor."""
    
    def __init__(self, unified_executor: UnifiedExecutor, node_type: str):
        self.unified_executor = unified_executor
        self.node_type = node_type
    
    async def execute(self, node: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute using unified executor but return legacy format."""
        # Convert legacy context to protocol-compliant context if needed
        result = await self.unified_executor.execute(node, context)
        
        # Convert ExecutorResult to legacy format
        legacy_result = {
            "output": result.output,
            "error": result.error,
            "metadata": result.metadata
        }
        
        if result.token_usage:
            legacy_result["token_usage"] = result.token_usage
        
        if result.execution_time:
            legacy_result["execution_time"] = result.execution_time
        
        return legacy_result


class LegacyExecutorAdapter:
    """Adapter to use unified executor in place of old executor factory."""
    
    def __init__(self, unified_executor: UnifiedExecutor, use_unified: bool = False):
        self.unified_executor = unified_executor
        self.use_unified = use_unified
        self._legacy_executors = {}
    
    async def get_executor(self, node_type: str) -> BaseExecutor:
        """Get executor for node type, using unified or legacy based on configuration."""
        if self.use_unified and node_type in self.unified_executor.get_supported_types():
            # Return wrapper for unified executor
            if node_type not in self._legacy_executors:
                self._legacy_executors[node_type] = LegacyExecutorWrapper(
                    self.unified_executor, 
                    node_type
                )
            return self._legacy_executors[node_type]
        else:
            # Fall back to original executor
            return await self._get_legacy_executor(node_type)
    
    async def _get_legacy_executor(self, node_type: str) -> BaseExecutor:
        """Get original legacy executor."""
        # Import here to avoid circular imports
        if node_type == "start":
            from .start_executor import StartExecutor
            return StartExecutor()
        elif node_type == "person_job":
            from .person_job_executor import PersonJobExecutor
            return PersonJobExecutor()
        elif node_type == "condition":
            from .condition_executor import ConditionExecutor
            return ConditionExecutor()
        elif node_type == "job":
            from .job_executor import JobExecutor
            return JobExecutor()
        elif node_type == "db":
            from .db_executor import DBExecutor
            return DBExecutor()
        elif node_type == "endpoint":
            from .endpoint_executor import EndpointExecutor
            return EndpointExecutor()
        elif node_type == "notion":
            from .notion_executor import NotionExecutor
            return NotionExecutor()
        elif node_type == "user_response":
            from .user_response_executor import UserResponseExecutor
            return UserResponseExecutor()
        else:
            raise ValueError(f"Unknown node type: {node_type}")


def create_executor_factory(use_unified: bool = False) -> LegacyExecutorAdapter:
    """
    Create executor factory with optional unified executor.
    
    Args:
        use_unified: If True, use unified executor for supported node types.
                    If False, use legacy executors.
    """
    from .registry import create_executor
    
    unified_executor = create_executor()
    return LegacyExecutorAdapter(unified_executor, use_unified)