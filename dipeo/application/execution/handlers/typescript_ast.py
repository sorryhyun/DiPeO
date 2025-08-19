import json
from typing import TYPE_CHECKING, Optional, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.diagram_generated.generated_nodes import TypescriptAstNode, NodeType
from dipeo.domain.execution.envelope import Envelope, get_envelope_factory
from dipeo.diagram_generated.models.typescript_ast_model import TypescriptAstNodeData

if TYPE_CHECKING:
    from dipeo.domain.execution.execution_context import ExecutionContext


@register_handler
class TypescriptAstNodeHandler(TypedNodeHandler[TypescriptAstNode]):
    """Handler for TypeScript AST parsing node.
    
    Uses Template Method Pattern for cleaner code:
    - validate() for compile-time checks
    - pre_execute() for runtime setup
    - run() for core parsing logic
    - serialize_output() for custom envelope creation
    """
    
    
    def __init__(self):
        """Initialize the handler.
        
        The TypeScript parser service will be injected via the service registry
        during execution, following the DI pattern.
        """
        super().__init__()
        # Instance variables for passing data between methods
        self._current_debug = None
    
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
        """Validate the TypeScript AST parser configuration - static checks only."""
        import logging
        logger = logging.getLogger(__name__)
        node = request.node
        logger.info(f"[TypescriptAstNode {node.id}] Validating node")
        
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
    
    async def pre_execute(self, request: ExecutionRequest[TypescriptAstNode]) -> Optional[Envelope]:
        """Runtime validation and setup."""
        # Set debug flag for later use
        self._current_debug = False  # Will be set based on context if needed
        
        # Check parser service availability
        # Use the string key name, not the ServiceKey object
        parser_service = request.get_service("ast_parser")
        if not parser_service:
            factory = get_envelope_factory()
            return factory.error(
                "TypeScript parser service not available. Ensure AST_PARSER is registered in the service registry.",
                error_type="RuntimeError",
                produced_by=str(request.node.id)
            )
        
        return None
    
    async def run(
        self,
        inputs: dict[str, Any],
        request: ExecutionRequest[TypescriptAstNode]
    ) -> Any:
        import logging
        logger = logging.getLogger(__name__)
        """Execute TypeScript AST parsing."""
        node = request.node

        # Use the string key name, not the ServiceKey object
        parser_service = request.get_service("ast_parser")

        # Check if batch mode is enabled
        batch_mode = getattr(node, 'batch', False)

        if batch_mode:
            # Batch mode: parse multiple sources at once
            batch_input_key = getattr(node, 'batchInputKey', 'sources')
            
            # Get sources from node config or inputs
            sources = getattr(node, 'sources', None)
            if not sources:
                # Try direct access first
                sources = inputs.get(batch_input_key, {})
            
            # If not found, check if inputs has a 'default' key with the sources
            if not sources and 'default' in inputs:
                default_input = inputs['default']
                if isinstance(default_input, dict):
                    # Check if the default input has the batch_input_key
                    if batch_input_key in default_input:
                        sources = default_input[batch_input_key]
                    # Or if the default input IS the sources dict directly
                    elif all(isinstance(k, str) and k.endswith('.ts') for k in default_input.keys()):
                        sources = default_input
            
            # Also check if inputs itself looks like a sources dict (all keys are file paths)
            if not sources and isinstance(inputs, dict) and inputs:
                # Check if this looks like a sources dictionary (keys are file paths)
                if all(isinstance(k, str) and (k.endswith('.ts') or '/' in k) for k in inputs.keys() if k != 'default'):
                    # Exclude 'default' key and use the rest as sources
                    sources = {k: v for k, v in inputs.items() if k != 'default'}
            
            if not sources or not isinstance(sources, dict):
                raise ValueError(f"Batch mode enabled but no sources dictionary provided at key '{batch_input_key}'")

            # Parse all sources in batch
            try:
                results = await parser_service.parse_batch(
                    sources=sources,
                    extract_patterns=node.extractPatterns or ['interface', 'type', 'enum'],
                    options={
                        'includeJSDoc': node.includeJSDoc or False,
                        'parseMode': node.parseMode or 'module'
                    }
                )
            except Exception as parser_error:
                import traceback
                logger.error(f"[TypescriptAstNode {node.id}] Batch parse error: {traceback.format_exc()}")
                raise
            
            # Return results with metadata for serialize_output
            return {
                'results': results,
                'batch_mode': True,
                'total_sources': len(sources)
            }
        
        else:
            # Single mode: parse one source
            source = node.source
            if not source:
                source = inputs.get('source', '')
            if not source and 'default' in inputs and isinstance(inputs['default'], dict):
                source = inputs['default'].get('source', '')
            

            if not source:
                raise ValueError("No TypeScript source code provided")
            
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
                logger.error(f"[TypescriptAstNode {node.id}] Parse error: {parser_error}")
                logger.error(f"[TypescriptAstNode {node.id}] Traceback: {traceback.format_exc()}")
                raise

            # Extract AST data from the result
            ast_data = result.get('ast', {})
            metadata = result.get('metadata', {})

            # Return processed result with metadata
            return {
                'ast': ast_data,
                'metadata': metadata,
                'batch_mode': False
            }
    
    def serialize_output(
        self,
        result: Any,
        request: ExecutionRequest[TypescriptAstNode]
    ) -> Envelope:
        """Custom serialization for TypeScript AST results."""
        import logging
        logger = logging.getLogger(__name__)
        node = request.node
        trace_id = request.execution_id or ""
        factory = get_envelope_factory()

        # Handle batch mode results
        if isinstance(result, dict) and result.get('batch_mode'):
            return factory.json(
                result['results'],
                produced_by=node.id,
                trace_id=trace_id
            ).with_meta(
                batch_mode=True,
                total_sources=result['total_sources'],
                successful=len(result['results'])
            )
        
        # Handle single mode results
        if isinstance(result, dict) and 'ast' in result:
            # Determine what to include in the output
            include_raw_ast = getattr(node, 'includeRawAST', False)
            
            # Build output based on extraction results
            extracted_definitions = result['ast'].get('extracted', {})
            
            # Prepare output
            output = {}
            if include_raw_ast:
                output['rawAST'] = result['ast'].get('raw', {})
            
            output['extracted'] = extracted_definitions
            output['metadata'] = result['metadata']
            
            # Add processing summary
            summary = {
                'totalExtracted': result['metadata'].get('extractedCount', 0),
                'byType': result['metadata'].get('byType', {})
            }
            output['summary'] = summary
            
            return factory.json(
                output,
                produced_by=node.id,
                trace_id=trace_id
            ).with_meta(
                extracted_count=result['metadata'].get('extractedCount', 0),
                parse_mode=node.parseMode or 'module',
                include_jsdoc=node.includeJSDoc or False
            )
        
        # Fall back to base class serialization
        return super().serialize_output(result, request)