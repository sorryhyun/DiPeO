"""Base handler class for all node handlers."""

from __future__ import annotations

import logging
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from ..types import RuntimeExecutionContext
from dipeo_domain import NodeOutput
from .handler_utils import log_action


class BaseNodeHandler(ABC):
    # Base class for all node handlers with common functionality.
    
    def __init__(
        self, 
        node_type: str, 
        schema: Type[BaseModel], 
        description: str = "",
        requires_services: Optional[List[str]] = None
    ):
        # Initialize the base handler.

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
        # Execute the handler with common error handling and timing.

        start_time = time.perf_counter()
        
        try:
            self._validate_services(services)
            
            log_action(
                self.logger,
                context.current_node_id,
                f"Starting {self.node_type} execution"
            )
            result = await self._execute_core(props, context, inputs, services)

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
            return self._handle_timeout(start_time, props, context, e)
            
        except Exception as e:
            return self._handle_error(start_time, props, context, e)
    
    @abstractmethod
    async def _execute_core(
        self,
        props: BaseModel,
        context: RuntimeExecutionContext,
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> Any:
        # Execute the handler-specific logic.

        raise NotImplementedError("Subclasses must implement _execute_core")
    
    def _validate_services(self, services: Dict[str, Any]) -> None:
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
        # Handle timeout errors specially.
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
        # Handle general errors.

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