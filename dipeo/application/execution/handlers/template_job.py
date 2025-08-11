import os
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Any

from pydantic import BaseModel
from dipeo.domain.ports.storage import FileSystemPort

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.diagram_generated.generated_nodes import TemplateJobNode, NodeType
from dipeo.core.execution.node_output import TextOutput, ErrorOutput, NodeOutputProtocol, TemplateJobOutput
from dipeo.diagram_generated.models.template_job_model import TemplateJobNodeData
from dipeo.infrastructure.services.jinja_template.template_integration import get_enhanced_template_service
from dipeo.application.utils.template import TemplateProcessor

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


@register_handler
class TemplateJobNodeHandler(TypedNodeHandler[TemplateJobNode]):
    
    def __init__(self, filesystem_adapter: Optional[FileSystemPort] = None):
        self.filesystem_adapter = filesystem_adapter
        self._template_service = None  # Lazy initialization
    
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
    
    def _get_template_service(self):
        """Get or create the template service."""
        if self._template_service is None:
            # print("[DEBUG] Creating template service...")
            self._template_service = get_enhanced_template_service()
            # print("[DEBUG] Template service created successfully")
        return self._template_service
    
    async def execute_request(self, request: ExecutionRequest[TemplateJobNode]) -> NodeOutputProtocol:
        """Execute the template rendering."""
        # print(f"[DEBUG] TemplateJobNode.execute_request started for node {request.node.id}")
        node = request.node
        inputs = request.inputs
        services = request.services

        # Get filesystem adapter from services or use injected one
        filesystem_adapter = self.filesystem_adapter or services.get("filesystem_adapter")
        if not filesystem_adapter:
            return ErrorOutput(
                value="Filesystem adapter is required for template job execution",
                node_id=node.id,
                error_type="ServiceError"
            )

        # Get engine for later use
        engine = node.engine or "internal"
        
        try:
            # Prepare template variables first
            template_vars = {}
            
            # Add node-defined variables
            if node.variables:
                template_vars.update(node.variables)

            # Add inputs from connected nodes
            if inputs:
                
                # Check if we have a single 'default' key with dict value
                if len(inputs) == 1 and 'default' in inputs and isinstance(inputs['default'], dict):
                    # Unwrap the default for better template ergonomics
                    template_vars.update(inputs['default'])
                else:
                    # For labeled connections, merge all inputs into template_vars
                    template_vars.update(inputs)

            # Get template content
            # print(f"[DEBUG] Getting template content...")
            if node.template_content:
                template_content = node.template_content
            else:
                # First process single bracket {} interpolation for diagram variables
                template_processor = TemplateProcessor()
                processed_path = template_processor.process_single_brace(node.template_path, template_vars)
                
                # Then process Jinja2 {{ }} syntax if present
                template_service = self._get_template_service()
                processed_template_path = template_service.render_string(processed_path, **template_vars).strip()
                # print(f"[DEBUG] Processed template_path: {processed_template_path}")
                
                # Load from file - just use the path as-is since filesystem adapter handles base path
                template_path = Path(processed_template_path)
                
                if not filesystem_adapter.exists(template_path):
                    return ErrorOutput(
                        value=f"Template file not found: {node.template_path}",
                        node_id=node.id,
                        error_type="FileNotFoundError"
                    )
                
                with filesystem_adapter.open(template_path, 'rb') as f:
                    template_content = f.read().decode('utf-8')
            
            try:
                if engine == "internal":
                    # Use built-in template service
                    template_service = self._get_template_service()
                    rendered = template_service.render_string(template_content, **template_vars)
                elif engine == "jinja2":
                    # Use enhanced template service for jinja2
                    try:
                        template_service = self._get_template_service()
                        rendered = template_service.render_string(template_content, **template_vars)
                        # print(f"[DEBUG] Jinja2 rendering complete")
                    except Exception as e:
                        # Fall back to standard Jinja2
                        rendered = await self._render_jinja2(template_content, template_vars)
                        # Log the fallback but don't store in metadata
                        logger.debug(f"Enhancement fallback: {e}")
                else:
                    return ErrorOutput(
                        value=f"Unsupported template engine: {engine}",
                        node_id=node.id,
                        error_type="UnsupportedEngineError"
                    )
            except Exception as render_error:
                return ErrorOutput(
                    value=f"Template rendering failed: {str(render_error)}",
                    node_id=node.id,
                    error_type="RenderError",
                    metadata="{}"  # Empty metadata
                )
            
            # Write to file if output_path is specified
            if node.output_path:
                # First process single bracket {} interpolation for diagram variables
                template_processor = TemplateProcessor()
                processed_path = template_processor.process_single_brace(node.output_path, template_vars)
                
                # Then process Jinja2 {{ }} syntax if present
                template_service = self._get_template_service()
                processed_output_path = template_service.render_string(processed_path, **template_vars).strip()
                
                output_path = Path(processed_output_path)
                
                # Create parent directories if needed
                parent_dir = output_path.parent
                if parent_dir != Path(".") and not filesystem_adapter.exists(parent_dir):
                    filesystem_adapter.mkdir(parent_dir, parents=True)
                
                with filesystem_adapter.open(output_path, 'wb') as f:
                    f.write(rendered.encode('utf-8'))
            
            return TemplateJobOutput(
                value=rendered,
                node_id=node.id,
                metadata="{}",  # Empty metadata
                engine=engine,  # Use typed field
                template_path=node.template_path,  # Use typed field
                output_path=str(output_path) if node.output_path else None  # Use typed field
            )
        
        except Exception as e:
            output = ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type=type(e).__name__
            )
            output.metadata = json.dumps({"engine": node.engine or "internal"})
            return output
    
    async def _render_jinja2(self, template: str, variables: dict[str, Any]) -> str:
        """Render template using Jinja2."""
        try:
            from jinja2 import Template, StrictUndefined
            
            # Create Jinja2 template with strict undefined to catch missing variables
            jinja_template = Template(template, undefined=StrictUndefined)
            return jinja_template.render(**variables)
        except ImportError:
            raise ImportError("Jinja2 is not installed. Install it with: pip install jinja2")
    
    
    def post_execute(
        self,
        request: ExecutionRequest[TemplateJobNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        """Post-execution hook to log template execution details."""
        # Log execution details if in debug mode
        if request.metadata.get("debug"):
            engine = request.metadata.get("engine", "internal")
            success = output.metadata.get("success", False)
            print(f"[TemplateJobNode] Rendered template with {engine} - Success: {success}")
            if request.metadata.get("output_written"):
                print(f"[TemplateJobNode] Output written to: {request.metadata['output_written']}")
        
        return output