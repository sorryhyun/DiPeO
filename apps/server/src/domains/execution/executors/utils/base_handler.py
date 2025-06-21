"""Base handler class for all node handlers."""

from __future__ import annotations

import logging
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from ..types import RuntimeExecutionContext
from src.__generated__.models import NodeOutput
from .handler_utils import log_action


class BaseNodeHandler(ABC):
    """Base class for all node handlers with common functionality.
    
    This class provides:
    - Automatic timing and error handling
    - Service validation
    - Consistent logging
    - Standard metadata building
    
    Subclasses only need to implement the _execute_core method.
    """
    
    def __init__(
        self, 
        node_type: str, 
        schema: Type[BaseModel], 
        description: str = "",
        requires_services: Optional[List[str]] = None
    ):
        """Initialize the base handler.
        
        Args:
            node_type: The type identifier for this node
            schema: The Pydantic model for validating node properties
            description: Human-readable description of what the handler does
            requires_services: List of service names this handler requires
        """
        self.node_type = node_type
        self.schema = schema
        self.description = description
        self.requires_services = requires_services or []
        self.logger = logging.getLogger(self.__class__.__module__)
    
    async def __call__(
        self,
        props: BaseModel,
        context: RuntimeExecutionContext,
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> NodeOutput:
        """Execute the handler with common error handling and timing.
        
        This method provides the common execution wrapper that:
        1. Validates required services are available
        2. Times the execution
        3. Handles exceptions gracefully
        4. Builds consistent metadata
        5. Logs actions consistently
        
        Args:
            props: Validated node properties
            context: Runtime execution context
            inputs: Input values from connected nodes
            services: Available services
            
        Returns:
            NodeOutput with result value and metadata
        """
        start_time = time.perf_counter()
        
        try:
            # Validate required services
            self._validate_services(services)
            
            # Log start of execution
            log_action(
                self.logger,
                context.current_node_id,
                f"Starting {self.node_type} execution"
            )
            
            # Execute the handler-specific logic
            result = await self._execute_core(props, context, inputs, services)
            
            # Build success metadata
            metadata = self._build_metadata(start_time, props, context, result)
            
            # Log successful completion
            log_action(
                self.logger,
                context.current_node_id,
                f"{self.node_type} execution completed",
                execution_time=metadata.get("executionTime", 0)
            )
            
            return NodeOutput(value=result, metadata=metadata)
            
        except subprocess.TimeoutExpired as e:
            # Special handling for timeout errors
            return self._handle_timeout(start_time, props, context, e)
            
        except Exception as e:
            # General error handling
            return self._handle_error(start_time, props, context, e)
    
    @abstractmethod
    async def _execute_core(
        self,
        props: BaseModel,
        context: RuntimeExecutionContext,
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> Any:
        """Execute the handler-specific logic.
        
        This method must be implemented by subclasses to provide
        the actual node functionality.
        
        Args:
            props: Validated node properties
            context: Runtime execution context
            inputs: Input values from connected nodes
            services: Available services
            
        Returns:
            The result value to be wrapped in NodeOutput
        """
        raise NotImplementedError("Subclasses must implement _execute_core")
    
    def _validate_services(self, services: Dict[str, Any]) -> None:
        """Validate that all required services are available.
        
        Args:
            services: Dictionary of available services
            
        Raises:
            RuntimeError: If a required service is not available
        """
        for service_name in self.requires_services:
            if not services.get(service_name):
                raise RuntimeError(f"{service_name} service not available")
    
    def _build_metadata(
        self,
        start_time: float,
        props: BaseModel,
        context: RuntimeExecutionContext,
        result: Any
    ) -> Dict[str, Any]:
        """Build standard metadata for successful execution.
        
        Override this method in subclasses to add handler-specific metadata.
        
        Args:
            start_time: When execution started (from time.perf_counter())
            props: Node properties
            context: Execution context
            result: The execution result
            
        Returns:
            Dictionary of metadata
        """
        return {
            "executionTime": time.perf_counter() - start_time,
            "nodeType": self.node_type,
        }
    
    def _handle_timeout(
        self,
        start_time: float,
        props: BaseModel,
        context: RuntimeExecutionContext,
        error: subprocess.TimeoutExpired
    ) -> NodeOutput:
        """Handle timeout errors specially.
        
        Args:
            start_time: When execution started
            props: Node properties
            context: Execution context
            error: The timeout exception
            
        Returns:
            NodeOutput with timeout metadata
        """
        metadata = self._build_metadata(start_time, props, context, None)
        metadata.update({
            "timedOut": True,
            "error": f"Execution timed out: {str(error)}",
        })
        
        log_action(
            self.logger,
            context.current_node_id,
            f"{self.node_type} execution timed out",
            execution_time=metadata.get("executionTime", 0),
            error=str(error)
        )
        
        return NodeOutput(value=None, metadata=metadata)
    
    def _handle_error(
        self,
        start_time: float,
        props: BaseModel,
        context: RuntimeExecutionContext,
        error: Exception
    ) -> NodeOutput:
        """Handle general errors.
        
        Args:
            start_time: When execution started
            props: Node properties
            context: Execution context
            error: The exception that occurred
            
        Returns:
            NodeOutput with error metadata
        """
        metadata = self._build_metadata(start_time, props, context, None)
        metadata["error"] = str(error)
        
        log_action(
            self.logger,
            context.current_node_id,
            f"{self.node_type} execution failed",
            execution_time=metadata.get("executionTime", 0),
            error=str(error)
        )
        
        self.logger.exception(f"{self.node_type} handler failed")
        
        return NodeOutput(value=None, metadata=metadata)