from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
import logging
from ...utils.token_usage import TokenUsage

if TYPE_CHECKING:
    from ..engine import ExecutionContext

from .validator import (
    ValidationResult
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutorResult:
    """Result from executor execution"""
    output: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens: TokenUsage = field(default_factory=TokenUsage)
    error: Optional[str] = None
    execution_time: float = 0.0


class BaseExecutor(ABC):
    """
    Base class for all node executors.
    Provides common functionality for validation, execution, and utilities.
    """
    
    def __init__(self):
        self.logger = logger
    
    @abstractmethod
    async def validate(self, node: Dict[str, Any], context: 'ExecutionContext') -> ValidationResult:
        """
        Validate node configuration before execution.
        
        Args:
            node: The node to validate
            context: Current execution context
            
        Returns:
            ValidationResult with validity status and any errors/warnings
        """
        pass
    
    @abstractmethod
    async def execute(self, node: Dict[str, Any], context: 'ExecutionContext') -> ExecutorResult:
        """
        Execute the node and return results.
        
        Args:
            node: The node to execute
            context: Current execution context
            
        Returns:
            ExecutorResult with output and metadata
        """
        pass
    
    def get_node_type(self) -> str:
        """
        Get the node type this executor handles.
        By convention, uses the class name without 'Executor' suffix.
        """
        class_name = self.__class__.__name__
        if class_name.endswith('Executor'):
            return class_name[:-8].lower()
        return class_name.lower()


    
