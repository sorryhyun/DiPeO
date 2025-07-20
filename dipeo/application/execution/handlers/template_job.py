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
        
        # If template_path is provided, validate it exists
        if node.template_path:
            template_path = Path(node.template_path)
            if not template_path.is_absolute():
                base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                template_path = Path(base_dir) / node.template_path
            
            if not template_path.exists():
                return f"Template file not found: {node.template_path}"
            
            if not template_path.is_file():
                return f"Template path is not a file: {node.template_path}"
        
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
            # Get template content
            if node.template_content:
                template_content = node.template_content
            else:
                # Load from file
                template_path = Path(node.template_path)
                if not template_path.is_absolute():
                    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                    template_path = Path(base_dir) / node.template_path
                
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
            
            # Prepare template variables
            template_vars = {}
            
            # Add node-defined variables
            if node.variables:
                template_vars.update(node.variables)
            
            # Add inputs from connected nodes
            if inputs:
                for key, value in inputs.items():
                    # Try to parse JSON strings
                    if isinstance(value, str) and value.strip() and value.strip()[0] in '{[':
                        try:
                            parsed_value = json.loads(value)
                            template_vars[key] = parsed_value
                            # If it's a dict and this is the only/default input, also flatten it to top level
                            if isinstance(parsed_value, dict) and (key == 'default' or len(inputs) == 1):
                                template_vars.update(parsed_value)
                        except json.JSONDecodeError:
                            template_vars[key] = value
                    else:
                        template_vars[key] = value
                        # If it's a dict, flatten it to top level for easier access
                        if isinstance(value, dict):
                            # For labeled inputs like 'spec_data' or single/default inputs
                            if key in ['default', 'spec_data'] or len(inputs) == 1:
                                template_vars.update(value)
                                print(f"[TemplateJobNode] Flattened dict from key '{key}' to template_vars")
            
            # Choose template engine
            engine = node.engine or "internal"
            
            if engine == "internal":
                # Use built-in TemplateProcessor
                # Debug: log template vars for first 100 chars of template
                if request.metadata.get("debug") or "{{nodeType}}" in template_content[:100]:
                    print(f"[TemplateJobNode] Template engine: {engine}")
                    print(f"[TemplateJobNode] Template vars keys: {list(template_vars.keys())}")
                    for key in ['default', 'spec_data']:
                        if key in template_vars:
                            print(f"[TemplateJobNode] '{key}' type: {type(template_vars[key]).__name__}")
                            if isinstance(template_vars[key], dict):
                                print(f"[TemplateJobNode] '{key}' keys: {list(template_vars[key].keys())}")
                            elif isinstance(template_vars[key], str) and len(template_vars[key]) < 200:
                                print(f"[TemplateJobNode] '{key}' value: {template_vars[key][:100]}...")
                    if 'nodeType' in template_vars:
                        print(f"[TemplateJobNode] 'nodeType' value: {template_vars['nodeType']}")
                
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
            helpers = {
                'json': lambda this, value: json.dumps(value),
                'pascalCase': lambda this, value: ''.join(word.capitalize() for word in value.split('_')),
                'camelCase': lambda this, value: value[0].lower() + ''.join(word.capitalize() for word in value.split('_'))[1:],
                'upperCase': lambda this, value: value.upper(),
                'lowerCase': lambda this, value: value.lower(),
                'eq': lambda this, a, b: a == b,
                'ne': lambda this, a, b: a != b,
                'gt': lambda this, a, b: a > b,
                'lt': lambda this, a, b: a < b,
                'gte': lambda this, a, b: a >= b,
                'lte': lambda this, a, b: a <= b,
            }
            
            return compiled(variables, helpers=helpers)
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