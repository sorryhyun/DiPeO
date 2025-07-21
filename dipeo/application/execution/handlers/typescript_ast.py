import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.core.static.generated_nodes import TypescriptAstNode
from dipeo.core.execution.node_output import DataOutput, ErrorOutput, NodeOutputProtocol
from dipeo.models import TypescriptAstNodeData, NodeType

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


@register_handler
class TypescriptAstNodeHandler(TypedNodeHandler[TypescriptAstNode]):
    """Handler for TypeScript AST parsing node."""
    
    @property
    def node_class(self) -> type[TypescriptAstNode]:
        return TypescriptAstNode
    
    @property
    def node_type(self) -> str:
        return NodeType.typescript_ast.value
    
    @property
    def schema(self) -> type[BaseModel]:
        return TypescriptAstNodeData
    
    @property
    def requires_services(self) -> list[str]:
        return []
    
    @property
    def description(self) -> str:
        return "Parses TypeScript source code and extracts AST, interfaces, types, and enums"
    
    def validate(self, request: ExecutionRequest[TypescriptAstNode]) -> Optional[str]:
        """Validate the TypeScript AST parser configuration."""
        node = request.node
        
        # Must have source code to parse
        if not node.source and not request.inputs.get('source'):
            return "TypeScript source code must be provided either in node configuration or via input connection"
        
        # Validate extract patterns
        if node.extractPatterns:
            valid_patterns = {'interface', 'type', 'enum', 'class', 'function', 'const', 'export'}
            invalid = set(node.extractPatterns) - valid_patterns
            if invalid:
                return f"Invalid extract patterns: {', '.join(invalid)}. Valid patterns are: {', '.join(valid_patterns)}"
        
        # Validate parse mode
        if node.parseMode and node.parseMode not in ['module', 'script']:
            return f"Invalid parse mode: {node.parseMode}. Must be 'module' or 'script'"
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[TypescriptAstNode]) -> NodeOutputProtocol:
        """Execute the TypeScript AST parsing."""
        node = request.node
        inputs = request.inputs
        
        # Store execution metadata
        request.add_metadata("extract_patterns", node.extractPatterns or ['interface', 'type', 'enum'])
        request.add_metadata("include_jsdoc", node.includeJSDoc or False)
        request.add_metadata("parse_mode", node.parseMode or 'module')
        
        try:
            # Get source code from node config or inputs
            source = node.source or inputs.get('source', '')
            
            if not source:
                return ErrorOutput(
                    value="No TypeScript source code provided",
                    node_id=node.id,
                    error_type="ValidationError"
                )
            
            # Import the parser module
            parser_path = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd())) / 'files' / 'code' / 'codegen'
            sys.path.insert(0, str(parser_path))
            
            try:
                from typescript_parser import parse_typescript
                
                # Parse the TypeScript code
                result = parse_typescript({
                    'source': source,
                    'extractPatterns': node.extractPatterns or ['interface', 'type', 'enum'],
                    'includeJSDoc': node.includeJSDoc or False,
                    'parseMode': node.parseMode or 'module'
                })
                
                # Check for errors
                if result.get('error'):
                    return ErrorOutput(
                        value=f"TypeScript parsing failed: {result['error']}",
                        node_id=node.id,
                        error_type="ParseError"
                    )
                
                # Return successful result with all extracted data
                return DataOutput(
                    value={
                        'ast': result['ast'],
                        'interfaces': result['interfaces'],
                        'types': result['types'],
                        'enums': result['enums'],
                        'classes': result.get('classes', []),
                        'functions': result.get('functions', [])
                    },
                    node_id=node.id,
                    metadata={
                        'interfaces_count': len(result['interfaces']),
                        'types_count': len(result['types']),
                        'enums_count': len(result['enums']),
                        'classes_count': len(result.get('classes', [])),
                        'functions_count': len(result.get('functions', [])),
                        'success': True
                    }
                )
                
            finally:
                # Clean up sys.path
                if str(parser_path) in sys.path:
                    sys.path.remove(str(parser_path))
        
        except ImportError as e:
            return ErrorOutput(
                value=f"Failed to import TypeScript parser: {str(e)}",
                node_id=node.id,
                error_type="ImportError",
                metadata={"parser_path": str(parser_path)}
            )
        
        except Exception as e:
            return ErrorOutput(
                value=f"Unexpected error during TypeScript parsing: {str(e)}",
                node_id=node.id,
                error_type=type(e).__name__
            )
    
    def post_execute(
        self,
        request: ExecutionRequest[TypescriptAstNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        """Post-execution hook to log parsing statistics."""
        # Log execution details if in debug mode
        if request.metadata.get("debug"):
            success = output.metadata.get("success", False)
            print(f"[TypescriptAstNode] TypeScript parsing - Success: {success}")
            
            if success and isinstance(output, DataOutput):
                stats = []
                for key in ['interfaces', 'types', 'enums', 'classes', 'functions']:
                    count = output.metadata.get(f"{key}_count", 0)
                    if count > 0:
                        stats.append(f"{count} {key}")
                
                if stats:
                    print(f"[TypescriptAstNode] Extracted: {', '.join(stats)}")
        
        return output