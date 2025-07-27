from typing import TYPE_CHECKING, Optional, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.diagram_generated.generated_nodes import TypescriptAstNode, NodeType
from dipeo.core.execution.node_output import DataOutput, ErrorOutput, NodeOutputProtocol
from dipeo.core.ports.ast_parser_port import ASTParserPort
from dipeo.diagram_generated.models.typescript_ast_model import TypescriptAstNodeData

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


@register_handler
class TypescriptAstNodeHandler(TypedNodeHandler[TypescriptAstNode]):
    """Handler for TypeScript AST parsing node."""
    
    def __init__(self, typescript_parser=None):
        """Initialize with TypeScript parser.
        
        Args:
            typescript_parser: The TypeScript AST parser implementation
        """
        self._parser = typescript_parser
    
    @property
    def node_class(self) -> type[TypescriptAstNode]:
        return TypescriptAstNode
    
    @property
    def node_type(self) -> str:
        return NodeType.TYPESCRIPT_AST.value
    
    @property
    def schema(self) -> type[BaseModel]:
        return TypescriptAstNodeData
    
    @property
    def requires_services(self) -> list[str]:
        return ["typescript_parser"]
    
    @property
    def description(self) -> str:
        return "Parses TypeScript source code and extracts AST, interfaces, types, and enums"
    
    def validate(self, request: ExecutionRequest[TypescriptAstNode]) -> Optional[str]:
        """Validate the TypeScript AST parser configuration."""
        node = request.node
        
        # Only validate static configuration, not input data
        # Input validation will happen during execute_request
        
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
            # Also check in 'default' key as DiPeO may pass data there

            source = node.source
            if not source:
                source = inputs.get('source', '')
            if not source and 'default' in inputs and isinstance(inputs['default'], dict):
                source = inputs['default'].get('source', '')
            
            # Debug: print what we found
            if not source:
                return ErrorOutput(
                    value="No TypeScript source code provided",
                    node_id=node.id,
                    error_type="ValidationError"
                )
            
            # Check if parser is available
            if not self._parser:
                return ErrorOutput(
                    value="TypeScript parser service not available",
                    node_id=node.id,
                    error_type="ServiceError"
                )
            
            # Parse the TypeScript code using the injected parser
            try:
                result = await self._parser.parse(
                    source=source,
                    extract_patterns=node.extractPatterns or ['interface', 'type', 'enum'],
                    options={
                        'includeJSDoc': node.includeJSDoc or False,
                        'parseMode': node.parseMode or 'module'
                    }
                )
            except Exception as parser_error:
                print(f"[TypeScript AST] Parser error: {str(parser_error)}")
                raise
            

            # Extract AST data from the result
            ast_data = result.get('ast', {})
            metadata = result.get('metadata', {})


            output_data = {
                'ast': metadata.get('astSummary', {}),
                'interfaces': ast_data.get('interfaces', []),
                'types': ast_data.get('types', []),
                'enums': ast_data.get('enums', []),
                'classes': ast_data.get('classes', []),
                'functions': ast_data.get('functions', []),
                'constants': ast_data.get('constants', [])
            }

            # Return successful result with all extracted data
            return DataOutput(
                value=output_data,
                node_id=node.id,
                metadata={
                    'interfaces_count': len(ast_data.get('interfaces', [])),
                    'types_count': len(ast_data.get('types', [])),
                    'enums_count': len(ast_data.get('enums', [])),
                    'classes_count': len(ast_data.get('classes', [])),
                    'functions_count': len(ast_data.get('functions', [])),
                    'constants_count': len(ast_data.get('constants', [])),
                    'success': True
                }
            )
        
        except Exception as e:
            return ErrorOutput(
                value=f"TypeScript parsing failed: {str(e)}",
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
            
            if success and isinstance(output, DataOutput):
                stats = []
                for key in ['interfaces', 'types', 'enums', 'classes', 'functions']:
                    count = output.metadata.get(f"{key}_count", 0)
                    if count > 0:
                        stats.append(f"{count} {key}")
                
                if stats:
                    print(f"[TypescriptAstNode] Extracted: {', '.join(stats)}")
        
        return output