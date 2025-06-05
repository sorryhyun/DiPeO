"""Service for handling diagram execution with WebSocket support."""
import logging
from typing import Dict, Any, AsyncIterator, Optional, Set, Callable, TYPE_CHECKING

from ..utils.base_service import BaseService
from ..exceptions import ValidationError

if TYPE_CHECKING:
    pass


logger = logging.getLogger(__name__)


class ExecutionService(BaseService):
    """Service for handling diagram execution with WebSocket support."""
    
    def __init__(
        self,
        llm_service,
        api_key_service,
        memory_service,
        file_service,
        diagram_service,
        notion_service=None
    ):
        super().__init__()
        self.llm_service = llm_service
        self.api_key_service = api_key_service
        self.memory_service = memory_service
        self.file_service = file_service
        self.diagram_service = diagram_service
        self.notion_service = notion_service
        
    async def validate_diagram_for_execution(self, diagram: Dict[str, Any]) -> None:
        """Validate diagram structure for execution."""
        if not isinstance(diagram, dict):
            raise ValidationError("Diagram must be a dictionary")
            
        nodes = diagram.get("nodes", [])
        if not nodes:
            raise ValidationError("Diagram must contain at least one node")
            
        # Check for start nodes
        start_nodes = [
            node for node in nodes 
            if node.get("type", "") == "start" or 
               node.get("data", {}).get("type", "") == "start"
        ]
        if not start_nodes:
            raise ValidationError("Diagram must contain at least one start node")
            
    def prepare_execution_options(
        self, 
        options: Dict[str, Any], 
        execution_id: str,
        interactive_handler: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Prepare execution options with defaults."""
        execution_options = {
            "continue_on_error": options.get("continueOnError", False),
            "allow_partial": options.get("allowPartial", False),
            "debug_mode": options.get("debugMode", False),
            "execution_id": execution_id,
            **options
        }
        
        if interactive_handler:
            execution_options["interactive_handler"] = interactive_handler
            
        return execution_options
        
    async def pre_initialize_models(self, diagram: Dict[str, Any]) -> Set[str]:
        """Pre-initialize LLM models for faster execution."""
        pre_initialized = set()
        persons = diagram.get("persons", [])
        
        for person in persons:
            model = person.get("model", "")
            service = person.get("service", "")
            api_key_id = person.get("apiKeyId", "")
            
            if model and service and api_key_id:
                config_key = f"{service}:{model}:{api_key_id}"
                if config_key not in pre_initialized:
                    try:
                        self.llm_service.pre_initialize_model(
                            service=service,
                            model=model,
                            api_key_id=api_key_id
                        )
                        pre_initialized.add(config_key)
                    except Exception as e:
                        logger.warning(f"Failed to pre-initialize {config_key}: {e}")
                        
        return pre_initialized
        
    def enhance_diagram_with_api_keys(self, diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Add API keys to diagram for execution."""
        api_keys_list = self.api_key_service.list_api_keys()
        api_keys_dict = {}
        
        for key_info in api_keys_list:
            full_key_data = self.api_key_service.get_api_key(key_info["id"])
            api_keys_dict[key_info["id"]] = full_key_data["key"]
            
        return {
            **diagram,
            "api_keys": api_keys_dict
        }
        
    async def execute_diagram(
        self,
        diagram: Dict[str, Any],
        options: Dict[str, Any],
        execution_id: str,
        interactive_handler: Optional[Callable] = None,
        state_manager: Optional[Any] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Execute a diagram and yield updates.
        
        Args:
            diagram: The diagram to execute
            options: Execution options
            execution_id: Unique execution identifier
            interactive_handler: Optional handler for interactive prompts
            state_manager: Optional WebSocket state manager for pause/resume control
            
        Yields:
            Dict containing execution updates
            
        Raises:
            ValidationError: If diagram structure is invalid
            DiagramExecutionError: If execution fails
        """
        # Validate diagram
        await self.validate_diagram_for_execution(diagram)
        
        # Pre-initialize models
        await self.pre_initialize_models(diagram)
        
        # Enhance diagram with API keys
        enhanced_diagram = self.enhance_diagram_with_api_keys(diagram)
        
        # Prepare execution options
        execution_options = self.prepare_execution_options(
            options, execution_id, interactive_handler
        )
        
        # Import here to avoid circular dependency
        from ..engine.engine import UnifiedExecutionEngine
        
        # Create execution engine
        execution_engine = UnifiedExecutionEngine(
            llm_service=self.llm_service,
            file_service=self.file_service,
            memory_service=self.memory_service,
            notion_service=self.notion_service,
            state_manager=state_manager
        )
        
        # Execute and yield updates
        async for update in execution_engine.execute_diagram(
            enhanced_diagram, 
            execution_options
        ):
            update["execution_id"] = execution_id
            yield update