"""Person batch job node handler - executes prompts across multiple persons."""

import asyncio
from typing import TYPE_CHECKING, Any, Optional

from dipeo_core import BaseNodeHandler, register_handler
from dipeo_core.unified_context import UnifiedExecutionContext
from dipeo_core.execution import create_node_output
from dipeo_core.utils import is_conversation
from dipeo_application.utils.conversation_utils import MessageBuilder
from dipeo_domain.handle_utils import extract_node_id_from_handle
from dipeo_domain.models import (
    ChatResult,
    ContentType,
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

# PersonBatchJobNodeData is a type alias for PersonJobNodeData in TypeScript
# but not generated in Python, so we create it here
PersonBatchJobNodeData = PersonJobNodeData


@register_handler
class PersonBatchJobNodeHandler(BaseNodeHandler):
    """Handler for person_batch_job nodes."""

    @property
    def node_type(self) -> str:
        return "person_batch_job"

    @property
    def schema(self) -> type[BaseModel]:
        return PersonBatchJobNodeData

    @property
    def requires_services(self) -> list[str]:
        return ["conversation", "llm"]

    @property
    def description(self) -> str:
        return "Execute prompts across multiple persons in batch"

    async def execute(
        self,
        props: PersonBatchJobNodeData,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute person_batch_job node."""
        conversation_service: "ConversationMemoryService" = services["conversation"]
        llm_service = services["llm"]
        diagram: Optional[DomainDiagram] = services.get("diagram")

        # Just use the prompt as-is, inputs will be handled separately
        prompt = props.prompt

        results = {}
        metadata = {"person_count": len(props.person_ids)}
        total_tokens = 0

        if props.parallel_execution:
            # Execute in parallel
            tasks = []
            for person_id in props.person_ids:
                task = self._execute_single_person(
                    person_id=person_id,
                    prompt=prompt,
                    props=props,
                    context=context,
                    inputs=inputs,
                    diagram=diagram,
                    conversation_service=conversation_service,
                    llm_service=llm_service,
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for person_id, response in zip(props.person_ids, responses, strict=False):
                if isinstance(response, Exception):
                    results[person_id] = {"error": str(response)}
                else:
                    results[person_id] = response["text"]
                    if response.get("tokens"):
                        total_tokens += response["tokens"]
        else:
            # Execute sequentially
            for person_id in props.person_ids:
                try:
                    response = await self._execute_single_person(
                        person_id=person_id,
                        prompt=prompt,
                        props=props,
                        context=context,
                        inputs=inputs,
                        diagram=diagram,
                        conversation_service=conversation_service,
                        llm_service=llm_service,
                    )
                    results[person_id] = response["text"]
                    if response.get("tokens"):
                        total_tokens += response["tokens"]
                except Exception as e:
                    results[person_id] = {"error": str(e)}

        # Aggregate results if requested
        if props.aggregate_results:
            aggregated = "\n\n".join(
                [f"Person {pid}: {result}" for pid, result in results.items()]
            )
            output = create_node_output(
                {"default": aggregated, "results": results}, metadata
            )
        else:
            output = create_node_output(
                {"default": results, "results": results}, metadata
            )

        # Add token usage if any
        if total_tokens > 0:
            output.token_usage = {"total": total_tokens}
            output.metadata["tokens_used"] = total_tokens

        return output

    async def _execute_single_person(
        self,
        person_id: str,
        prompt: str,
        props: PersonBatchJobNodeData,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        diagram: Optional[DomainDiagram],
        conversation_service: "ConversationMemoryService",
        llm_service: Any,
    ) -> dict[str, Any]:
        """Execute a single person job within the batch."""
        # Find person
        person = self._find_person(diagram, person_id)
        if not person:
            raise ValueError(f"Person {person_id} not found")

        # Create message builder
        message_builder = MessageBuilder(conversation_service, person_id, context.execution_id)
        
        # Handle forgetting based on memory config
        if props.memory_config and props.memory_config.forget_mode == "on_every_turn":
            if context.get_node_execution_count(context.current_node_id) > 0:
                # For on_every_turn mode, clear all messages except system prompt
                # This ensures the model only sees the current input from the arrow
                conversation_service.clear_messages(person_id, keep_system=True)

        # Check if we have conversation state input
        has_conversation_state = False
        
        # Check for conversation state in inputs
        for edge in context.edges:
            if edge.get("target") and edge["target"].startswith(context.current_node_id):
                # Check if this edge has conversation_state content type
                # Parse handle ID to get node ID (format: nodeId_handleName_direction)
                source_handle = edge.get("source", "")
                # Extract node ID from handle
                source_node_id = extract_node_id_from_handle(source_handle) if source_handle else ""
                source_node_id = source_node_id or ""
                for arrow in diagram.arrows if diagram else []:
                    if arrow.source.startswith(source_node_id) and arrow.target.startswith(context.current_node_id):
                        if arrow.content_type == ContentType.conversation_state:
                            has_conversation_state = True
                            break
        
        # Process inputs based on whether we have conversation state
        if has_conversation_state and inputs:
            # For conversation state input, combine the input content with the prompt
            combined_content_parts = []
            
            # Add input content first
            for key, value in inputs.items():
                if value:
                    if key == "conversation":
                        # Extract the last user message from conversation
                        if isinstance(value, list):
                            for msg in reversed(value):
                                if msg.get("role") == "user":
                                    combined_content_parts.append(msg.get("content", ""))
                                    break
                    elif key == "default":
                        # Handle conversation data nested under 'default' key
                        if is_conversation(value):
                            for msg in reversed(value):
                                if msg.get("role") == "user":
                                    combined_content_parts.append(msg.get("content", ""))
                                    break
                        else:
                            combined_content_parts.append(str(value))
                    else:
                        combined_content_parts.append(str(value))
            
            # Append the prompt
            if prompt:
                combined_content_parts.append(prompt)
            
            # Add as a single user message
            if combined_content_parts:
                combined_content = "\n".join(combined_content_parts)
                message_builder.user(combined_content)
        else:
            # Original behavior for non-conversation-state inputs
            if inputs:
                for key, value in inputs.items():
                    if value and key != "conversation":
                        # Format the external input with its source
                        message_builder.external(key, str(value))

            # Add prompt to conversation separately only if not conversation state
            if prompt:
                message_builder.user(prompt)

        # Build messages with system prompt
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
        message_builder.assistant(result.text)

        return {
            "text": result.text,
            "tokens": result.token_usage.total
            if result.token_usage and result.token_usage.total
            else 0,
        }

    def _find_person(
        self, diagram: Optional[DomainDiagram], person_id: str
    ) -> Optional[DomainPerson]:
        """Find person in diagram."""
        if not diagram:
            return None
        return next((p for p in diagram.persons if p.id == person_id), None)
