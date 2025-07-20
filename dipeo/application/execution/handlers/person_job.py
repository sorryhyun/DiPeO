
import logging
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.unified_service_registry import (
    LLM_SERVICE,
    DIAGRAM,
    CONVERSATION_MANAGER,
    PERSON_MANAGER,
    PROMPT_BUILDER,
    TOOL_CONFIG_SERVICE,
    OUTPUT_BUILDER
)
from dipeo.application.utils import ConversationProcessor
from dipeo.core.dynamic import Person
from dipeo.core.static.generated_nodes import PersonJobNode
from dipeo.core.execution.node_output import ConversationOutput, TextOutput, NodeOutputProtocol, ErrorOutput
from dipeo.models import (
    NodeType,
    PersonID,
    PersonJobNodeData,
)

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


@register_handler
class PersonJobNodeHandler(TypedNodeHandler[PersonJobNode]):
    
    def __init__(self, tool_config_service=None, output_builder=None):
        self._tool_config_service = tool_config_service
        self._output_builder = output_builder


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
            "person_manager",
            "prompt_builder",
            "tool_config_service",
            "output_builder",
        ]

    @property
    def description(self) -> str:
        return "Execute person job with conversation memory"
    
    def validate(self, request: ExecutionRequest[PersonJobNode]) -> Optional[str]:
        """Validate the execution request."""
        if not request.node.person_id:
            return "No person specified"
        
        # Check max iteration
        execution_count = request.context.get_node_execution_count(request.node_id)
        if execution_count > request.node.max_iteration:
            return f"Max iteration ({request.node.max_iteration}) reached"
            
        return None
    
    async def execute_request(self, request: ExecutionRequest[PersonJobNode]) -> NodeOutputProtocol:
        """Execute the person job with the unified request object."""
        # Get node and context from request
        node = request.node
        context = request.context
        
        # Get inputs from request (already resolved by engine)
        inputs = request.inputs or {}
        
        # Direct typed access to person_id
        person_id = node.person_id

        # Get services from services dict
        llm_service = request.services.get(LLM_SERVICE.name)
        diagram = request.services.get(DIAGRAM.name)
        conversation_manager = request.services.get(CONVERSATION_MANAGER.name)
        person_manager = request.services.get(PERSON_MANAGER.name)
        prompt_builder = request.services.get(PROMPT_BUILDER.name)
        
        # Get or use injected services
        tool_config_service = self._tool_config_service or request.services.get(TOOL_CONFIG_SERVICE.name)
        output_builder = self._output_builder or request.services.get(OUTPUT_BUILDER.name)

        execution_count = context.get_node_execution_count(node.id)

        try:
            # Get or create person through PersonManager
            try:
                person = person_manager.get_person(PersonID(person_id))
            except KeyError:
                # Person doesn't exist - create through PersonManager
                person_config = self._get_person_config(node, conversation_manager)
                if not person_config:
                    return ErrorOutput(
                        value=f"No LLM configuration found for person '{person_id}'",
                        node_id=node.id,
                        error_type="ConfigurationError"
                    )
                person = person_manager.create_person(
                    person_id=PersonID(person_id),
                    name=person_id,
                    llm_config=person_config
                )
                # Set conversation manager after creation
                person._conversation_manager = conversation_manager
            
            # Apply memory settings if configured
            if node.memory_settings:
                person.apply_memory_settings(node.memory_settings)
            
            # Use inputs directly
            transformed_inputs = inputs
            
            # Handle conversation inputs
            has_conversation_input = ConversationProcessor.has_conversation_input(transformed_inputs)
            if has_conversation_input:
                ConversationProcessor.rebuild_conversation(person, transformed_inputs)

            # Build prompt BEFORE applying memory management
            template_values = prompt_builder.prepare_template_values(
                transformed_inputs, 
                conversation_manager=conversation_manager,
                person_id=person_id
            )

            # Disable auto-prepend if we have conversation input (to avoid duplication)
            built_prompt = prompt_builder.build(
                prompt=node.default_prompt,
                first_only_prompt=node.first_only_prompt,
                execution_count=execution_count,
                template_values=template_values,
                auto_prepend_conversation=not has_conversation_input
            )

            # Skip if no prompt
            if not built_prompt:
                logger.warning(f"Skipping execution for person {person_id} - no prompt available")
                return TextOutput(
                    value="",
                    node_id=node.id,
                    metadata={"skipped": True, "reason": "No prompt available"}
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
                # Convert tools to proper format using service
                tool_configs = tool_config_service.convert_tools(node.tools)
                
                if tool_configs:
                    complete_kwargs["tools"] = tool_configs
                
            result = await person.complete(**complete_kwargs)
            
            # Build and return output
            return output_builder.build_node_output(
                result=result,
                person=person,
                node=node,
                diagram=diagram,
                model=person.llm_config.model
            )
            
        except Exception as e:
            # Let on_error handle it
            raise
    
    async def on_error(
        self,
        request: ExecutionRequest[PersonJobNode],
        error: Exception
    ) -> Optional[NodeOutputProtocol]:
        """Handle errors gracefully."""
        # For ValueError (domain validation), only log in debug mode
        if isinstance(error, ValueError):
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Validation error in person job: {error}")
            return ErrorOutput(
                value=str(error),
                node_id=request.node.id,
                error_type="ValidationError"
            )
        
        # For other errors, log them
        logger.error(f"Error executing person job: {error}")
        return ErrorOutput(
            value=str(error),
            node_id=request.node.id,
            error_type=type(error).__name__
        )
    
    def _get_person_config(self, node: PersonJobNode, conversation_manager: Any) -> Optional["PersonLLMConfig"]:
        """Get person configuration from conversation manager."""
        if hasattr(conversation_manager, 'get_person_config'):
            return conversation_manager.get_person_config(node.person_id)
        return None
    
    
    
