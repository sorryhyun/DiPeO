
import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution import UnifiedExecutionContext
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.types import TypedNodeHandler
from dipeo.core.dynamic import Person
from dipeo.core.static.generated_nodes import PersonJobNode
from dipeo.models import (
    MemorySettings,
    Message,
    NodeOutput,
    NodeType,
    PersonID,
    PersonJobNodeData,
)

if TYPE_CHECKING:
    from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution

logger = logging.getLogger(__name__)


@register_handler
class PersonJobNodeHandler(TypedNodeHandler[PersonJobNode]):
    
    def __init__(self):
        # Person cache managed at handler level
        self._person_cache: dict[str, Person] = {}


    @property
    def node_class(self) -> type[PersonJobNode]:
        return PersonJobNode
    
    @property
    def node_type(self) -> str:
        return NodeType.person_job.value

    @property
    def schema(self) -> type[BaseModel]:
        return PersonJobNodeData


    @property
    def requires_services(self) -> list[str]:
        return [
            "llm_service", 
            "diagram", 
            "conversation_manager",
            "prompt_builder",
        ]

    @property
    def description(self) -> str:
        return "Execute person job with conversation memory"
    
    def _resolve_service(self, context: UnifiedExecutionContext, services: dict[str, Any], service_name: str) -> Any | None:
        return context.get_service(service_name) or services.get(service_name)

    async def pre_execute(
        self,
        node: PersonJobNode,
        execution: "TypedStatefulExecution"
    ) -> dict[str, Any]:
        """Pre-execute logic for PersonJobNode."""
        exec_count = execution.get_node_execution_count(node.id)
        
        # Determine which prompt to use
        # exec_count is 1 on first run because it's incremented before execution
        if exec_count == 1 and node.first_only_prompt:
            prompt = node.first_only_prompt
        else:
            prompt = node.default_prompt
        
        return {
            "prompt": prompt,
            "exec_count": exec_count,
            "should_continue": exec_count < node.max_iteration,
            "tools": node.tools
        }
    
    async def execute(
        self,
        node: PersonJobNode,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        # Direct typed access to person_id
        person_id = node.person_id
        logger.debug(f"Raw inputs for person {person_id}: {inputs}")
        # Resolve services
        llm_service = self._resolve_service(context, services, "llm_service")
        diagram = self._resolve_service(context, services, "diagram")
        conversation_manager = self._resolve_service(context, services, "conversation_manager")
        prompt_builder = self._resolve_service(context, services, "prompt_builder")
        # Get execution count for iteration check
        execution_count = context.get_node_execution_count(context.current_node_id)
        
        # Check if max_iteration is reached
        if execution_count > node.max_iteration:
            return NodeOutput(
                value={"default": ""},
                metadata={"skipped": True, "reason": f"Max iteration ({node.max_iteration}) reached"},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )
        
        # Only log in debug mode if explicitly enabled

        # Basic validation using typed property
        if not person_id:
            return NodeOutput(
                value={"default": ""}, 
                metadata={"error": "No person specified"},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )
        
        try:
            # Get or create person
            person = self._get_or_create_person(person_id, conversation_manager)
            
            # Apply memory settings if configured and not the first execution
            if execution_count > 0 and node.memory_settings:
                person.apply_memory_settings(node.memory_settings)
            
            # Use inputs directly
            transformed_inputs = inputs
            
            # Handle conversation inputs
            if self._has_conversation_input(transformed_inputs):
                self._rebuild_conversation(person, transformed_inputs)
            
            # Build prompt BEFORE applying memory management
            template_values = prompt_builder.prepare_template_values(
                transformed_inputs, 
                conversation_manager=conversation_manager,
                person_id=person_id
            )
            built_prompt = prompt_builder.build(
                prompt=node.default_prompt if node.default_prompt is not None else node.first_only_prompt,
                first_only_prompt=node.first_only_prompt,
                execution_count=execution_count,
                template_values=template_values,
            )

            # Skip if no prompt
            if not built_prompt:
                logger.warning(f"Skipping execution for person {person_id} - no prompt available")
                return NodeOutput(
                    value={"default": ""},
                    metadata={"skipped": True, "reason": "No prompt available"},
                    node_id=context.current_node_id,
                    executed_nodes=context.executed_nodes
                )
            
            # Execute LLM call
            # Only pass tools if they are configured
            complete_kwargs = {
                "prompt": built_prompt,
                "llm_service": llm_service,
                "from_person_id": "system",
                "temperature": 0.7,
                "max_tokens": 4096,
            }
            
            # Add tools only if they exist
            if node.tools:
                complete_kwargs["tools"] = node.tools
                
            result = await person.complete(**complete_kwargs)
            
            # Build and return output
            return self._build_node_output(
                result=result,
                person=person,
                context=context,
                diagram=diagram,
                model=person.llm_config.model
            )
            
        except ValueError as e:
            # Domain validation errors - only log if debug enabled
            if logger.isEnabledFor(logging.DEBUG):
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
    
    # _execute_with_props removed - logic integrated into execute method
    
    def _get_or_create_person(
        self,
        person_id: str,
        conversation_manager: Any
    ) -> Person:
        # Check cache first
        if person_id in self._person_cache:
            return self._person_cache[person_id]
        
        # Get person config from conversation manager
        person_config = None
        person_name = person_id  # Default to person_id as name
        
        if hasattr(conversation_manager, 'get_person_config'):
            person_config = conversation_manager.get_person_config(person_id)
        
        
        if not person_config:
            # Fallback: create minimal config with default LLM
            from dipeo.models import ApiKeyID, LLMService, PersonLLMConfig
            person_config = PersonLLMConfig(
                service=LLMService.openai,
                model="gpt-4.1-nano",
                api_key_id=ApiKeyID("")  # Wrap empty string with ApiKeyID
            )
        
        # Create Person object without conversation_manager to avoid circular reference
        person = Person(
            id=PersonID(person_id),
            name=person_name,
            llm_config=person_config,
            conversation_manager=None  # Initially None to avoid recursion
        )
        
        # Cache the person BEFORE setting conversation_manager
        self._person_cache[person_id] = person
        
        # Now safely set the conversation_manager after caching
        person._conversation_manager = conversation_manager
        
        return person
    
    def _has_conversation_input(self, inputs: dict[str, Any]) -> bool:
        for value in inputs.values():
            if isinstance(value, dict) and "messages" in value:
                return True
        return False
    
    def _rebuild_conversation(self, person: Person, inputs: dict[str, Any]) -> None:
        all_messages = []
        for value in inputs.values():
            if isinstance(value, dict) and "messages" in value:
                messages = value["messages"]
                if isinstance(messages, list):
                    all_messages.extend(messages)
        
        if not all_messages:
            return
        
        for msg_dict in all_messages:
            message = Message(
                from_person_id=msg_dict.get("from_person_id", person.id),
                to_person_id=msg_dict.get("to_person_id", person.id),
                content=msg_dict.get("content", ""),
                message_type="person_to_person",
                timestamp=msg_dict.get("timestamp"),
            )
            person.add_message(message)
    
    def _needs_conversation_output(self, node_id: str, diagram: Any) -> bool:
        # Check if any edge from this node expects conversation output
        for edge in diagram.edges:
            if str(edge.source_node_id) == node_id:
                # Check for explicit conversation output
                if edge.source_output == "conversation":
                    return True
                # Check data_transform for content_type = conversation_state
                if hasattr(edge, 'data_transform') and edge.data_transform:
                    if edge.data_transform.get('content_type') == 'conversation_state':
                        return True
        logger.debug(f"[CONVERSATION_OUTPUT] Node {node_id} does not need conversation output")
        return False
    
    def _build_node_output(self, result: Any, person: Person, context: UnifiedExecutionContext, diagram: Any, model: str) -> NodeOutput:
        output_value = {"default": result.text}
        
        # Add conversation if needed
        if self._needs_conversation_output(context.current_node_id, diagram):
            output_value["conversation"] = []
            for msg in person.get_messages():
                output_value["conversation"].append({
                    "role": "assistant" if msg.from_person_id == person.id else "user",
                    "content": msg.content,
                    "person_id": str(person.id),
                    "person_label": person.name,
                })

        # Build metadata - token usage is now handled by UnifiedExecutionContext
        metadata = {"model": model}
        
        return NodeOutput(
            value=output_value, 
            metadata=metadata,
            node_id=context.current_node_id,
            executed_nodes=context.executed_nodes
        )
    
