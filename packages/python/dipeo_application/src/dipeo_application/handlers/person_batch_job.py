"""Person batch job node handler - executes prompts across multiple persons."""

import asyncio
from typing import TYPE_CHECKING, Any, Optional

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
from dipeo_core.execution import create_node_output
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
        context: RuntimeContext,
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
        context: RuntimeContext,
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

        # Handle forgetting based on memory config
        if props.memory_config and props.memory_config.forget_mode == "on_every_turn":
            if context.get_node_execution_count(context.current_node_id) > 0:
                conversation_service.clear_own_messages(person_id)

        # Add external inputs as separate messages
        if inputs:
            for key, value in inputs.items():
                if value and key != "conversation":
                    # Format the external input with its source
                    external_content = f"[Input from {key}]: {value}"
                    conversation_service.add_message(person_id, "external", external_content)

        # Add prompt to conversation
        if prompt:
            conversation_service.add_message(person_id, "user", prompt)

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
        conversation_service.add_message(person_id, "assistant", result.text)

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
