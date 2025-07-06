"""Simplified person_job handler with direct implementation."""

from typing import Any, Optional, List, Dict

from dipeo_core import BaseNodeHandler, register_handler
from dipeo_core.unified_context import UnifiedExecutionContext
from dipeo_domain.models import (
    ChatResult,
    DomainDiagram,
    NodeOutput,
    PersonJobNodeData,
    LLMRequestOptions,
)
from dipeo_domain.domains.conversation.on_every_turn_handler import OnEveryTurnHandler
from pydantic import BaseModel

from ..utils.template import substitute_template
from ..utils.conversation_utils import ConversationUtils, InputDetector, MessageBuilder


@register_handler
class PersonJobNodeHandler(BaseNodeHandler):
    """Simplified person_job handler."""

    @property
    def node_type(self) -> str:
        return "person_job"

    @property
    def schema(self) -> type[BaseModel]:
        return PersonJobNodeData

    @property
    def requires_services(self) -> list[str]:
        return ["conversation", "llm"]

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
        """Execute person_job node."""
        
        # Initialize services
        conversation_service = services["conversation"]
        llm_service = services["llm"]
        diagram: Optional[DomainDiagram] = services.get("diagram")
        
        # Set execution context
        if hasattr(conversation_service, 'current_execution_id'):
            conversation_service.current_execution_id = context.execution_id

        # Validate person
        person_id = props.person
        if not person_id:
            return self._error_output("No person specified")
        
        person = ConversationUtils.find_person(diagram, person_id)
        if not person:
            return self._error_output("Person not found")

        # Create message builder
        message_builder = MessageBuilder(conversation_service, person_id, context.execution_id)
        
        # Handle memory forgetting
        if self._should_forget_messages(props, context):
            conversation_service.forget_own_messages_for_person(person_id)
        
        # Process prompt
        prompt, used_keys, error = await self._process_prompt(props, context, inputs)
        if error:
            return error
        
        # Handle conversation inputs
        await self._handle_conversation_inputs(
            inputs, prompt, props, message_builder, 
            conversation_service, used_keys, person_id, context, diagram
        )

        # Prepare and execute LLM call
        system_prompt = person.llm_config.system_prompt if person.llm_config else None
        messages = conversation_service.prepare_messages_for_llm(person_id, system_prompt)
        
        result = await self._execute_llm_call(
            llm_service, messages, person, props.tools
        )
        
        # Store response
        message_builder.assistant(result.text)
        
        # Build output
        return self._build_output(
            result, person_id, person, props, context, 
            conversation_service, diagram
        )

    def _error_output(self, error_msg: str) -> NodeOutput:
        """Create an error output."""
        return NodeOutput(
            value={"default": ""}, 
            metadata={"error": error_msg}
        )
    
    def _should_forget_messages(self, props: PersonJobNodeData, context: UnifiedExecutionContext) -> bool:
        """Check if messages should be forgotten based on memory config."""
        forget_mode = props.memory_config.forget_mode if props.memory_config else None
        execution_count = context.get_node_execution_count(context.current_node_id)
        return OnEveryTurnHandler.should_forget_messages(execution_count, forget_mode)
    
    async def _process_prompt(
        self, 
        props: PersonJobNodeData, 
        context: UnifiedExecutionContext, 
        inputs: Dict[str, Any]
    ) -> tuple[str, set[str], Optional[NodeOutput]]:
        """Process prompt template and return (prompt, used_keys, error)."""
        used_template_keys = set()
        
        # Select prompt based on execution count
        exec_count = context.get_node_execution_count(context.current_node_id)
        if exec_count == 0 and props.first_only_prompt:
            prompt_template = props.first_only_prompt
        else:
            prompt_template = props.default_prompt or ""
        
        # Substitute template if needed
        prompt = prompt_template
        if prompt_template and "{{" in prompt_template:
            prompt, missing_keys, used_keys = substitute_template(prompt_template, inputs)
            used_template_keys.update(used_keys)
            
            if missing_keys:
                available_keys = list(inputs.keys())
                error_msg = (
                    f"Missing placeholder(s) {missing_keys} in prompt. "
                    f"Available inputs: {available_keys}. "
                    f"Make sure the edges connecting to this node are labeled with the required keys."
                )
                return "", used_template_keys, self._error_output(error_msg)
        
        return prompt, used_template_keys, None
    
    async def _consolidate_on_every_turn_messages(
        self, 
        inputs: Dict[str, Any], 
        used_template_keys: set[str],
        diagram: Optional[DomainDiagram] = None
    ) -> Optional[str]:
        """Consolidate messages for on_every_turn mode."""
        consolidated_content, _ = OnEveryTurnHandler.consolidate_conversation_inputs(
            inputs, used_template_keys, diagram
        )
        return consolidated_content if consolidated_content else None
    
    async def _handle_conversation_inputs(
        self,
        inputs: Dict[str, Any],
        prompt: str,
        props: PersonJobNodeData,
        message_builder: MessageBuilder,
        conversation_service: Any,
        used_template_keys: set[str],
        person_id: str,
        context: UnifiedExecutionContext,
        diagram: Optional[DomainDiagram]
    ) -> None:
        """Handle all conversation input scenarios."""
        
        # Case 1: Nested conversation
        if InputDetector.has_nested_conversation(inputs):
            from dipeo_domain.domains.conversation import ConversationAggregationService
            aggregation_service = ConversationAggregationService()
            aggregated = aggregation_service.aggregate_conversations(inputs, diagram)
            if aggregated:
                message_builder.user(aggregated)
            if prompt:
                message_builder.developer(prompt)
        
        # Case 2: Conversation state input
        elif (ConversationUtils.has_conversation_state_input(context, diagram) and 
              InputDetector.contains_conversation(inputs)):
            forget_mode = props.memory_config.forget_mode if props.memory_config else None
            
            if forget_mode == "on_every_turn" and prompt:
                consolidated = await self._consolidate_on_every_turn_messages(
                    inputs, used_template_keys, diagram
                )
                if consolidated:
                    message_builder.user(f"{consolidated}\n[developer]: {prompt}")
                else:
                    message_builder.developer(prompt)
            else:
                # Rebuild conversation context for other modes
                for key, value in inputs.items():
                    if conversation_service.is_conversation(value) and key not in used_template_keys:
                        conversation_service.rebuild_conversation_context(
                            person_id, value, forget_mode=forget_mode
                        )
                if prompt:
                    message_builder.developer(prompt)
        
        # Case 3: Non-conversation inputs
        else:
            for key, value in inputs.items():
                if value and key not in used_template_keys and key != "conversation":
                    message_builder.external(key, str(value))
            if prompt:
                message_builder.user(prompt)
    
    async def _execute_llm_call(
        self,
        llm_service: Any,
        messages: List[Dict[str, str]],
        person: Any,
        tools: Optional[List[Any]] = None
    ) -> ChatResult:
        """Execute LLM call with proper configuration."""
        request_options = LLMRequestOptions(tools=tools) if tools else None
        
        return await llm_service.complete(
            messages=messages,
            model=person.llm_config.model if person.llm_config else "gpt-4.1-nano",
            api_key_id=person.llm_config.api_key_id if person.llm_config else None,
            options=request_options,
        )
    
    def _build_output(
        self,
        result: ChatResult,
        person_id: str,
        person: Any,
        props: PersonJobNodeData,
        context: UnifiedExecutionContext,
        conversation_service: Any,
        diagram: Optional[DomainDiagram]
    ) -> NodeOutput:
        """Build the node output with all necessary data."""
        output_value = {"default": result.text}
        
        # Add conversation output if needed
        if ConversationUtils.needs_conversation_output(context.current_node_id, diagram):
            forget_mode = props.memory_config.forget_mode if props.memory_config else None
            
            
            messages = conversation_service.get_messages_with_person_id(person_id, forget_mode=forget_mode)
            
            # Add person labels to messages
            person_label = ConversationUtils.get_person_label(person_id, diagram)
            for msg in messages:
                msg["person_label"] = person_label
            
            output_value["conversation"] = messages
        
        # Build metadata
        metadata = {
            "model": person.llm_config.model if person.llm_config else "gpt-4.1-nano",
            "tokens_used": result.token_usage.total if result.token_usage and result.token_usage.total else 0,
            "token_usage": result.token_usage.model_dump() if result.token_usage else None,
        }
        
        # Add tool outputs if present
        if result.tool_outputs:
            metadata["tool_outputs"] = [
                output.model_dump() for output in result.tool_outputs
            ]
            
            # Add tool outputs to output value for downstream nodes
            for tool_output in result.tool_outputs:
                if tool_output.type.value == "web_search_preview":
                    output_value["web_search_results"] = tool_output.result
                elif tool_output.type.value == "image_generation":
                    output_value["generated_image"] = tool_output.result
        
        return NodeOutput(value=output_value, metadata=metadata)
