"""Simplified person_job handler with direct implementation."""

from typing import Any, Optional

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
from dipeo_domain.models import (
    ChatResult,
    ContentType,
    DomainDiagram,
    DomainPerson,
    NodeOutput,
    PersonJobNodeData,
    LLMRequestOptions,
)
from pydantic import BaseModel

from ..utils.template import substitute_template


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
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute person_job node."""
        
        conversation_service = services["conversation"]
        llm_service = services["llm"]
        diagram: Optional[DomainDiagram] = services.get("diagram")
        
        # Set the current execution ID on the conversation service
        if hasattr(conversation_service, 'current_execution_id'):
            conversation_service.current_execution_id = context.execution_id

        person_id = props.person
        if not person_id:
            return NodeOutput(
                value={"default": ""}, metadata={"error": "No person specified"}
            )
        

        # Find person config
        person = self._find_person(diagram, person_id) if diagram else None
        if not person:
            return NodeOutput(
                value={"default": ""}, metadata={"error": "Person not found"}
            )

        # Create a helper to reduce redundant parameters
        def add_message(role: str, content: str) -> None:
            """Helper to add messages with consistent parameters."""
            conversation_service.add_message_to_conversation(
                person_id=person_id,
                execution_id=context.execution_id,
                role=role,
                content=content,
                current_person_id=person_id
            )
        
        # Handle forgetting based on memory config
        if props.memory_config and props.memory_config.forget_mode == "on_every_turn":
            if context.get_node_execution_count(context.current_node_id) > 0:
                # Use interface method for forgetting only assistant messages
                conversation_service.forget_own_messages_for_person(person_id)

        # Track which keys are used in template substitution
        used_template_keys = set()
        
        # Build prompt
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
                return NodeOutput(
                    value={"default": error_msg},
                    metadata={"error": error_msg, "missing_placeholders": missing_keys}
                )
        
        # Check if we need to aggregate conversations
        if self._has_nested_conversation(inputs):
            # Create aggregation service on demand
            from dipeo_domain.domains.conversation import ConversationAggregationService
            aggregation_service = ConversationAggregationService()
            
            # Use aggregation service to handle complex conversation structures
            aggregated = aggregation_service.aggregate_conversations(inputs, diagram)
            if aggregated:
                add_message("user", aggregated)
            # Add prompt after aggregated conversation if provided
            if prompt:
                add_message("user", f"[developer]: {prompt}")
        elif self._has_conversation_state_input(context, diagram) and self._inputs_contain_conversation(inputs):
            # Handle conversation state inputs
            # Get the forget_mode for the current person
            forget_mode = props.memory_config.forget_mode if props.memory_config else None
            
            # For on_every_turn mode, we'll consolidate messages
            if forget_mode == "on_every_turn" and prompt:
                # Collect all conversation messages first
                consolidated_messages = []
                for key, value in inputs.items():
                    if conversation_service.is_conversation(value) and key not in used_template_keys:
                        for msg in value:
                            if msg.get("role") == "assistant" and msg.get("person_id"):
                                # Format message from other person
                                sender_label = msg.get("person_label", msg.get("person_id"))
                                consolidated_messages.append(f"[{sender_label}]: {msg.get('content', '')}")
                
                # Add consolidated message with developer prompt
                if consolidated_messages:
                    combined_content = "\n".join(consolidated_messages) + f"\n\n[developer]: {prompt}"
                    add_message("user", combined_content)
                else:
                    add_message("user", f"[developer]: {prompt}")
            else:
                # Original behavior for other modes
                for key, value in inputs.items():
                    if conversation_service.is_conversation(value) and key not in used_template_keys:
                        conversation_service.rebuild_conversation_context(person_id, value, forget_mode=forget_mode)
                # Add prompt if provided
                if prompt:
                    add_message("user", f"[developer]: {prompt}")
        else:
            # Original behavior for non-conversation inputs
            if inputs:
                for key, value in inputs.items():
                    if value and key not in used_template_keys and key != "conversation":
                        external_content = f"[Input from {key}]: {value}"
                        add_message("external", external_content)
            
            if prompt:
                add_message("user", prompt)

        system_prompt = person.llm_config.system_prompt if person.llm_config else None
        messages = conversation_service.prepare_messages_for_llm(person_id, system_prompt)

        # Prepare LLM request options with tools if configured
        request_options = None
        if props.tools:
            request_options = LLMRequestOptions(tools=props.tools)
        
        # Call LLM
        result: ChatResult = await llm_service.complete(
            messages=messages,
            model=person.llm_config.model if person.llm_config else "gpt-4.1-nano",
            api_key_id=person.llm_config.api_key_id if person.llm_config else None,
            options=request_options,
        )

        # Store response
        add_message("assistant", result.text)

        # Prepare output
        output_value = {"default": result.text}

        # Check if we need conversation output (for downstream nodes)
        if self._needs_conversation_output(context.current_node_id, diagram):
            # Get messages with person_id attached
            # NOTE: We do NOT apply forget_mode here - downstream nodes should receive full conversation
            messages = conversation_service.get_messages_with_person_id(person_id, forget_mode=None)
            
            # Add person labels to messages
            person_label = self._get_person_label(person_id, diagram)
            for msg in messages:
                msg["person_label"] = person_label
            
            output_value["conversation"] = messages

        # Build metadata
        metadata = {
            "model": person.llm_config.model
            if person.llm_config
            else "gpt-4.1-nano",
            "tokens_used": result.token_usage.total
            if result.token_usage and result.token_usage.total
            else 0,
            "token_usage": result.token_usage.model_dump() if result.token_usage else None,
        }
        
        # Add tool outputs to metadata if present
        if result.tool_outputs:
            metadata["tool_outputs"] = [
                output.model_dump() for output in result.tool_outputs
            ]
            
            # Also add tool outputs to the output value for downstream nodes
            for tool_output in result.tool_outputs:
                # Add web search results as a separate output
                if tool_output.type.value == "web_search_preview":
                    output_value["web_search_results"] = tool_output.result
                # Add image generation results  
                elif tool_output.type.value == "image_generation":
                    output_value["generated_image"] = tool_output.result

        return NodeOutput(
            value=output_value,
            metadata=metadata,
        )

    def _find_person(
        self, diagram: Optional[DomainDiagram], person_id: str
    ) -> Optional[DomainPerson]:
        """Find person in diagram."""
        if not diagram:
            return None
        return next((p for p in diagram.persons if p.id == person_id), None)

    def _get_person_label(self, person_id: str, diagram: Optional[DomainDiagram]) -> str:
        """Get the label for a person from the diagram."""
        if not diagram or not person_id:
            return person_id or "Person"
        
        person = self._find_person(diagram, person_id)
        if person:
            return person.label or person_id
        
        return person_id

    def _has_conversation_state_input(
        self, context: RuntimeContext, diagram: Optional[DomainDiagram]
    ) -> bool:
        """Check if this node has incoming conversation state."""
        if not diagram:
            return False
        
        for edge in context.edges:
            if edge.get("target") and edge["target"].startswith(context.current_node_id):
                source_node_id = edge.get("source", "").split(":")[0]
                for arrow in diagram.arrows:
                    if arrow.source.startswith(source_node_id) and arrow.target.startswith(context.current_node_id):
                        if arrow.content_type == ContentType.conversation_state:
                            return True
        return False
    
    def _inputs_contain_conversation(self, inputs: dict[str, Any]) -> bool:
        """Check if the inputs contain conversation data."""
        for key, value in inputs.items():
            if isinstance(value, list) and value:
                # Check if it's a list of conversation messages
                if all(isinstance(item, dict) and "role" in item and "content" in item for item in value):
                    return True
        return False
    
    def _needs_conversation_output(
        self, node_id: str, diagram: Optional[DomainDiagram]
    ) -> bool:
        """Check if any outgoing edge needs conversation data."""
        if not diagram:
            return False
        for arrow in diagram.arrows:
            if arrow.source.startswith(node_id + ":"):
                if arrow.content_type == ContentType.conversation_state:
                    return True
        return False
    
    def _has_nested_conversation(self, inputs: dict[str, Any]) -> bool:
        """Check if inputs contain nested conversation structures."""
        for key, value in inputs.items():
            # Check for direct conversation
            if isinstance(value, list) and value and all(
                isinstance(item, dict) and 'role' in item and 'content' in item 
                for item in value
            ):
                return True
                
            # Check for nested structures
            if isinstance(value, dict) and 'default' in value:
                nested = value['default']
                if isinstance(nested, list) and nested and all(
                    isinstance(item, dict) and 'role' in item and 'content' in item 
                    for item in nested
                ):
                    return True
                # Check double nesting
                if isinstance(nested, dict) and 'default' in nested:
                    double_nested = nested['default']
                    if isinstance(double_nested, list) and double_nested and all(
                        isinstance(item, dict) and 'role' in item and 'content' in item 
                        for item in double_nested
                    ):
                        return True
        
        return False
