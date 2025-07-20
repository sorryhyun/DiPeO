
import asyncio
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.unified_service_registry import (
    CONVERSATION_SERVICE,
    LLM_SERVICE,
    DIAGRAM,
    CURRENT_NODE_INFO,
    PROMPT_BUILDER,
)
from dipeo.core.static.generated_nodes import PersonBatchJobNode
from dipeo.core.execution.node_output import DataOutput, NodeOutputProtocol
from dipeo.core.utils import is_conversation
from dipeo.models import (
    ChatResult,
    ContentType,
    DomainDiagram,
    DomainPerson,
    Message,
    NodeType,
    PersonID,
    PersonJobNodeData,
    extract_node_id_from_handle,
)

if TYPE_CHECKING:
    from dipeo.core.dynamic.conversation_manager import ConversationManager
    from dipeo.core.dynamic.execution_context import ExecutionContext

# PersonBatchJobNodeData is a type alias for PersonJobNodeData in TypeScript
# but not generated in Python, so we create it here
PersonBatchJobNodeData = PersonJobNodeData


@register_handler
class PersonBatchJobNodeHandler(TypedNodeHandler[PersonBatchJobNode]):
    # TODO: This handler expects fields (person_ids, prompt, parallel_execution, aggregate_results)
    # that don't exist in PersonJobNodeData. This needs to be fixed either by:
    # 1. Creating a proper PersonBatchJobNodeData model with these fields, or
    # 2. Refactoring the handler to use PersonJobNodeData fields correctly
    
    def __init__(self, llm_service=None, diagram_storage_service=None, conversation_service=None):
        self.llm_service = llm_service
        self.diagram_storage_service = diagram_storage_service
        self.conversation_service = conversation_service


    @property
    def node_class(self) -> type[PersonBatchJobNode]:
        return PersonBatchJobNode
    
    @property
    def node_type(self) -> str:
        return NodeType.person_batch_job.value

    @property
    def schema(self) -> type[BaseModel]:
        return PersonBatchJobNodeData
    

    @property
    def requires_services(self) -> list[str]:
        return ["conversation_service", "llm_service"]

    @property
    def description(self) -> str:
        return "Execute prompts across multiple persons in batch"


    async def execute(
        self,
        node: PersonBatchJobNode,
        context: "ExecutionContext",
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutputProtocol:
        # Note: The current implementation expects fields like person_ids, prompt, parallel_execution, aggregate_results
        # which don't exist in PersonBatchJobNode. For now, we'll pass the node directly.
        return await self._execute_batch(node, context, inputs, services)
    
    async def _execute_batch(
        self,
        node: PersonBatchJobNode,
        context: "ExecutionContext",
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutputProtocol:
        # Get services from services dict
        conversation_service: ConversationManager = services.get(CONVERSATION_SERVICE.name)
        llm_service = self.llm_service or services.get(LLM_SERVICE.name)
        diagram: DomainDiagram | None = services.get(DIAGRAM.name)
        
        if not conversation_service or not llm_service:
            raise ValueError("Required services not available")

        # FIXME: PersonBatchJobNode doesn't have a prompt field - this needs to be fixed
        # For now, using default_prompt as a fallback
        prompt = getattr(node, 'prompt', node.default_prompt or '')

        results = {}
        # FIXME: PersonBatchJobNode doesn't have person_ids field
        # For now, create a single-person list using person_id
        person_ids = getattr(node, 'person_ids', [node.person_id] if node.person_id else [])
        metadata = {"person_count": len(person_ids)}
        total_tokens = 0

        # FIXME: PersonBatchJobNode doesn't have parallel_execution field
        parallel_execution = getattr(node, 'parallel_execution', False)
        if parallel_execution:
            # Execute in parallel
            tasks = []
            for person_id in person_ids:
                task = self._execute_single_person(
                    person_id=person_id,
                    prompt=prompt,
                    node=node,
                    context=context,
                    inputs=inputs,
                    diagram=diagram,
                    conversation_service=conversation_service,
                    llm_service=llm_service,
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for person_id, response in zip(person_ids, responses, strict=False):
                if isinstance(response, Exception):
                    results[person_id] = {"error": str(response)}
                else:
                    results[person_id] = response["text"]
                    if response.get("tokens"):
                        total_tokens += response["tokens"]
        else:
            # Execute sequentially
            for person_id in person_ids:
                try:
                    response = await self._execute_single_person(
                        person_id=person_id,
                        prompt=prompt,
                        node=node,
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
        # FIXME: PersonBatchJobNode doesn't have aggregate_results field
        aggregate_results = getattr(node, 'aggregate_results', True)
        if aggregate_results:
            aggregated = "\n\n".join(
                [f"Person {pid}: {result}" for pid, result in results.items()]
            )
            output = DataOutput(
                value={"default": aggregated, "results": results},
                node_id=node.id,
                metadata=metadata
            )
        else:
            output = DataOutput(
                value={"default": results, "results": results},
                node_id=node.id,
                metadata=metadata
            )

        # Add token usage if any
        if total_tokens > 0:
            output.metadata["token_usage"] = {"total": total_tokens}
            output.metadata["tokens_used"] = total_tokens

        return output

    async def _execute_single_person(
        self,
        person_id: str,
        prompt: str,
        node: PersonBatchJobNode,
        context: "ExecutionContext",
        inputs: dict[str, Any],
        diagram: DomainDiagram | None,
        conversation_service: "ConversationManager",
        llm_service: Any,
        services: dict[str, Any],
    ) -> dict[str, Any]:
        # Find person
        person = self._find_person(diagram, person_id)
        if not person:
            raise ValueError(f"Person {person_id} not found")

        # Create message builder
        # TODO: Add method to get execution_id from context protocol
        execution_id = getattr(context, '_execution_id', 'unknown')
        prompt_builder = services.get(PROMPT_BUILDER.name)
        
        # Apply memory settings if configured
        if node.memory_settings:
            execution_count = 0
            if hasattr(context, 'get_node_execution_count'):
                execution_count = context.get_node_execution_count(node.id)
            
            if execution_count > 0:
                # Apply memory settings for subsequent executions
                # Note: This handler needs refactoring to properly support memory settings
                # For now, we maintain backward compatibility
                pass

        # Check if we have conversation state input
        has_conversation_state = False
        
        # Check for conversation state in inputs
        # Get current node ID from service
        current_node_id = None
        node_info = services.get(CURRENT_NODE_INFO.name)
        if node_info and 'node_id' in node_info:
            current_node_id = node_info['node_id']
        
        # Check arrows directly from diagram to determine if we have conversation state inputs
        if diagram and current_node_id:
            for arrow in diagram.arrows:
                # Check if arrow targets current node
                target_node_id = extract_node_id_from_handle(arrow.target) if arrow.target else ""
                if target_node_id == current_node_id:
                    # Check if this arrow has conversation_state content type
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
                                if isinstance(msg, dict) and msg.get("role") == "user":
                                    combined_content_parts.append(msg.get("content", ""))
                                    break
                                elif isinstance(msg, Message) and msg.from_person_id == "system" and msg.message_type == "system_to_person":
                                    combined_content_parts.append(msg.content)
                                    break
                    elif key == "default":
                        # Handle conversation data nested under 'default' key
                        if is_conversation(value):
                            for msg in reversed(value):
                                if isinstance(msg, dict) and msg.get("role") == "user":
                                    combined_content_parts.append(msg.get("content", ""))
                                    break
                                elif isinstance(msg, Message) and msg.from_person_id == "system" and msg.message_type == "system_to_person":
                                    combined_content_parts.append(msg.content)
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
                prompt_builder.user(combined_content)
        else:
            # Original behavior for non-conversation-state inputs
            if inputs:
                for key, value in inputs.items():
                    if value and key != "conversation":
                        # Format the external input with its source
                        prompt_builder.external(key, str(value))

            # Add prompt to conversation separately only if not conversation state
            if prompt:
                prompt_builder.user(prompt)

        # Build messages list
        messages = []
        
        # Handle system prompt if available
        if person.llm_config and person.llm_config.system_prompt:
            # For now, we keep using dictionary format for LLM compatibility
            messages.append(
                {"role": "system", "content": person.llm_config.system_prompt}
            )
        
        # Get messages from conversation service
        # Note: The conversation service may still return dictionaries for backward compatibility
        conversation_messages = conversation_service.get_messages(person_id)
        
        # Convert messages, mapping 'external' to 'system' for LLM compatibility
        for msg in conversation_messages:
            if isinstance(msg, dict):
                # Handle dictionary format (backward compatibility)
                if msg.get("role") == "external":
                    # Convert external messages to system messages for LLM
                    messages.append({"role": "system", "content": msg["content"]})
                else:
                    messages.append(msg)
            else:
                # Handle Message object format
                # Convert Message to dictionary for LLM API
                if msg.from_person_id == "system":
                    role = "system"
                elif msg.from_person_id == PersonID(person_id):
                    role = "assistant"
                else:
                    role = "user"
                messages.append({"role": role, "content": msg.content})

        # Call LLM
        result: ChatResult = await llm_service.complete(
            messages=messages,
            model=person.llm_config.model if person.llm_config else "gpt-4.1-nano",
            api_key_id=person.llm_config.api_key_id if person.llm_config else None,
        )

        # Store response
        prompt_builder.assistant(result.text)

        return {
            "text": result.text,
            "tokens": result.token_usage.total
            if result.token_usage and result.token_usage.total
            else 0,
        }

    def _find_person(
        self, diagram: DomainDiagram | None, person_id: str
    ) -> DomainPerson | None:
        if not diagram:
            return None
        return next((p for p in diagram.persons if p.id == person_id), None)
