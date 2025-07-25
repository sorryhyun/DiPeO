import os
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.core.static.generated_nodes import TemplateJobNode
from dipeo.core.execution.node_output import TextOutput, ErrorOutput, NodeOutputProtocol
from dipeo.models import TemplateJobNodeData, NodeType
from dipeo.application.utils.template import TemplateProcessor

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


@register_handler
class TemplateJobNodeHandler(TypedNodeHandler[TemplateJobNode]):
    
    def __init__(self):
        self._processor = TemplateProcessor()
    
    @property
    def node_class(self) -> type[TemplateJobNode]:
        return TemplateJobNode
    
    @property
    def node_type(self) -> str:
        return NodeType.template_job.value
    
    @property
    def schema(self) -> type[BaseModel]:
        return TemplateJobNodeData
    
    @property
    def requires_services(self) -> list[str]:
        return []
    
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
    
    async def execute_request(self, request: ExecutionRequest[TemplateJobNode]) -> NodeOutputProtocol:
        """Execute the template rendering."""
        node = request.node
        inputs = request.inputs
        
        
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
                template_vars.update(inputs)
            
            # Get template content
            if node.template_content:
                template_content = node.template_content
            else:
                # Process template_path through template processor to handle variables
                processed_template_path = self._processor.process_simple(node.template_path, template_vars)
                
                # Load from file
                template_path = Path(processed_template_path)
                if not template_path.is_absolute():
                    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                    template_path = Path(base_dir) / processed_template_path
                
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
            
            # Choose template engine
            engine = node.engine or "internal"
            
            try:
                if engine == "internal":
                    # Use built-in TemplateProcessor
                    rendered = self._processor.process_simple(template_content, template_vars)
                elif engine == "jinja2":
                    # Use Jinja2
                    rendered = await self._render_jinja2(template_content, template_vars)
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
                # Process output_path through template processor to handle variables
                processed_output_path = self._processor.process_simple(node.output_path, template_vars)
                
                output_path = Path(processed_output_path)
                if not output_path.is_absolute():
                    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                    output_path = Path(base_dir) / processed_output_path
                
                # Create parent directories if needed
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(rendered)
                
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