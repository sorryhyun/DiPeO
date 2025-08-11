import json
from typing import TYPE_CHECKING, Optional, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.diagram_generated.generated_nodes import TypescriptAstNode, NodeType
from dipeo.core.execution.node_output import DataOutput, ErrorOutput, NodeOutputProtocol
from dipeo.diagram_generated.models.typescript_ast_model import TypescriptAstNodeData

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext


@register_handler
class TypescriptAstNodeHandler(TypedNodeHandler[TypescriptAstNode]):
    """Handler for TypeScript AST parsing node."""
    
    def __init__(self):
        """Initialize the handler.
        
        The TypeScript parser service will be injected via the service registry
        during execution, following the DI pattern.
        """
        pass
    
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
        return ["ast_parser"]  # Uses the AST_PARSER service key
    
    @property
    def description(self) -> str:
        return "Parses TypeScript source code and extracts AST, interfaces, types, and enums"
    
    def validate(self, request: ExecutionRequest[TypescriptAstNode]) -> Optional[str]:
        """Validate the TypeScript AST parser configuration."""
        node = request.node
        
        # Only validate static configuration, not input data
        # Input validation will happen during execute_request
        # Add debug logging
        import logging
        logger = logging.getLogger(__name__)

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

        
        try:
            # Get source code from node config or inputs
            # Also check in 'default' key as DiPeO may pass data there
            # Add debug logging
            import logging
            logger = logging.getLogger(__name__)

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
            
            # Get TypeScript parser from services using DI pattern
            parser_service = request.get_service("ast_parser")
            if not parser_service:
                return ErrorOutput(
                    value="TypeScript parser service not available. Ensure AST_PARSER is registered in the service registry.",
                    node_id=node.id,
                    error_type="ServiceError"
                )
            
            # Parse the TypeScript code using the parser service
            try:
                result = await parser_service.parse(
                    source=source,
                    extract_patterns=node.extractPatterns or ['interface', 'type', 'enum'],
                    options={
                        'includeJSDoc': node.includeJSDoc or False,
                        'parseMode': node.parseMode or 'module'
                    }
                )
            except Exception as parser_error:
                import traceback
                logger.error(f"[TypescriptAstNode {node.id}] Traceback: {traceback.format_exc()}")
                raise
            

            # Extract AST data from the result
            ast_data = result.get('ast', {})
            metadata = result.get('metadata', {})


            # Apply transformations based on node configuration
            transform_enums = getattr(node, 'transformEnums', False)
            flatten_output = getattr(node, 'flattenOutput', False)
            output_format = getattr(node, 'outputFormat', 'standard')
            
            # Transform enums if requested
            enums = ast_data.get('enums', [])
            if transform_enums and enums:
                enums = self._transform_enums(enums)
            
            # Build output data based on format
            if output_format == 'for_codegen':
                # Optimized format for code generation
                output_data = {
                    'interfaces': ast_data.get('interfaces', []),
                    'types': ast_data.get('types', []),
                    'enums': enums,
                    'consts': ast_data.get('constants', []),
                    'total_definitions': (
                        len(ast_data.get('interfaces', [])) +
                        len(ast_data.get('types', [])) +
                        len(enums) +
                        len(ast_data.get('constants', []))
                    )
                }
            elif output_format == 'for_analysis':
                # Detailed format for analysis
                output_data = {
                    'ast': ast_data,
                    'metadata': metadata,
                    'summary': {
                        'interfaces': len(ast_data.get('interfaces', [])),
                        'types': len(ast_data.get('types', [])),
                        'enums': len(enums),
                        'classes': len(ast_data.get('classes', [])),
                        'functions': len(ast_data.get('functions', [])),
                        'constants': len(ast_data.get('constants', []))
                    }
                }
            else:
                # Standard format (default)
                output_data = {
                    'ast': metadata.get('astSummary', {}),
                    'interfaces': ast_data.get('interfaces', []),
                    'types': ast_data.get('types', []),
                    'enums': enums,
                    'classes': ast_data.get('classes', []),
                    'functions': ast_data.get('functions', []),
                    'constants': ast_data.get('constants', [])
                }
            
            # Flatten output if requested
            if flatten_output and output_format == 'standard':
                output_data = self._flatten_output(output_data)

            # Return successful result with all extracted data
            return DataOutput(
                value=output_data,
                node_id=node.id,
                metadata=json.dumps({
                    'output_format': output_format
                })
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
        if request.metadata.get("debug") and isinstance(output, DataOutput):
            # Extract counts from the actual output data if available
            if isinstance(output.value, dict):
                stats = []
                # Check various output formats for counts
                if 'summary' in output.value:
                    # for_analysis format
                    summary = output.value['summary']
                    for key in ['interfaces', 'types', 'enums', 'classes', 'functions', 'constants']:
                        count = summary.get(key, 0)
                        if count > 0:
                            stats.append(f"{count} {key}")
                else:
                    # standard or for_codegen format - count items directly
                    for key in ['interfaces', 'types', 'enums', 'classes', 'functions', 'constants']:
                        if key in output.value and isinstance(output.value[key], list):
                            count = len(output.value[key])
                            if count > 0:
                                stats.append(f"{count} {key}")
                
                if stats:
                    print(f"[TypescriptAstNode] Extracted: {', '.join(stats)}")
        
        return output
    
    def _transform_enums(self, enums: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Transform enum definitions to a simpler format.
        
        Converts enum member references from 'EnumName.MEMBER' to 'member' format.
        """
        transformed_enums = []
        
        for enum in enums:
            transformed = enum.copy()
            
            # Transform members if they exist
            if 'members' in transformed and isinstance(transformed['members'], list):
                transformed_members = []
                for member in transformed['members']:
                    if isinstance(member, dict):
                        # Transform member value if it's an enum reference
                        if 'value' in member and isinstance(member['value'], str):
                            value = member['value']
                            # Handle "EnumName.MEMBER" -> "member"
                            if '.' in value:
                                value = value.split('.')[-1]
                            # Handle "UPPER_CASE" -> "upper_case"
                            if value.isupper() and '_' in value:
                                value = value.lower()
                            member = member.copy()
                            member['value'] = value
                    transformed_members.append(member)
                transformed['members'] = transformed_members
            
            transformed_enums.append(transformed)
        
        return transformed_enums
    
    def _flatten_output(self, output_data: dict[str, Any]) -> dict[str, Any]:
        """Flatten the output structure for easier consumption.
        
        Merges all definition types into a single 'definitions' array.
        """
        flattened = {
            'definitions': [],
            'ast': output_data.get('ast', {})
        }
        
        # Add all definition types to the definitions array
        for def_type in ['interfaces', 'types', 'enums', 'classes', 'functions', 'constants']:
            if def_type in output_data and isinstance(output_data[def_type], list):
                for item in output_data[def_type]:
                    if isinstance(item, dict):
                        # Add the definition type to each item
                        item_with_type = item.copy()
                        item_with_type['definition_type'] = def_type.rstrip('s')  # Remove plural 's'
                        flattened['definitions'].append(item_with_type)
        
        return flattened