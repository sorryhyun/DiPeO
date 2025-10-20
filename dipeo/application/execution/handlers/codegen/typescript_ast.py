import json
from typing import Any

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.registry.keys import AST_PARSER
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.unified_nodes.typescript_ast_node import NodeType, TypescriptAstNode
from dipeo.domain.execution.messaging.envelope import Envelope, EnvelopeFactory

logger = get_module_logger(__name__)


@register_handler
@requires_services(ast_parser=AST_PARSER)
class TypescriptAstNodeHandler(TypedNodeHandler[TypescriptAstNode]):
    """Handler for TypeScript AST parsing node."""

    NODE_TYPE = NodeType.TYPESCRIPT_AST

    def __init__(self):
        super().__init__()

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
        node = request.node

        if node.extract_patterns:
            valid_patterns = {"interface", "type", "enum", "class", "function", "const", "export"}
            invalid = set(node.extract_patterns) - valid_patterns
            if invalid:
                return f"Invalid extract patterns: {', '.join(invalid)}. Valid patterns are: {', '.join(valid_patterns)}"

        if node.parse_mode and node.parse_mode not in ["module", "script"]:
            return f"Invalid parse mode: {node.parse_mode}. Must be 'module' or 'script'"

        return None

    async def pre_execute(self, request: ExecutionRequest[TypescriptAstNode]) -> Envelope | None:
        request.set_handler_state("debug", False)
        return None

    async def run(
        self, inputs: dict[str, Any], request: ExecutionRequest[TypescriptAstNode]
    ) -> Any:
        node = request.node

        skip_parsing = inputs.get("_skip_parsing", False)
        if not skip_parsing and "default" in inputs and isinstance(inputs["default"], dict):
            skip_parsing = inputs["default"].get("_skip_parsing", False)

        if skip_parsing:
            logger.info(f"[TypescriptAstNode {node.id}] Skipping parsing - cache already exists")
            return {"results": {}, "batch_mode": True, "total_sources": 0, "skipped": True}

        parser_service = self._ast_parser

        batch_mode = getattr(node, "batch", False)

        if batch_mode:
            batch_input_key = getattr(node, "batchInputKey", "sources")

            sources = getattr(node, "sources", None)
            if not sources:
                sources = inputs.get(batch_input_key)

            if not sources and "default" in inputs:
                default_input = inputs["default"]
                if isinstance(default_input, dict):
                    if batch_input_key in default_input:
                        sources = default_input[batch_input_key]
                    elif default_input and all(
                        isinstance(k, str) and (k.endswith(".ts") or "/" in k)
                        for k in list(default_input.keys())[:10]
                    ):
                        sources = default_input

            if not sources and isinstance(inputs, dict) and inputs:
                non_default_keys = [k for k in inputs if k != "default"]
                if non_default_keys and all(
                    isinstance(k, str) and (k.endswith(".ts") or "/" in k)
                    for k in non_default_keys[:10]
                ):
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

            sources = {k: v for k, v in sources.items() if k != "_dummy"}

            if not sources:
                logger.info(
                    f"[TypescriptAstNode {node.id}] No real sources after filtering dummy entries - cache must exist"
                )
                return {"results": {}, "batch_mode": True, "total_sources": 0, "skipped": True}

            try:
                results = await self._ast_parser.parse_batch(
                    sources=sources,
                    extract_patterns=node.extract_patterns or ["interface", "type", "enum"],
                    options={
                        "parseMode": node.parse_mode or "module",
                    },
                )
            except Exception:
                import traceback

                logger.error(
                    f"[TypescriptAstNode {node.id}] Batch parse error: {traceback.format_exc()}"
                )
                raise

            return {"results": results, "batch_mode": True, "total_sources": len(sources)}

        else:
            source = node.source
            if not source:
                source = inputs.get("source", "")
            if not source and "default" in inputs and isinstance(inputs["default"], dict):
                source = inputs["default"].get("source", "")

            if not source:
                raise ValueError("No TypeScript source code provided")

            try:
                result = await self._ast_parser.parse(
                    source=source,
                    extract_patterns=node.extract_patterns or ["interface", "type", "enum"],
                    options={
                        "parseMode": node.parse_mode or "module",
                    },
                )
            except Exception as parser_error:
                import traceback

                logger.error(f"[TypescriptAstNode {node.id}] Parse error: {parser_error}")
                logger.error(f"[TypescriptAstNode {node.id}] Traceback: {traceback.format_exc()}")
                raise

            ast_data = result.get("ast", {})
            metadata = result.get("metadata", {})

            return {"ast": ast_data, "metadata": metadata, "batch_mode": False}

    def serialize_output(
        self, result: Any, request: ExecutionRequest[TypescriptAstNode]
    ) -> Envelope:
        node = request.node
        trace_id = request.execution_id or ""

        if isinstance(result, dict) and result.get("skipped"):
            return EnvelopeFactory.create({}, produced_by=node.id, trace_id=trace_id).with_meta(
                batch_mode=True, skipped=True, reason="Cache already exists"
            )

        if isinstance(result, dict) and result.get("batch_mode"):
            return EnvelopeFactory.create(
                result["results"], produced_by=node.id, trace_id=trace_id
            ).with_meta(
                batch_mode=True,
                total_sources=result["total_sources"],
                successful=len(result["results"]),
            )

        if isinstance(result, dict) and "ast" in result:
            include_raw_ast = getattr(node, "includeRawAST", False)

            extracted_definitions = result["ast"].get("extracted", {})

            output = {}
            if include_raw_ast:
                output["rawAST"] = result["ast"].get("raw", {})

            output["extracted"] = extracted_definitions
            output["metadata"] = result["metadata"]

            summary = {
                "totalExtracted": result["metadata"].get("extractedCount", 0),
                "byType": result["metadata"].get("byType", {}),
            }
            output["summary"] = summary

            return EnvelopeFactory.create(output, produced_by=node.id, trace_id=trace_id).with_meta(
                extracted_count=result["metadata"].get("extractedCount", 0),
                parse_mode=node.parse_mode or "module",
                include_jsdoc=node.include_jsdoc or False,
            )

        return super().serialize_output(result, request)

    async def prepare_inputs(
        self, request: ExecutionRequest[TypescriptAstNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        envelope_inputs = self.get_effective_inputs(request, inputs)
        return await super().prepare_inputs(request, envelope_inputs)

    def post_execute(
        self, request: ExecutionRequest[TypescriptAstNode], output: Envelope
    ) -> Envelope:
        self.emit_token_outputs(request, output)
        return output
