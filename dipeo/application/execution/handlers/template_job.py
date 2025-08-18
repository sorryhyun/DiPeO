import os
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Any
from importlib import import_module

from pydantic import BaseModel
from dipeo.domain.ports.storage import FileSystemPort

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER
from dipeo.diagram_generated.generated_nodes import TemplateJobNode, NodeType
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.models.template_job_model import TemplateJobNodeData
from dipeo.infrastructure.shared.template.drivers.jinja_template.template_integration import get_enhanced_template_service
from dipeo.domain.ports.template import TemplateProcessorPort

if TYPE_CHECKING:
    from dipeo.domain.execution.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


@register_handler
class TemplateJobNodeHandler(TypedNodeHandler[TemplateJobNode]):
    """
    Clean separation of concerns:
    1. validate() - Static/structural validation (compile-time checks)
    2. pre_execute() - Runtime validation and setup
    3. execute_with_envelopes() - Core execution logic with envelope inputs
    
    Now uses envelope-based communication for clean input/output interfaces.
    """
    
    
    def __init__(self, filesystem_adapter: Optional[FileSystemPort] = None, template_processor: Optional[TemplateProcessorPort] = None):
        super().__init__()
        self.filesystem_adapter = filesystem_adapter
        self._template_service = None  # Lazy initialization
        self._template_processor = template_processor
        # Instance variables for passing data between methods
        self._current_filesystem_adapter = None
        self._current_engine = None
        self._current_template_service = None
        self._current_template_processor = None
    
    @property
    def node_class(self) -> type[TemplateJobNode]:
        return TemplateJobNode
    
    @property
    def node_type(self) -> str:
        return NodeType.TEMPLATE_JOB.value
    
    @property
    def schema(self) -> type[BaseModel]:
        return TemplateJobNodeData
    
    @property
    def requires_services(self) -> list[str]:
        return ["filesystem_adapter"]
    
    @property
    def description(self) -> str:
        return "Renders templates using Jinja2 syntax and outputs the result"
    
    def validate(self, request: ExecutionRequest[TemplateJobNode]) -> Optional[str]:
        """Validate the template job configuration."""
        node = request.node

        # Must have either template_path or template_content
        if not node.template_path and not node.template_content:
            return "Either template_path or template_content must be provided"
        
        return None
    
    async def pre_execute(self, request: ExecutionRequest[TemplateJobNode]) -> Optional[Envelope]:
        """Pre-execution setup: validate template file and processor availability.
        
        Moves template file existence check, processor setup, and service validation
        out of execute_request for cleaner separation of concerns.
        """
        node = request.node
        services = request.services
        
        # Get filesystem adapter from services or use injected one
        filesystem_adapter = self.filesystem_adapter or services.resolve(FILESYSTEM_ADAPTER)
        if not filesystem_adapter:
            return EnvelopeFactory.error(
                "Filesystem adapter is required for template job execution",
                error_type="RuntimeError",
                produced_by=str(node.id)
            )
        
        # Store filesystem adapter in instance variable for execute_request
        self._current_filesystem_adapter = filesystem_adapter
        
        # Validate template engine
        engine = node.engine or "internal"
        if engine not in ["internal", "jinja2"]:
            return EnvelopeFactory.error(
                f"Unsupported template engine: {engine}",
                error_type="ValueError",
                produced_by=str(node.id)
            )
        self._current_engine = engine
        
        # Initialize template service
        try:
            template_service = self._get_template_service()
            self._current_template_service = template_service
        except Exception as e:
            return EnvelopeFactory.error(
                str(e),
                error_type=e.__class__.__name__,
                produced_by=str(node.id)
            )
        
        # Initialize template processor for path interpolation
        # Use injected processor or try to get from services
        from dipeo.application.registry.keys import TEMPLATE_PROCESSOR
        template_processor = self._template_processor
        if not template_processor:
            try:
                template_processor = services.resolve(TEMPLATE_PROCESSOR)
            except:
                # If not available in services, template processing will be skipped
                pass
        self._current_template_processor = template_processor
        
        # No early return - proceed to execute_request
        return None
    
    def _get_template_service(self):
        """Get or create the template service."""
        if self._template_service is None:
            # print("[DEBUG] Creating template service...")
            self._template_service = get_enhanced_template_service()
            # print("[DEBUG] Template service created successfully")
        return self._template_service
    
    def _resolve_dotted_path(self, dotted: str, ctx: dict) -> Any:
        """Resolve a dotted path like 'a.b.c' into the context."""
        current = ctx
        for part in dotted.split('.'):
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                current = current[idx] if idx < len(current) else None
            else:
                current = getattr(current, part, None)
            if current is None:
                break
        return current

    async def prepare_inputs(
        self,
        request: ExecutionRequest[TemplateJobNode],
        inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Prepare template variables from envelopes and node configuration."""
        node = request.node
        template_vars = {}
        
        # Add node-defined variables
        if node.variables:
            template_vars.update(node.variables)

        # Add inputs from connected nodes - convert from envelopes
        if inputs:
            # Process envelope inputs
            for key, envelope in inputs.items():
                try:
                    # Try to parse as JSON first
                    value = envelope.as_json()
                except ValueError:
                    # Fall back to text
                    value = envelope.as_text()
                
                # Check if we have a single 'default' key with dict value
                if key == 'default' and isinstance(value, dict):
                    # Unwrap the default for better template ergonomics
                    template_vars.update(value)
                else:
                    # For labeled connections, add to template_vars
                    template_vars[key] = value
        return template_vars

    async def run(
        self,
        inputs: dict[str, Any],
        request: ExecutionRequest[TemplateJobNode]
    ) -> Any:
        """Execute template rendering with support for foreach and preprocessor."""
        node = request.node
        template_vars = inputs
        
        # Use services from instance variables (set in pre_execute)
        filesystem_adapter = self._current_filesystem_adapter
        engine = self._current_engine
        template_service = self._current_template_service
        template_processor = self._current_template_processor
        
        # Apply preprocessor if configured
        if node.preprocessor:
            preprocessor_config = node.preprocessor if isinstance(node.preprocessor, dict) else {}
            module_name = preprocessor_config.get('module')
            function_name = preprocessor_config.get('function')
            
            if module_name and function_name:
                try:
                    # Import the module and get the function
                    module = import_module(module_name)
                    func = getattr(module, function_name)
                    
                    # Call the preprocessor with context and any additional args
                    preprocessor_args = preprocessor_config.get('args', {})
                    extra_context = func(context=template_vars, **preprocessor_args)
                    
                    # Update template vars with preprocessor results
                    if isinstance(extra_context, dict):
                        template_vars.update(extra_context)
                except Exception as e:
                    logger.warning(f"Preprocessor failed: {e}")
                    # Continue without preprocessor results
        
        # Get template content
        if node.template_content:
            template_content = node.template_content
        else:
            # First process single bracket {} interpolation for diagram variables (if processor available)
            processed_path = node.template_path
            if template_processor:
                processed_path = template_processor.process_single_brace(node.template_path, template_vars)
            
            # Then process Jinja2 {{ }} syntax if present
            processed_template_path = template_service.render_string(processed_path, **template_vars).strip()
            
            # Load from file - just use the path as-is since filesystem adapter handles base path
            template_path = Path(processed_template_path)
            
            if not filesystem_adapter.exists(template_path):
                raise FileNotFoundError(f"Template file not found: {node.template_path}")
            
            with filesystem_adapter.open(template_path, 'rb') as f:
                template_content = f.read().decode('utf-8')
        
        # Helper function to render and write a single file
        def render_to_path(output_path_template: str, local_context: dict) -> str:
            """Render template and write to file specified by path template."""
            # Render the template content
            if engine == "internal":
                rendered = template_service.render_string(template_content, **local_context)
            elif engine == "jinja2":
                try:
                    rendered = template_service.render_string(template_content, **local_context)
                except Exception as e:
                    # Fall back to standard Jinja2
                    rendered = self._render_jinja2_sync(template_content, local_context)
                    logger.debug(f"Enhancement fallback: {e}")
            else:
                rendered = template_content  # Fallback
            
            # Process output path template
            if template_processor:
                output_path_str = template_processor.process_single_brace(output_path_template, local_context)
            else:
                output_path_str = output_path_template
            
            # Render any Jinja2 syntax in the path
            output_path_str = template_service.render_string(output_path_str, **local_context).strip()
            output_path = Path(output_path_str)
            
            # Create parent directories if needed
            parent_dir = output_path.parent
            if parent_dir != Path(".") and not filesystem_adapter.exists(parent_dir):
                filesystem_adapter.mkdir(parent_dir, parents=True)
            
            # Write the file
            with filesystem_adapter.open(output_path, 'wb') as f:
                f.write(rendered.encode('utf-8'))
            
            return str(output_path)
        
        # Handle foreach mode
        if node.foreach:
            foreach_config = node.foreach if isinstance(node.foreach, dict) else {}
            items = foreach_config.get('items', [])
            
            # Resolve items if it's a string (dotted path or expression)
            if isinstance(items, str):
                items = self._resolve_dotted_path(items, template_vars)
            
            # Ensure items is a list
            items = list(items or [])
            
            # Apply limit if specified
            limit = foreach_config.get('limit')
            if limit:
                items = items[:limit]
            
            # Get the variable name for each item (handle both 'as' and 'as_')
            var_name = foreach_config.get('as') or foreach_config.get('as_') or "item"
            
            # Get output path template
            output_path_template = foreach_config.get('output_path', 'output_{index}.txt')
            
            # Render template for each item
            written_files = []
            for idx, item in enumerate(items):
                # Create local context with item
                local_context = {**template_vars, var_name: item, 'index': idx}
                
                # Render and write file
                output_file = render_to_path(output_path_template, local_context)
                written_files.append(output_file)
            
            # Return list of written files
            return {"written": written_files, "count": len(written_files)}
        
        # Single file mode (backward compatible)
        else:
            # Render template
            if engine == "internal":
                rendered = template_service.render_string(template_content, **template_vars)
            elif engine == "jinja2":
                try:
                    rendered = template_service.render_string(template_content, **template_vars)
                except Exception as e:
                    # Fall back to standard Jinja2
                    rendered = await self._render_jinja2(template_content, template_vars)
                    logger.debug(f"Enhancement fallback: {e}")
            else:
                rendered = template_content
            
            # Write to file if output_path is specified
            if node.output_path:
                # First process single bracket {} interpolation for diagram variables (if processor available)
                processed_path = node.output_path
                if template_processor:
                    processed_path = template_processor.process_single_brace(node.output_path, template_vars)
                
                # Then process Jinja2 {{ }} syntax if present
                processed_output_path = template_service.render_string(processed_path, **template_vars).strip()
                
                output_path = Path(processed_output_path)
                
                # Create parent directories if needed
                parent_dir = output_path.parent
                if parent_dir != Path(".") and not filesystem_adapter.exists(parent_dir):
                    filesystem_adapter.mkdir(parent_dir, parents=True)
                
                with filesystem_adapter.open(output_path, 'wb') as f:
                    f.write(rendered.encode('utf-8'))
                
                # Store output path for metadata
                self._current_output_path = output_path
            
            return rendered

    def serialize_output(
        self,
        result: Any,
        request: ExecutionRequest[TemplateJobNode]
    ) -> Envelope:
        """Serialize rendered template to text envelope."""
        node = request.node
        trace_id = request.execution_id or ""
        
        return EnvelopeFactory.text(
            result,
            produced_by=node.id,
            trace_id=trace_id
        ).with_meta(
            engine=self._current_engine,
            template_path=node.template_path,
            output_path=str(self._current_output_path) if hasattr(self, '_current_output_path') and self._current_output_path else None
        )
    
    async def _render_jinja2(self, template: str, variables: dict[str, Any]) -> str:
        """Render template using Jinja2 with custom filters."""
        try:
            from jinja2 import Environment, StrictUndefined
            
            # Create Jinja2 environment with custom filters
            env = Environment(undefined=StrictUndefined)
            
            # Add custom filters from the registry
            from dipeo.infrastructure.shared.template.drivers.jinja_template.filters import create_filter_registry
            registry = create_filter_registry()
            for name, func in registry.get_all_filters().items():
                env.filters[name] = func
            
            # Create and render template
            jinja_template = env.from_string(template)
            return jinja_template.render(**variables)
        except ImportError:
            raise ImportError("Jinja2 is not installed. Install it with: pip install jinja2")
    
    def _render_jinja2_sync(self, template: str, variables: dict[str, Any]) -> str:
        """Synchronous version of Jinja2 rendering for use in nested functions."""
        try:
            from jinja2 import Environment, StrictUndefined
            
            # Create Jinja2 environment with custom filters
            env = Environment(undefined=StrictUndefined)
            
            # Add custom filters from the registry
            from dipeo.infrastructure.shared.template.drivers.jinja_template.filters import create_filter_registry
            registry = create_filter_registry()
            for name, func in registry.get_all_filters().items():
                env.filters[name] = func
            
            # Create and render template
            jinja_template = env.from_string(template)
            return jinja_template.render(**variables)
        except ImportError:
            raise ImportError("Jinja2 is not installed. Install it with: pip install jinja2")
    
    
    def post_execute(
        self,
        request: ExecutionRequest[TemplateJobNode],
        output: Envelope
    ) -> Envelope:
        """Post-execution hook to log template execution details."""
        # Post-execution logging can use instance variables if needed
        # No need for metadata access
        return output