import contextlib
import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.registry.keys import AST_PARSER
from dipeo.diagram_generated.unified_nodes.typescript_ast_node import NodeType, TypescriptAstNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    pass


@register_handler
@requires_services(ast_parser=AST_PARSER)
class TypescriptAstNodeHandler(TypedNodeHandler[TypescriptAstNode]):
    """Handler for TypeScript AST parsing node.

    Uses Template Method Pattern for cleaner code:
    - validate() for compile-time checks
    - pre_execute() for runtime setup
    - run() for core parsing logic
    - serialize_output() for custom envelope creation
    """

    NODE_TYPE = NodeType.TYPESCRIPT_AST

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
        return TypescriptAstNode

    @property
    def description(self) -> str:
        return "Parses TypeScript source code and extracts AST, interfaces, types, and enums"

    def validate(self, request: ExecutionRequest[TypescriptAstNode]) -> str | None:
        """Validate the TypeScript AST parser configuration - static checks only."""
        import logging

        logger = logging.getLogger(__name__)
        node = request.node
        logger.info(f"[TypescriptAstNode {node.id}] Validating node")

        # Validate extract patterns
        if node.extract_patterns:
            valid_patterns = {"interface", "type", "enum", "class", "function", "const", "export"}
            invalid = set(node.extract_patterns) - valid_patterns
            if invalid:
                return f"Invalid extract patterns: {', '.join(invalid)}. Valid patterns are: {', '.join(valid_patterns)}"

        # Validate parse mode
        if node.parse_mode and node.parse_mode not in ["module", "script"]:
            return f"Invalid parse mode: {node.parse_mode}. Must be 'module' or 'script'"

        return None

    async def pre_execute(self, request: ExecutionRequest[TypescriptAstNode]) -> Envelope | None:
        """Runtime validation and setup."""
        import logging

        logger = logging.getLogger(__name__)

        # Set debug flag for later use
        self._current_debug = False  # Will be set based on context if needed

        # Check parser service availability
        ast_parser = request.get_optional_service(AST_PARSER)
        return None

    async def run(
        self, inputs: dict[str, Any], request: ExecutionRequest[TypescriptAstNode]
    ) -> Any:
        import logging

        logger = logging.getLogger(__name__)
        """Execute TypeScript AST parsing."""
        node = request.node

        # Check if parsing should be skipped (cache already exists)
        # Check both at root level and in default dict
        skip_parsing = inputs.get("_skip_parsing", False)
        if not skip_parsing and "default" in inputs and isinstance(inputs["default"], dict):
            skip_parsing = inputs["default"].get("_skip_parsing", False)

        if skip_parsing:
            logger.info(f"[TypescriptAstNode {node.id}] Skipping parsing - cache already exists")
            # Return empty results to indicate no parsing was done
            return {"results": {}, "batch_mode": True, "total_sources": 0, "skipped": True}

        # Get the parser service
        parser_service = self._ast_parser

        # Check if batch mode is enabled
        batch_mode = getattr(node, "batch", False)

        if batch_mode:
            # Batch mode: parse multiple sources at once
            batch_input_key = getattr(node, "batchInputKey", "sources")

            # Get sources from node config or inputs
            sources = getattr(node, "sources", None)
            if not sources:
                # Try direct access first
                sources = inputs.get(batch_input_key)

            # If not found, check if inputs has a 'default' key with the sources
            if not sources and "default" in inputs:
                default_input = inputs["default"]
                if isinstance(default_input, dict):
                    # Check if the default input has the batch_input_key
                    if batch_input_key in default_input:
                        sources = default_input[batch_input_key]
                    # Or if the default input IS the sources dict directly (all keys look like file paths)
                    elif default_input and all(
                        isinstance(k, str) and (k.endswith(".ts") or "/" in k)
                        for k in list(default_input.keys())[:10]
                    ):
                        sources = default_input

            # Also check if inputs itself looks like a sources dict (all keys are file paths)
            if not sources and isinstance(inputs, dict) and inputs:
                # Check if this looks like a sources dictionary (keys are file paths)
                non_default_keys = [k for k in inputs if k != "default"]
                if non_default_keys and all(
                    isinstance(k, str) and (k.endswith(".ts") or "/" in k)
                    for k in non_default_keys[:10]
                ):
                    # Exclude 'default' key and use the rest as sources
                    sources = {k: v for k, v in inputs.items() if k != "default"}

            if not sources or not isinstance(sources, dict):
                logger.error(
                    f"[TypescriptAstNode {node.id}] Failed to find sources - sources type: {type(sources).__name__ if sources else 'None'}"
                )
                logger.error(
                    f"[TypescriptAstNode {node.id}] Full inputs structure: {json.dumps({k: type(v).__name__ for k, v in inputs.items()}, indent=2)}"
                )
                raise ValueError(
                    f"Batch mode enabled but no sources dictionary provided at key '{batch_input_key}'"
                )

            # Filter out dummy sources that indicate cache skip
            sources = {k: v for k, v in sources.items() if k != "_dummy"}

            if not sources:
                logger.info(
                    f"[TypescriptAstNode {node.id}] No real sources after filtering dummy entries - cache must exist"
                )
                return {"results": {}, "batch_mode": True, "total_sources": 0, "skipped": True}

            # Parse all sources in batch
            try:
                results = await self._ast_parser.parse_batch(
                    sources=sources,
                    extract_patterns=node.extract_patterns or ["interface", "type", "enum"],
                    options={
                        "includeJSDoc": node.include_js_doc or False,
                        "parseMode": node.parse_mode or "module",
                    },
                )
            except Exception:
                import traceback

                logger.error(
                    f"[TypescriptAstNode {node.id}] Batch parse error: {traceback.format_exc()}"
                )
                raise

            # Return results with metadata for serialize_output
            return {"results": results, "batch_mode": True, "total_sources": len(sources)}

        else:
            # Single mode: parse one source
            source = node.source
            if not source:
                source = inputs.get("source", "")
            if not source and "default" in inputs and isinstance(inputs["default"], dict):
                source = inputs["default"].get("source", "")

            if not source:
                raise ValueError("No TypeScript source code provided")

            # Parse the TypeScript code using the parser service
            try:
                result = await self._ast_parser.parse(
                    source=source,
                    extract_patterns=node.extract_patterns or ["interface", "type", "enum"],
                    options={
                        "includeJSDoc": node.include_js_doc or False,
                        "parseMode": node.parse_mode or "module",
                    },
                )
            except Exception as parser_error:
                import traceback

                logger.error(f"[TypescriptAstNode {node.id}] Parse error: {parser_error}")
                logger.error(f"[TypescriptAstNode {node.id}] Traceback: {traceback.format_exc()}")
                raise

            # Extract AST data from the result
            ast_data = result.get("ast", {})
            metadata = result.get("metadata", {})

            # Return processed result with metadata
            return {"ast": ast_data, "metadata": metadata, "batch_mode": False}

    def serialize_output(
        self, result: Any, request: ExecutionRequest[TypescriptAstNode]
    ) -> Envelope:
        """Custom serialization for TypeScript AST results."""
        import logging

        logger = logging.getLogger(__name__)
        node = request.node
        trace_id = request.execution_id or ""

        # Handle skipped parsing (cache already exists)
        if isinstance(result, dict) and result.get("skipped"):
            return EnvelopeFactory.create({}, produced_by=node.id, trace_id=trace_id).with_meta(
                batch_mode=True, skipped=True, reason="Cache already exists"
            )

        # Handle batch mode results
        if isinstance(result, dict) and result.get("batch_mode"):
            return EnvelopeFactory.create(
                result["results"], produced_by=node.id, trace_id=trace_id
            ).with_meta(
                batch_mode=True,
                total_sources=result["total_sources"],
                successful=len(result["results"]),
            )

        # Handle single mode results
        if isinstance(result, dict) and "ast" in result:
            # Determine what to include in the output
            include_raw_ast = getattr(node, "includeRawAST", False)

            # Build output based on extraction results
            extracted_definitions = result["ast"].get("extracted", {})

            # Prepare output
            output = {}
            if include_raw_ast:
                output["rawAST"] = result["ast"].get("raw", {})

            output["extracted"] = extracted_definitions
            output["metadata"] = result["metadata"]

            # Add processing summary
            summary = {
                "totalExtracted": result["metadata"].get("extractedCount", 0),
                "byType": result["metadata"].get("byType", {}),
            }
            output["summary"] = summary

            return EnvelopeFactory.create(output, produced_by=node.id, trace_id=trace_id).with_meta(
                extracted_count=result["metadata"].get("extractedCount", 0),
                parse_mode=node.parse_mode or "module",
                include_jsdoc=node.include_js_doc or False,
            )

        # Fall back to base class serialization
        return super().serialize_output(result, request)

    async def prepare_inputs(
        self, request: ExecutionRequest[TypescriptAstNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Prepare inputs with token consumption.

        Phase 5: Now consumes tokens from incoming edges when available.
        """
        # Phase 5: Consume tokens from incoming edges or fall back to regular inputs
        envelope_inputs = self.get_effective_inputs(request, inputs)

        # Call parent prepare_inputs for default envelope conversion
        return await super().prepare_inputs(request, envelope_inputs)

    def post_execute(
        self, request: ExecutionRequest[TypescriptAstNode], output: Envelope
    ) -> Envelope:
        """Post-execution hook to emit tokens.

        Phase 5: Now emits output as tokens to trigger downstream nodes.
        """
        # Phase 5: Emit output as tokens to trigger downstream nodes
        self.emit_token_outputs(request, output)

        return output
