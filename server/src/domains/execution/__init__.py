"""
Execution Domain Facade
Provides backward-compatible imports during migration
"""

from .engine.engine import CompactEngine
from .executors import create_executors, BaseExecutor, ExecutorResult, ValidationResult
from .executors.config import executor_config
from .services.execution_service import ExecutionService
from .models import ExecutionResult, NodeResult

__all__ = [
    'CompactEngine',
    'ExecutionService', 
    'ExecutionResult',
    'NodeResult',
    'create_executors',
    'BaseExecutor',
    'ExecutorResult',
    'ValidationResult',
    'executor_config'
]
