"""Simplified person_job handler with direct implementation."""

import re
from typing import TYPE_CHECKING, Any, Optional

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
from dipeo_domain.models import (
    ChatResult,
    DomainDiagram,
    DomainPerson,
    NodeOutput,
    PersonJobNodeData,
)
from pydantic import BaseModel

if TYPE_CHECKING:
    from dipeo_domain.domains.conversation.simple_service import (
        ConversationMemoryService,
    )


def substitute_template(template: str, values: dict[str, Any]) -> tuple[str, list[str]]:
    """Substitute {{placeholders}} in template with values.
    
    Returns:
        tuple: (substituted_string, list_of_missing_keys)
    """
    missing_keys = []
    
    def replacer(match):
        key = match.group(1)
        if key in values:
            return str(values[key])
        else:
            missing_keys.append(key)
            return match.group(0)  # Keep original placeholder
    
    # Match {{key}} pattern
    pattern = r'\{\{(\w+)\}\}'
    result = re.sub(pattern, replacer, template)
    
    return result, missing_keys


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
        import logging
        log = logging.getLogger(__name__)
        log.debug(f"PersonJobNodeHandler.execute - inputs: {inputs}, firstOnlyPrompt: {props.first_only_prompt}")
        
        conversation_service: "ConversationMemoryService" = services["conversation"]
        llm_service = services["llm"]
        diagram: Optional[DomainDiagram] = services.get("diagram")

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

        # Handle forgetting based on memory config
        if props.memory_config and props.memory_config.forget_mode == "on_every_turn":
            if context.get_node_execution_count(context.current_node_id) > 0:
                conversation_service.clear_own_messages(person_id)

        # Add external inputs as separate messages
        if inputs:
            # Handle special conversation input from other person nodes
            if "conversation" in inputs:
                # This is handled by judge_helper logic below
                pass
            else:
                # Add other external inputs (from DB, API, etc.) as external messages
                for key, value in inputs.items():
                    if value and key != "conversation":
                        # Format the external input with its source
                        external_content = f"[Input from {key}]: {value}"
                        conversation_service.add_message(person_id, "external", external_content)

        # Build prompt
        exec_count = context.get_node_execution_count(context.current_node_id)
        if exec_count == 0 and props.first_only_prompt:
            # For first execution, use inputs for template substitution
            # but don't include them in the prompt text
            log.debug(f"Attempting template substitution with inputs: {inputs}")
            prompt, missing_keys = substitute_template(props.first_only_prompt, inputs)
            
            if missing_keys:
                available_keys = list(inputs.keys())
                error_msg = (
                    f"Missing placeholder(s) {missing_keys} in prompt. "
                    f"Available inputs: {available_keys}. "
                    f"Make sure the edges connecting to this node are labeled with the required keys."
                )
                log.error(error_msg)
                return NodeOutput(
                    value={"default": error_msg},
                    metadata={"error": error_msg, "missing_placeholders": missing_keys}
                )
            
            log.debug(f"Template substitution successful: {prompt}")
        else:
            prompt = props.default_prompt or ""
            # Check if default_prompt has placeholders and substitute them
            if prompt and "{{" in prompt:
                prompt, missing_keys = substitute_template(prompt, inputs)
                
                if missing_keys:
                    available_keys = list(inputs.keys())
                    error_msg = (
                        f"Missing placeholder(s) {missing_keys} in default prompt. "
                        f"Available inputs: {available_keys}. "
                        f"Make sure the edges connecting to this node are labeled with the required keys."
                    )
                    log.error(error_msg)
                    return NodeOutput(
                        value={"default": error_msg},
                        metadata={"error": error_msg, "missing_placeholders": missing_keys}
                    )

        # Check if this is a judge node and add conversation context
        if "judge" in (props.label or "").lower():
            from dipeo_domain.utils.judge_helper import prepare_judge_context

            judge_context = prepare_judge_context(inputs, diagram)
            if judge_context:
                # Add judge context as external message
                conversation_service.add_message(person_id, "external", judge_context)

        # Add prompt to conversation
        if prompt:
            conversation_service.add_message(person_id, "user", prompt)

        # Get messages and add system prompt
        messages = []
        if person.llm_config and person.llm_config.system_prompt:
            messages.append(
                {"role": "system", "content": person.llm_config.system_prompt}
            )
        
        # Convert messages, mapping 'external' to 'system' for LLM compatibility
        for msg in conversation_service.get_messages(person_id):
            if msg["role"] == "external":
                # Convert external messages to system messages for LLM
                messages.append({"role": "system", "content": msg["content"]})
            else:
                messages.append(msg)

        # Call LLM
        result: ChatResult = await llm_service.complete(
            messages=messages,
            model=person.llm_config.model if person.llm_config else "gpt-4.1-nano",
            api_key_id=person.llm_config.api_key_id if person.llm_config else None,
        )

        # Store response
        conversation_service.add_message(person_id, "assistant", result.text)

        # Prepare output
        output_value = {"default": result.text}

        # Check if we need conversation output (for downstream nodes)
        if self._needs_conversation_output(context.current_node_id, diagram):
            # Add personId to messages for downstream nodes
            conv_messages = []
            for msg in conversation_service.get_messages(person_id):
                msg_with_person = msg.copy()
                msg_with_person["personId"] = person_id
                conv_messages.append(msg_with_person)
            output_value["conversation"] = conv_messages

        return NodeOutput(
            value=output_value,
            metadata={
                "model": person.llm_config.model
                if person.llm_config
                else "gpt-4.1-nano",
                "tokens_used": result.token_usage.total
                if result.token_usage and result.token_usage.total
                else 0,
                "tokenUsage": result.token_usage.model_dump() if result.token_usage else None,
            },
        )

    def _find_person(
        self, diagram: Optional[DomainDiagram], person_id: str
    ) -> Optional[DomainPerson]:
        """Find person in diagram."""
        if not diagram:
            return None
        return next((p for p in diagram.persons if p.id == person_id), None)

    def _needs_conversation_output(
        self, node_id: str, diagram: Optional[DomainDiagram]
    ) -> bool:
        """Check if any outgoing edge needs conversation data."""
        if not diagram:
            return False
        for arrow in diagram.arrows:
            if arrow.source.startswith(node_id + ":"):
                if arrow.data and arrow.data.get("contentType") == "conversation_state":
                    return True
        return False
