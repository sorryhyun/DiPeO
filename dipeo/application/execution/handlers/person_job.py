
import logging
from typing import Any, Optional

from dipeo.application import register_handler
from dipeo.application.execution.typed_handler_base import TypedNodeHandler
from dipeo.application.execution.context.unified_execution_context import UnifiedExecutionContext
from dipeo.models import (
    NodeOutput,
    PersonJobNodeData,
    ForgettingMode,
    Message,
    PersonID,
    MemoryConfig,
    NodeType,
)
from dipeo.core.static.generated_nodes import PersonJobNode
from dipeo.core.dynamic import Person
from pydantic import BaseModel

logger = logging.getLogger(__name__)


@register_handler
class PersonJobNodeHandler(TypedNodeHandler[PersonJobNode]):
    
    def __init__(self, person_job_execution_service=None, llm_service=None, diagram_storage_service=None, conversation_service=None):
        self.person_job_execution_service = person_job_execution_service
        self.llm_service = llm_service
        self.diagram_storage_service = diagram_storage_service
        self.conversation_service = conversation_service
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
        # Note: person_job_orchestrator removed - functionality integrated into handler
        return [
            "llm_service", 
            "diagram", 
            "conversation_service",
            "conversation_manager",
            "prompt_builder",
            "conversation_state_manager", 
            "memory_transformer"
        ]

    @property
    def description(self) -> str:
        return "Execute person job with conversation memory"
    
    def _resolve_service(self, context: UnifiedExecutionContext, services: dict[str, Any], service_name: str) -> Optional[Any]:
        service = context.get_service(service_name)
        if not service:
            service = services.get(service_name)

        # If it's a dependency_injector provider, call it to get the instance
        from dependency_injector import providers
        if isinstance(service, (providers.Factory, providers.Singleton, providers.Dependency)):
            service = service()
            
        return service

    async def execute_typed(
        self,
        node: PersonJobNode,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        # Direct typed access to person_id
        person_id = node.person_id
        # Resolve services
        llm_service = self._resolve_service(context, services, "llm_service")
        diagram = self._resolve_service(context, services, "diagram")
        conversation_service = self._resolve_service(context, services, "conversation_service")
        conversation_manager = self._resolve_service(context, services, "conversation_manager")
        prompt_builder = self._resolve_service(context, services, "prompt_builder")
        conversation_state_manager = self._resolve_service(context, services, "conversation_state_manager")
        memory_transformer = self._resolve_service(context, services, "memory_transformer")
        
        # Get current node ID and execution info
        node_id = self._extract_node_id(context)
        execution_count = self._extract_execution_count(context)
        execution_id = getattr(context.execution_state, 'id', None) if hasattr(context, 'execution_state') else None
        
        # Only log in debug mode if explicitly enabled

        # Basic validation using typed property
        if not person_id:
            return self._build_output(
                {"default": ""}, 
                context,
                {"error": "No person specified"}
            )
        
        try:
            # Get or create person
            person = self._get_or_create_person(person_id, diagram, conversation_manager)
            
            # Direct typed access to memory_config
            forget_mode = ForgettingMode.no_forget
            if node.memory_config:
                # Direct property access - no dict lookups!
                forget_mode = node.memory_config.forget_mode
            
            # Apply memory transformation
            transformed_inputs = inputs
            if memory_transformer:
                from dipeo.utils.arrow import unwrap_inputs
                transformed_inputs = memory_transformer.transform_input(
                    inputs, "person_job", execution_count, 
                    {"forget_mode": forget_mode.value}
                )
            else:
                from dipeo.utils.arrow import unwrap_inputs
                transformed_inputs = unwrap_inputs(inputs)
            
            # Handle conversation inputs
            if self._has_conversation_input(transformed_inputs):
                self._rebuild_conversation(person, transformed_inputs, forget_mode)
            
            # Apply memory management with typed access
            if conversation_manager and execution_count > 0 and conversation_state_manager.should_forget_messages(execution_count, forget_mode):
                if node.memory_config:
                    # Direct typed access to max_messages
                    mem_config = MemoryConfig(
                        forget_mode=forget_mode,
                        max_messages=node.memory_config.max_messages
                    )
                    person.apply_memory_management(mem_config)
                else:
                    conversation_manager.apply_forgetting(
                        person_id, forget_mode, execution_id, execution_count
                    )
            
            # Build prompt
            template_values = prompt_builder.prepare_template_values(transformed_inputs)
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
            chat_kwargs = {
                "message": built_prompt,
                "llm_service": llm_service,
                "from_person_id": "system",
                "memory_config": None,
                "temperature": 0.7,
                "max_tokens": 4096,
            }
            
            # Add tools only if they exist
            if node.tools:
                chat_kwargs["tools"] = node.tools
                
            result = await person.chat(**chat_kwargs)
            
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
                logger.debug(f"Validation error in person job: {e}")
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
        diagram: Any,
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
            # Try to get from conversation service if available
            conversation_service = self.conversation_service
            if conversation_service and hasattr(conversation_service, 'get_person_config'):
                person_config = conversation_service.get_person_config(person_id)
        
        if not person_config:
            # Fallback: create minimal config with default LLM
            from dipeo.models import PersonLLMConfig, LLMService, ApiKeyID
            person_config = PersonLLMConfig(
                service=LLMService.openai,
                model="gpt-4.1-nano",
                api_key_id=ApiKeyID("")  # Wrap empty string with ApiKeyID
            )
        
        # Create Person object
        person = Person(
            id=PersonID(person_id),
            name=person_name,
            llm_config=person_config,
            conversation_manager=conversation_manager
        )
        
        # Cache the person
        self._person_cache[person_id] = person
        return person
    
    def _has_conversation_input(self, inputs: dict[str, Any]) -> bool:
        for value in inputs.values():
            if isinstance(value, dict) and "messages" in value:
                return True
        return False
    
    def _rebuild_conversation(self, person: Person, inputs: dict[str, Any], forget_mode: ForgettingMode) -> None:
        all_messages = []
        for value in inputs.values():
            if isinstance(value, dict) and "messages" in value:
                messages = value["messages"]
                if isinstance(messages, list):
                    all_messages.extend(messages)
        
        if not all_messages:
            return
        
        if forget_mode == ForgettingMode.on_every_turn:
            person.clear_conversation()
        
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
            if edge.source == node_id and edge.source_output == "conversation":
                return True
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
                    "person_id": person.id,
                    "person_label": person.name,
                })
        
        # Build metadata
        metadata = {"model": model}
        if result.token_usage:
            if isinstance(result.token_usage, dict):
                metadata["tokens_used"] = result.token_usage.get("total", 0)
                metadata["token_usage"] = result.token_usage
            else:
                metadata["tokens_used"] = getattr(result.token_usage, "total", 0)
                metadata["token_usage"] = {
                    "input": getattr(result.token_usage, "input", 0),
                    "output": getattr(result.token_usage, "output", 0),
                    "cached": getattr(result.token_usage, "cached", 0)
                }
        
        return NodeOutput(
            value=output_value, 
            metadata=metadata,
            node_id=context.current_node_id,
            executed_nodes=context.executed_nodes
        )
    
    def _extract_node_id(self, context: UnifiedExecutionContext) -> str:
        return context.current_node_id
    
    def _extract_execution_count(self, context: UnifiedExecutionContext) -> int:
        return context.get_node_execution_count(context.current_node_id)
    
    def _transform_result_to_output(self, result: Any, context: UnifiedExecutionContext) -> NodeOutput:
        output_value = {"default": result.content}
        
        # Add conversation if present
        if result.conversation_state:
            # conversation_state is now a dictionary with 'messages' key
            messages = result.conversation_state.get("messages", [])
            output_value["conversation"] = []
            
            for msg in messages:
                if isinstance(msg, dict):
                    # Handle dictionary format (backward compatibility)
                    output_value["conversation"].append({
                        "role": msg.get("role"),
                        "content": msg.get("content"),
                        "tool_calls": msg.get("tool_calls"),
                        "tool_call_id": msg.get("tool_call_id"),
                        "person_label": result.metadata.get("person") if result.metadata else None,
                    })
                elif isinstance(msg, Message):
                    # Handle Message object format
                    # Convert Message to dictionary format for output
                    role = "system" if msg.from_person_id == "system" else "user"
                    if msg.message_type == "person_to_system":
                        role = "assistant"
                    
                    output_value["conversation"].append({
                        "role": role,
                        "content": msg.content,
                        "tool_calls": msg.metadata.get("tool_calls") if msg.metadata else None,
                        "tool_call_id": msg.metadata.get("tool_call_id") if msg.metadata else None,
                        "person_label": result.metadata.get("person") if result.metadata else None,
                    })
        
        # Build metadata
        metadata = {}
        if result.usage:
            # Handle both dict and object formats for usage
            if isinstance(result.usage, dict):
                metadata["tokens_used"] = result.usage.get("total", 0)
                metadata["token_usage"] = result.usage
            else:
                # Assume it's a TokenUsage object with attributes
                metadata["tokens_used"] = getattr(result.usage, "total", 0)
                metadata["token_usage"] = {
                    "input": getattr(result.usage, "input", getattr(result.usage, "prompt", 0)),
                    "output": getattr(result.usage, "output", getattr(result.usage, "completion", 0)),
                    "cached": getattr(result.usage, "cached", 0)
                }
            metadata["model"] = result.metadata.get("model") if result.metadata else "gpt-4.1-nano"
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
        
        return NodeOutput(
            value=output_value, 
            metadata=metadata,
            node_id=context.current_node_id,
            executed_nodes=context.executed_nodes
        )