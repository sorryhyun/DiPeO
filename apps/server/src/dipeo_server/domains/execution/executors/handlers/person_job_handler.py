from __future__ import annotations

from typing import Any, Dict, List

from ..schemas.person_job import PersonJobProps, PersonBatchJobProps
from ..types import RuntimeExecutionContext
from ..decorators import node
from ..utils import BaseNodeHandler, log_action
from dipeo_server.domains.llm.service_utils.token_usage_service import TokenUsageService
from dipeo_server.core import OutputProcessor
from dipeo_domain import PersonConfiguration, TokenUsage


@node(
    node_type="person_job",
    schema=PersonJobProps,
    description="Execute LLM task with person context and memory",
    requires_services=["llm_service", "memory_service", "interactive_handler"]
)
class PersonJobHandler(BaseNodeHandler):
    
    async def _execute_core(
        self,
        props: PersonJobProps,
        context: RuntimeExecutionContext,
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> Any:
        """Execute LLM task with conversation context."""
        node_id = context.current_node_id
        execution_count = context.get_node_execution_count(node_id)
        
        if props.maxIteration and execution_count >= props.maxIteration:
            last_output = context.outputs.get(node_id, "No previous output")
            self._passthrough_metadata = {
                "skipped": True,
                "reason": f"Max iterations ({props.maxIteration}) reached",
                "executionCount": execution_count,
                "passthrough": True,
                "tokenUsage": TokenUsageService.zero().model_dump()
            }
            return last_output
        
        prompt = props.get_effective_prompt(execution_count)
        if not prompt:
            raise ValueError("No prompt available")

        person = await self._resolve_person(props, context)
        conversation_inputs = await self._get_conversation_inputs(context, node_id)
        final_prompt = props.substitute_variables(prompt, inputs)
        
        llm_service = services["llm_service"]
        memory_service = services["memory_service"]
        interactive_handler = services.get("interactive_handler")
        
        person_id = person.id or node_id
        
        if memory_service and props.contextCleaningRule != "no_forget":
            if props.contextCleaningRule == "on_every_turn":
                memory_service.forget_for_person(person_id)
            else:
                memory_service.forget_own_messages_for_person(
                    person_id, 
                    context.execution_id
                )
        
        history = memory_service.get_conversation_history(person_id) if memory_service else []
        messages = history + conversation_inputs + [{"role": "user", "content": final_prompt}]
        
        if props.interactive and interactive_handler:
            interactive_response = await interactive_handler(
                node_id=node_id,
                prompt=final_prompt,
                context={
                    "person_id": person_id,
                    "person_name": props.label or person.label or "Person",
                    "model": person.model,
                    "service": person.service,
                    "execution_count": execution_count
                }
            )
            if interactive_response:
                messages.append({"role": "user", "content": interactive_response})
                final_prompt += f"\n\nUser response: {interactive_response}"
        
        log_action(
            self.logger,
            node_id,
            f"Executing LLM call for person {person_id}",
            execution_count=execution_count,
            model=person.model,
            service=person.service
        )
        
        service = person.service or await self._get_service_from_api_key(str(person.api_key_id) if person.api_key_id else "", context)
        
        response = await llm_service.call_llm(
            service=service,
            api_key_id=str(person.api_key_id) if person.api_key_id else "",
            model=person.model,
            messages=messages,
            system_prompt=person.system_prompt or ""
        )
        
        usage = TokenUsageService.from_response(response)
        
        if memory_service and context.execution_id:
            await self._store_conversation(
                memory_service, 
                final_prompt, 
                response["response"],
                person_id,
                context.execution_id,
                node_id,
                props.label or "PersonJob",
                usage
            )
        
        context.increment_node_execution_count(node_id)
        
        self._llm_metadata = {
            "tokenUsage": usage.model_dump() if usage else None,
            "conversationHistory": messages[:-1],
            "model": person.model,
            "service": service,
            "executionCount": execution_count + 1
        }
        
        return response["response"]
    
    def _build_metadata(
        self,
        start_time: float,
        props: PersonJobProps,
        context: RuntimeExecutionContext,
        result: Any
    ) -> Dict[str, Any]:
        """Build metadata including LLM-specific fields."""
        metadata = super()._build_metadata(start_time, props, context, result)
        
        if hasattr(self, '_passthrough_metadata'):
            metadata.update(self._passthrough_metadata)
            delattr(self, '_passthrough_metadata')
        
        if hasattr(self, '_llm_metadata'):
            metadata.update(self._llm_metadata)
            delattr(self, '_llm_metadata')
        
        return metadata
    
    async def _resolve_person(self, props: PersonJobProps, context: RuntimeExecutionContext) -> PersonConfiguration:
        """Resolve person from ID or inline config."""
        if props.person:
            return props.person
        
        if not props.personId:
            raise ValueError("No person ID provided")
        
        person = context.persons.get(props.personId)
        
        if not person:
            raise ValueError(f"Person not found: {props.personId}")
        
        if isinstance(person, dict):
            return PersonConfiguration(**person)
        
        return person
    
    async def _get_service_from_api_key(self, api_key_id: str, context: RuntimeExecutionContext) -> str:  # noqa: ARG002
        """Get service type from API key."""
        try:
            from dipeo_server.core.context import app_context
            if app_context.api_key_service:
                api_key_info = app_context.api_key_service.get_api_key(api_key_id)
                return api_key_info.get("service", "openai")
            return "openai"
        except Exception as e:
            self.logger.warning(f"Failed to get API key info for {api_key_id}: {e}")
            return "openai"
    
    async def _get_conversation_inputs(self, context: RuntimeExecutionContext, node_id: str) -> List[Dict[str, str]]:
        """Extract conversation history from incoming connections."""
        conversation_inputs = []
        
        for edge in context.edges:
            if edge["target"] == node_id and edge.get("targetHandle") == "conversation_state":
                source_node_id = edge["source"]
                output = context.outputs.get(source_node_id)
                if OutputProcessor.is_personjob_output(output):
                    conv_history = OutputProcessor.extract_conversation_history(output) or []
                    conversation_inputs.extend(conv_history)
                    
                    value = OutputProcessor.extract_value(output)
                    if value:
                        conversation_inputs.append({"role": "user", "content": value})
        
        return conversation_inputs
    
    async def _store_conversation(
        self,
        memory_service: Any,
        user_message: str,
        assistant_message: str,
        person_id: str,
        execution_id: str,
        node_id: str,
        node_label: str,
        usage: TokenUsage
    ) -> None:
        """Store conversation messages in memory service."""
        memory_service.add_message_to_conversation(
            content=user_message,
            sender_person_id="user",
            execution_id=execution_id,
            participant_person_ids=[person_id],
            role="user",
            node_id=node_id,
            node_label=node_label
        )
        
        memory_service.add_message_to_conversation(
            content=assistant_message,
            sender_person_id=person_id,
            execution_id=execution_id,
            participant_person_ids=[person_id],
            role="assistant",
            node_id=node_id,
            node_label=node_label,
            token_count=usage.input + usage.output,
            input_tokens=usage.input,
            output_tokens=usage.output,
            cached_tokens=usage.cached
        )


@node(
    node_type="person_batch_job",
    schema=PersonBatchJobProps,
    description="Execute LLM task in batch mode",
    requires_services=["llm_service", "memory_service", "interactive_handler"]
)
class PersonBatchJobHandler(PersonJobHandler):
    """PersonBatchJob handler with batch metadata."""
    
    def _build_metadata(
        self,
        start_time: float,
        props: PersonBatchJobProps,
        context: RuntimeExecutionContext,
        result: Any
    ) -> Dict[str, Any]:
        """Add batch-specific metadata."""
        metadata = super()._build_metadata(start_time, props, context, result)
        metadata.update({
            "node_type": "person_batch_job",
            "batch_size": props.batchSize,
            "is_batch": True
        })
        return metadata