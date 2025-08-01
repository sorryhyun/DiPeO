import os
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Any

from pydantic import BaseModel
from dipeo.domain.ports.storage import FileSystemPort

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.diagram_generated.generated_nodes import TemplateJobNode, NodeType
from dipeo.core.execution.node_output import TextOutput, ErrorOutput, NodeOutputProtocol
from dipeo.diagram_generated.models.template_job_model import TemplateJobNodeData
from dipeo.infrastructure.services.template.template_integration import get_enhanced_template_service
from dipeo.application.utils.template import TemplateProcessor

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


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
        return "Renders templates using Handlebars-style syntax and outputs the result"
    
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

        # Store execution metadata
        request.add_metadata("engine", node.engine or "internal")
        if node.template_path:
            request.add_metadata("template_path", node.template_path)
        if node.output_path:
            request.add_metadata("output_path", node.output_path)
        
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
                    # Debug logging for transparency
                    # print(f"[DEBUG] Unwrapped 'default' input containing keys: {list(inputs['default'].keys())}")
                else:
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
            
            # Choose template engine
            engine = node.engine or "internal"

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
                        request.add_metadata("enhanced_rendering", True)
                    except Exception as e:
                        # Fall back to standard Jinja2
                        rendered = await self._render_jinja2(template_content, template_vars)
                        request.add_metadata("enhancement_fallback", str(e))
                elif engine == "handlebars":
                    # Use Python handlebars implementation
                    rendered = await self._render_handlebars(template_content, template_vars)
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
                    metadata={"engine": engine}
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
                
                request.add_metadata("output_written", str(output_path))
            
            return TextOutput(
                value=rendered,
                node_id=node.id,
                metadata={
                    "engine": engine,
                    "output_path": node.output_path,
                    "success": True
                }
            )
        
        except Exception as e:
            return ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type=type(e).__name__,
                metadata={"engine": node.engine or "internal"}
            )
    
    async def _render_jinja2(self, template: str, variables: dict[str, Any]) -> str:
        """Render template using Jinja2."""
        try:
            from jinja2 import Template, StrictUndefined
            
            # Create Jinja2 template with strict undefined to catch missing variables
            jinja_template = Template(template, undefined=StrictUndefined)
            return jinja_template.render(**variables)
        except ImportError:
            raise ImportError("Jinja2 is not installed. Install it with: pip install jinja2")
    
    async def _render_handlebars(self, template: str, variables: dict[str, Any]) -> str:
        """Render template using Python handlebars implementation."""
        try:
            from pybars import Compiler
            
            # Compile the template
            compiler = Compiler()
            compiled = compiler.compile(template)
            
            # Add helper functions that might be useful
            def ts_type(this, type_name):
                """Convert field type to TypeScript type."""
                type_map = {
                    'string': 'string',
                    'number': 'number',
                    'boolean': 'boolean',
                    'array': 'any[]',
                    'object': 'Record<string, any>',
                    'date': 'Date',
                    'datetime': 'Date',
                }
                return type_map.get(type_name, 'any')
            
            def humanize(this, value):
                """Convert snake_case or camelCase to human readable text."""
                if isinstance(value, str):
                    # Replace underscores with spaces and capitalize words
                    result = value.replace('_', ' ')
                    # Handle camelCase
                    import re
                    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', result)
                    # Capitalize first letter of each word
                    return ' '.join(word.capitalize() for word in result.split())
                return str(value)
            
            def safe_json(this, value):
                """Serialize value to JSON for use in TypeScript/JavaScript code."""
                if value is None:
                    return 'null'
                elif isinstance(value, bool):
                    return 'true' if value else 'false'
                elif isinstance(value, str):
                    # For string values in TypeScript, use single quotes
                    return f"'{value}'"
                elif isinstance(value, (list, dict)):
                    # For objects and arrays, use JSON serialization without indentation
                    return json.dumps(value, separators=(', ', ': '))
                else:
                    return json.dumps(value)
            
            helpers = {
                'json': lambda this, value: json.dumps(value),
                'safeJson': safe_json,
                'pascalCase': lambda this, value: ''.join(word.capitalize() for word in str(value).split('_')) if value is not None else '',
                'camelCase': lambda this, value: str(value)[0].lower() + ''.join(word.capitalize() for word in str(value).split('_'))[1:] if value else '',
                'upperCase': lambda this, value: str(value).upper() if value is not None else '',
                'lowerCase': lambda this, value: str(value).lower() if value is not None else '',
                'eq': lambda this, a, b: a == b,
                'ne': lambda this, a, b: a != b,
                'gt': lambda this, a, b: a > b if a is not None and b is not None else False,
                'lt': lambda this, a, b: a < b if a is not None and b is not None else False,
                'gte': lambda this, a, b: a >= b if a is not None and b is not None else False,
                'lte': lambda this, a, b: a <= b if a is not None and b is not None else False,
                'tsType': ts_type,
                'humanize': humanize,
            }
            
            # Ensure spec_data fields are available at top level for templates
            if 'spec_data' in variables and isinstance(variables['spec_data'], dict):
                # Make spec_data fields available at top level for easier access
                for key, value in variables['spec_data'].items():
                    if key not in variables:  # Don't override existing top-level keys
                        variables[key] = value
            
            try:
                result = compiled(variables, helpers=helpers)
                return result
            except Exception as e:
                raise
        except ImportError:
            raise ImportError("PyBars3 is not installed. Install it with: pip install pybars3")
    
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