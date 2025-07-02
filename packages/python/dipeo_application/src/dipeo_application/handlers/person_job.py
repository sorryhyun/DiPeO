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
)
from pydantic import BaseModel


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
        log.debug(f"PersonJobNodeHandler.execute - inputs: {inputs}, first_only_prompt: {props.first_only_prompt}")
        
        conversation_service = services["conversation"]
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
            prompt, missing_keys, used_keys = conversation_service.substitute_template(prompt_template, inputs)
            used_template_keys.update(used_keys)
            
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
        
        # Check if we have conversation state input
        has_conversation_state = self._has_conversation_state_input(context, diagram)
        
        # Process inputs based on whether we have conversation state
        log.debug(f"has_conversation_state: {has_conversation_state}, inputs: {bool(inputs)}")
        if has_conversation_state and inputs:
            log.debug("Processing conversation state input - delegating to conversation service")
            # Delegate all conversation input processing to the service
            remaining_prompt = conversation_service.process_conversation_inputs(
                person_id=person_id,
                inputs=inputs,
                prompt=prompt,
                used_template_keys=used_template_keys,
                diagram=diagram
            )
            
            # If prompt wasn't consumed, add it now
            if remaining_prompt:
                add_message("user", f"[developer]: {remaining_prompt}")
        else:
            # Original behavior for non-conversation-state inputs
            if inputs:
                # Handle special conversation input from other person nodes
                if "conversation" in inputs:
                    pass
                else:
                    for key, value in inputs.items():
                        if value and key != "conversation" and key not in used_template_keys:
                            external_content = f"[Input from {key}]: {value}"
                            add_message("external", external_content)

            # Check if this is a judge node and add conversation context
            if "judge" in (props.label or "").lower():
                from dipeo_domain.utils.judge_helper import prepare_judge_context

                judge_context = prepare_judge_context(inputs, diagram)
                if judge_context:
                    add_message("external", judge_context)

            if prompt:
                add_message("user", prompt)

        system_prompt = person.llm_config.system_prompt if person.llm_config else None
        messages = conversation_service.prepare_messages_for_llm(person_id, system_prompt)

        # Call LLM
        result: ChatResult = await llm_service.complete(
            messages=messages,
            model=person.llm_config.model if person.llm_config else "gpt-4.1-nano",
            api_key_id=person.llm_config.api_key_id if person.llm_config else None,
        )

        # Store response
        add_message("assistant", result.text)

        # Prepare output
        output_value = {"default": result.text}

        # Check if we need conversation output (for downstream nodes)
        if self._needs_conversation_output(context.current_node_id, diagram):
            # Get messages with person_id attached
            forget_mode = props.memory_config.forget_mode if props.memory_config else None
            output_value["conversation"] = conversation_service.get_messages_with_person_id(person_id, forget_mode)

        return NodeOutput(
            value=output_value,
            metadata={
                "model": person.llm_config.model
                if person.llm_config
                else "gpt-4.1-nano",
                "tokens_used": result.token_usage.total
                if result.token_usage and result.token_usage.total
                else 0,
                "token_usage": result.token_usage.model_dump() if result.token_usage else None,
            },
        )

    def _find_person(
        self, diagram: Optional[DomainDiagram], person_id: str
    ) -> Optional[DomainPerson]:
        """Find person in diagram."""
        if not diagram:
            return None
        return next((p for p in diagram.persons if p.id == person_id), None)

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
