"""Person job handler using domain services."""

import logging
from typing import Any, Dict, Optional

from dipeo.core import BaseNodeHandler, register_handler
from dipeo.application import UnifiedExecutionContext
from dipeo.models import (
    NodeOutput,
    PersonJobNodeData,
    ForgettingMode,
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)


@register_handler
class PersonJobNodeHandler(BaseNodeHandler):
    """Person job handler that delegates to domain services."""

    @property
    def node_type(self) -> str:
        return "person_job"

    @property
    def schema(self) -> type[BaseModel]:
        return PersonJobNodeData

    @property
    def requires_services(self) -> list[str]:
        return ["person_job_execution", "llm", "diagram", "conversation"]

    @property
    def description(self) -> str:
        return "Execute person job with conversation memory"
    
    def _resolve_service(self, context: UnifiedExecutionContext, services: dict[str, Any], service_name: str) -> Optional[Any]:
        """Helper to resolve service from context or services dict."""
        service = context.get_service(service_name)
        if not service:
            service = services.get(service_name)
        return service

    async def execute(
        self,
        props: PersonJobNodeData,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute person_job node by delegating to domain service."""
        # Resolve services
        execution_service = self._resolve_service(context, services, "person_job_execution")
        llm_service = self._resolve_service(context, services, "llm")
        diagram = self._resolve_service(context, services, "diagram")
        conversation_service = self._resolve_service(context, services, "conversation")
        
        # Get current node ID and execution info
        node_id = self._extract_node_id(context)
        execution_count = self._extract_execution_count(context)
        execution_id = getattr(context.execution_state, 'id', None) if hasattr(context, 'execution_state') else None
        
        logger.debug(f"🚀 Executing person_job node: {node_id}")
        logger.debug(f"🔍 Node inputs: {list(inputs.keys())}")
        
        # Basic validation
        if not props.person:
            return NodeOutput(
                value={"default": ""}, 
                metadata={"error": "No person specified"},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )
        
        try:
            # Execute using domain service - all business logic is in the service
            result = await execution_service.execute_person_job_with_validation(
                person_id=props.person,
                node_id=node_id,
                props=props,
                inputs=inputs,
                diagram=diagram,
                execution_count=execution_count,
                llm_client=llm_service,
                conversation_service=conversation_service,
                execution_id=execution_id,
            )
            
            # Transform domain result to handler output
            return self._transform_result_to_output(result)
            
        except ValueError as e:
            # Domain validation errors
            logger.warning(f"Validation error in person job: {e}")
            return NodeOutput(
                value={"default": ""}, 
                metadata={"error": str(e)},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )
        except Exception as e:
            # Unexpected errors
            logger.error(f"Error executing person job: {e}")
            return NodeOutput(
                value={"default": ""}, 
                metadata={"error": str(e)},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )
    
    def _extract_node_id(self, context: UnifiedExecutionContext) -> str:
        """Extract node ID from context."""
        if hasattr(context.execution_state, 'current_node_id'):
            return context.execution_state.current_node_id
        elif hasattr(context, 'current_node_id'):
            return context.current_node_id
        return 'unknown'
    
    def _extract_execution_count(self, context: UnifiedExecutionContext) -> int:
        """Extract execution count from context."""
        if hasattr(context, 'get_service'):
            exec_info = context.get_service('execution_info')
            if exec_info and 'exec_count' in exec_info:
                return exec_info['exec_count']
        return 0
    
    def _transform_result_to_output(self, result: Any) -> NodeOutput:
        """Transform domain result to handler NodeOutput."""
        output_value = {"default": result.content}
        
        # Add conversation if present
        if result.conversation_state:
            output_value["conversation"] = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "tool_calls": msg.tool_calls,
                    "tool_call_id": msg.tool_call_id,
                    "person_label": result.metadata.get("person") if result.metadata else None,
                }
                for msg in result.conversation_state.messages
            ]
        
        # Build metadata
        metadata = {}
        if result.usage:
            metadata["tokens_used"] = result.usage.get("total", 0)
            metadata["token_usage"] = result.usage
            metadata["model"] = result.metadata.get("model") if result.metadata else "gpt-4.1-nano"
        if result.metadata:
            metadata.update(result.metadata)
        if result.tool_outputs:
            metadata["tool_outputs"] = result.tool_outputs
            
            # Add tool outputs to output value for downstream nodes
            for tool_output in result.tool_outputs:
                if isinstance(tool_output, dict):
                    if tool_output.get("type") == "web_search_preview":
                        output_value["web_search_results"] = tool_output.get("result")
                    elif tool_output.get("type") == "image_generation":
                        output_value["generated_image"] = tool_output.get("result")
        
        return NodeOutput(
            value=output_value, 
            metadata=metadata,
            node_id=context.current_node_id,
            executed_nodes=context.executed_nodes
        )