"""Person job handler using domain services."""

import logging
from typing import Any, Dict

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

    async def execute(
        self,
        props: PersonJobNodeData,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute person_job node by delegating to domain service."""
        # Get services
        execution_service = context.get_service("person_job_execution")
        if not execution_service:
            execution_service = services.get("person_job_execution")
            
        llm_service = context.get_service("llm")
        if not llm_service:
            llm_service = services.get("llm")
            
        diagram = context.get_service("diagram")
        if not diagram:
            diagram = services.get("diagram")
            
        conversation_service = context.get_service("conversation")
        if not conversation_service:
            conversation_service = services.get("conversation")
        
        # Log execution start
        node_id = 'unknown'
        if hasattr(context.execution_state, 'current_node_id'):
            node_id = context.execution_state.current_node_id
        elif hasattr(context, 'current_node_id'):
            node_id = context.current_node_id
        logger.debug(f"🚀 Executing person_job node: {node_id}")
        logger.debug(f"🔍 Node inputs: {list(inputs.keys())}")
        
        # Validate person
        person_id = props.person
        if not person_id:
            return NodeOutput(
                value={"default": ""}, 
                metadata={"error": "No person specified"}
            )
        
        # Get execution count
        execution_count = 0
        if hasattr(context, 'get_service'):
            exec_info = context.get_service('execution_info')
            if exec_info and 'exec_count' in exec_info:
                execution_count = exec_info['exec_count']
        
        # Extract person from diagram
        person = None
        if diagram and diagram.persons:
            for p in diagram.persons:
                if p.id == person_id:
                    person = p
                    break
        
        if not person:
            return NodeOutput(
                value={"default": ""}, 
                metadata={"error": "Person not found"}
            )
        
        try:
            # Execute using domain service
            result = await execution_service.execute_person_job(
                person_id=person_id,
                node_id=node_id,
                prompt=props.default_prompt or "",
                first_only_prompt=props.first_only_prompt,
                forget_mode=ForgettingMode(props.memory_config.forget_mode) if props.memory_config and props.memory_config.forget_mode else ForgettingMode.no_forget,
                model=person.llm_config.model if person.llm_config else "gpt-4.1-nano",
                api_key_id=person.llm_config.api_key_id if person.llm_config else None,
                system_prompt=person.llm_config.system_prompt if person.llm_config else None,
                inputs=inputs,
                diagram=diagram,
                execution_count=execution_count,
                llm_client=llm_service,
                tools=props.tools,
                conversation_service=conversation_service,
                execution_id=context.execution_state.id if hasattr(context, 'execution_state') else None,
            )
            
            # Convert domain result to NodeOutput
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
                metadata["model"] = person.llm_config.model if person.llm_config else "gpt-4.1-nano"
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
            
            return NodeOutput(value=output_value, metadata=metadata)
            
        except Exception as e:
            logger.error(f"Error executing person job: {e}")
            return NodeOutput(
                value={"default": ""}, 
                metadata={"error": str(e)}
            )