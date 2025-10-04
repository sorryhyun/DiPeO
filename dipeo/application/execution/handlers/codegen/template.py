import hashlib
import logging
import time
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER, TEMPLATE_RENDERER
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.unified_nodes.template_job_node import NodeType, TemplateJobNode
from dipeo.domain.codegen.ports import TemplateRendererPort
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    pass

logger = get_module_logger(__name__)


@register_handler
@requires_services(
    filesystem_adapter=FILESYSTEM_ADAPTER,
    template_renderer=TEMPLATE_RENDERER,
)
class TemplateJobNodeHandler(TypedNodeHandler[TemplateJobNode]):
    """Renders templates using Jinja2 syntax and outputs the result."""

    NODE_TYPE = NodeType.TEMPLATE_JOB

    # Class-level cache for deduplication
    # Key: (file_path, content_hash), Value: (timestamp, node_id)
    _recent_writes: ClassVar[dict[tuple[str, str], tuple[float, str]]] = {}
    _DEDUP_WINDOW_SECONDS = 2.0  # Deduplicate writes within 2 seconds

    def __init__(self):
        super().__init__()

    @property
    def node_class(self) -> type[TemplateJobNode]:
        return TemplateJobNode

    @property
    def node_type(self) -> str:
        return NodeType.TEMPLATE_JOB.value

    @property
    def schema(self) -> type[BaseModel]:
        return TemplateJobNode

    @property
    def description(self) -> str:
        return "Renders templates using Jinja2 syntax and outputs the result"

    def validate(self, request: ExecutionRequest[TemplateJobNode]) -> str | None:
        """Validate the template job configuration."""
        node = request.node

        # Must have either template_path or template_content
        if not node.template_path and not node.template_content:
            return "Either template_path or template_content must be provided"

        return None

    async def pre_execute(self, request: ExecutionRequest[TemplateJobNode]) -> Envelope | None:
        """Pre-execution setup: validate template engine configuration."""
        node = request.node

        # Validate template engine
        engine = node.engine or "internal"
        if engine not in ["internal", "jinja2"]:
            return EnvelopeFactory.create(
                body={"error": f"Unsupported template engine: {engine}", "type": "ValueError"},
                produced_by=str(node.id),
            )
        request.set_handler_state("engine", engine)

        # No early return - proceed to execute_request
        return None

    @classmethod
    def _is_duplicate_write(cls, file_path: str, content: str, node_id: str) -> bool:
        """Check if this is a duplicate write within the deduplication window."""
        # Skip deduplication for codegen output directories
        # These files should always be regenerated with fresh content
        if "diagram_generated_staged" in str(file_path) or "diagram_generated" in str(file_path):
            # logger.debug(f"[CODEGEN] Skipping deduplication for codegen output: {file_path}")
            return False

        # Special handling for generated_nodes.py - normalize content to ignore timestamps
        normalized_content = content
        if "generated_nodes.py" in str(file_path):
            # Remove timestamp lines for comparison
            import re

            # Remove lines with timestamps like "Generated at: 2025-08-21T11:38:18.584978"
            normalized_content = re.sub(
                r"Generated at: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+",
                "Generated at: [TIMESTAMP]",
                content,
            )
            # Also normalize the "now" variable in comments
            normalized_content = re.sub(
                r"# Available variables: now: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+",
                "# Available variables: now: [TIMESTAMP]",
                normalized_content,
            )

        # Create content hash for comparison
        content_hash = hashlib.md5(normalized_content.encode()).hexdigest()
        cache_key = (str(file_path), content_hash)

        current_time = time.time()

        # Check if we've seen this write recently
        if cache_key in cls._recent_writes:
            last_write_time, last_node_id = cls._recent_writes[cache_key]
            time_diff = current_time - last_write_time

            if time_diff < cls._DEDUP_WINDOW_SECONDS:
                # This is a duplicate write
                return True

        # Not a duplicate - update cache
        cls._recent_writes[cache_key] = (current_time, node_id)

        # Clean up old entries from cache
        cutoff_time = current_time - cls._DEDUP_WINDOW_SECONDS * 2
        cls._recent_writes = {k: v for k, v in cls._recent_writes.items() if v[0] > cutoff_time}

        return False

    def _resolve_dotted_path(self, dotted: str, ctx: dict) -> Any:
        """Resolve a dotted path like 'a.b.c' into the context."""
        current = ctx
        for part in dotted.split("."):
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                current = current[idx] if idx < len(current) else None
            else:
                current = getattr(current, part, None)
            if current is None:
                break
        return current

    async def prepare_inputs(
        self, request: ExecutionRequest[TemplateJobNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Prepare template variables from envelopes and node configuration.

        Phase 5: Now consumes tokens from incoming edges when available.
        """
        from datetime import datetime

        # Phase 5: Consume tokens from incoming edges or fall back to regular inputs
        envelope_inputs = self.get_effective_inputs(request, inputs)

        template_vars = {}

        # Add default variables
        template_vars["generated_at"] = datetime.now().isoformat()

        # Add node-defined variables
        if request.node.variables:
            template_vars.update(request.node.variables)

        # Add inputs from connected nodes - convert from envelopes
        if envelope_inputs:
            # Process envelope inputs
            for key, envelope in envelope_inputs.items():
                try:
                    # Try to parse as JSON first
                    value = envelope.as_json()
                except ValueError:
                    # Fall back to text
                    value = envelope.as_text()

                # Check if we have a single 'default' key with dict value
                if key == "default" and isinstance(value, dict):
                    # Unwrap the default for better template ergonomics
                    template_vars.update(value)
                else:
                    # For labeled connections, add to template_vars
                    template_vars[key] = value
        return template_vars

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[TemplateJobNode]) -> Any:
        """Execute template rendering with support for foreach and preprocessor."""
        node = request.node
        # Use centralized context builder to include globals
        template_vars = request.context.build_template_context(inputs=inputs, globals_win=True)

        # Store template variables for building representations via handler state
        request.set_handler_state("template_vars", template_vars.copy())

        # Services are now injected by the decorator
        filesystem_adapter = self._filesystem_adapter
        template_service = self._template_renderer
        engine = request.get_handler_state("engine")

        # Apply preprocessor if configured
        preprocessor = getattr(node, "preprocessor", None)
        if preprocessor:
            preprocessor_config = preprocessor if isinstance(preprocessor, dict) else {}
            module_name = preprocessor_config.get("module")
            function_name = preprocessor_config.get("function")

            if module_name and function_name:
                try:
                    # Import the module and get the function
                    module = import_module(module_name)
                    func = getattr(module, function_name)

                    # Call the preprocessor with context and any additional args
                    preprocessor_args = preprocessor_config.get("args", {})
                    extra_context = func(context=template_vars, **preprocessor_args)

                    # Update template vars with preprocessor results
                    if isinstance(extra_context, dict):
                        template_vars.update(extra_context)
                except Exception as e:
                    logger.warning(f"Preprocessor failed: {e}")
                    # Continue without preprocessor results

        # Get template content
        if node.template_content:
            template_content = node.template_content
        else:
            # Use Jinja2 for both paths and contents
            processed_template_path = (
                await template_service.render_string(node.template_path, template_vars)
            ).strip()

            # Load from file - just use the path as-is since filesystem adapter handles base path
            template_path = Path(processed_template_path)

            if not filesystem_adapter.exists(template_path):
                raise FileNotFoundError(f"Template file not found: {node.template_path}")

            with filesystem_adapter.open(template_path, "rb") as f:
                template_content = f.read().decode("utf-8")

        # Render template (foreach mode not currently implemented)
        # Render template
        if engine in ("internal", "jinja2"):
            try:
                rendered = await template_service.render_string(template_content, template_vars)
            except Exception as e:
                # Only log on errors
                logger.error(
                    f"[TEMPLATE ERROR] Failed to render template for node {node.id} ({node.label})"
                )
                logger.error(f"[TEMPLATE ERROR] Template path: {node.template_path}")
                logger.error(f"[TEMPLATE ERROR] Template content preview: {template_content[:200]}")
                logger.error(f"[TEMPLATE ERROR] Available variables: {list(template_vars.keys())}")
                logger.error(f"[TEMPLATE ERROR] Error details: {e}")
                raise
        else:
            rendered = template_content

        # Write to file if output_path is specified
        if node.output_path:
            # Use Jinja2 for output path
            processed_output_path = (
                await template_service.render_string(node.output_path, template_vars)
            ).strip()

            output_path = Path(processed_output_path)

            # Check if this is a duplicate write to generated_nodes.py
            # if "generated_nodes.py" in str(output_path):
            # logger.warning(f"[GENERATED_NODES WRITE] Node {node.id} writing to {output_path}")
            # if "batch_item" in template_vars:
            # logger.debug("[GENERATED_NODES BATCH] Batch item detected in context")

            # Check for duplicate write
            if self._is_duplicate_write(str(output_path), rendered, str(node.id)):
                # logger.info(f"[DEDUP] Skipping duplicate write to {output_path}")
                # Store output path for metadata but don't write
                request.set_handler_state("current_output_path", output_path)
                return rendered  # Return content without writing

            # Create parent directories if needed
            parent_dir = output_path.parent
            if parent_dir != Path() and not filesystem_adapter.exists(parent_dir):
                filesystem_adapter.mkdir(parent_dir, parents=True)

            with filesystem_adapter.open(output_path, "wb") as f:
                f.write(rendered.encode("utf-8"))
            # Store output path for metadata
            self._current_output_path = output_path
        else:
            logger.info(
                "[TEMPLATE_JOB DEBUG] No output_path specified, returning rendered content only"
            )

        return rendered

    def serialize_output(self, result: Any, request: ExecutionRequest[TemplateJobNode]) -> Envelope:
        """Serialize rendered template to envelope."""
        node = request.node
        trace_id = request.execution_id or ""
        template_vars = request.get_handler_state("template_vars", {})
        engine = request.get_handler_state("engine")
        current_output_path = request.get_handler_state("current_output_path")

        # Determine the body content
        if isinstance(result, dict) and "written" in result:
            # Foreach mode - multiple files written
            body = f"Written {result['count']} files: {', '.join(result['written'])}"
        else:
            # Single file mode
            body = result if isinstance(result, str) else str(result)

        # Create envelope
        envelope = EnvelopeFactory.create(body=body, produced_by=node.id, trace_id=trace_id)

        # Build metadata
        meta = {
            "engine": engine,
            "template_path": node.template_path,
            "template_vars": template_vars,
        }

        # Add output path if available
        if current_output_path:
            meta["output_path"] = str(current_output_path)

        # Add file write info if available
        if isinstance(result, dict) and "written" in result:
            meta["files"] = result["written"]
            meta["file_count"] = result["count"]
        elif current_output_path:
            meta["files"] = [str(current_output_path)]
            meta["file_count"] = 1

        # Add metadata to envelope
        envelope = envelope.with_meta(**meta)

        return envelope

    def post_execute(
        self, request: ExecutionRequest[TemplateJobNode], output: Envelope
    ) -> Envelope:
        """Post-execution hook to log template execution details and emit tokens.

        Phase 5: Now emits output as tokens to trigger downstream nodes.
        """
        # Phase 5: Emit output as tokens to trigger downstream nodes
        self.emit_token_outputs(request, output)

        # Post-execution logging can use instance variables if needed
        # No need for metadata access
        return output
