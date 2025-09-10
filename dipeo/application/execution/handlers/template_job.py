import hashlib
import logging
import time
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER
from dipeo.diagram_generated.unified_nodes.template_job_node import NodeType, TemplateJobNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.infrastructure.codegen.templates.drivers.factory import get_enhanced_template_service

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@register_handler
class TemplateJobNodeHandler(TypedNodeHandler[TemplateJobNode]):
    """Renders templates using Jinja2 syntax and outputs the result."""

    NODE_TYPE = NodeType.TEMPLATE_JOB

    # Class-level cache for deduplication
    # Key: (file_path, content_hash), Value: (timestamp, node_id)
    _recent_writes: ClassVar[dict[tuple[str, str], tuple[float, str]]] = {}
    _DEDUP_WINDOW_SECONDS = 2.0  # Deduplicate writes within 2 seconds

    def __init__(self):
        super().__init__()
        self._template_service = None  # Lazy initialization
        # Instance variables for passing data between methods
        self._current_filesystem_adapter = None
        self._current_engine = None
        self._current_template_service = None
        self._current_template_processor = None

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
    def requires_services(self) -> list[str]:
        return ["filesystem_adapter"]

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
        """Pre-execution setup: validate template file and processor availability.

        Moves template file existence check, processor setup, and service validation
        out of execute_request for cleaner separation of concerns.
        """
        node = request.node
        services = request.services

        # Get filesystem adapter from services or use injected one
        filesystem_adapter = services.resolve(FILESYSTEM_ADAPTER)
        if not filesystem_adapter:
            return EnvelopeFactory.create(
                body={
                    "error": "Filesystem adapter is required for template job execution",
                    "type": "RuntimeError",
                },
                produced_by=str(node.id),
            )

        # Store filesystem adapter in instance variable for execute_request
        self._current_filesystem_adapter = filesystem_adapter

        # Validate template engine
        engine = node.engine or "internal"
        if engine not in ["internal", "jinja2"]:
            return EnvelopeFactory.create(
                body={"error": f"Unsupported template engine: {engine}", "type": "ValueError"},
                produced_by=str(node.id),
            )
        self._current_engine = engine

        # Initialize template service
        try:
            template_service = self._get_template_service()
            self._current_template_service = template_service
        except Exception as e:
            return EnvelopeFactory.create(
                body={"error": str(e), "type": e.__class__.__name__}, produced_by=str(node.id)
            )

        # Template processor no longer needed - using Jinja2 for everything
        self._current_template_processor = None

        # No early return - proceed to execute_request
        return None

    def _get_template_service(self):
        """Get or create the template service."""
        if self._template_service is None:
            try:
                self._template_service = get_enhanced_template_service()
            except Exception as e:
                print(f"[ERROR] Failed to create template service: {e}")
                import traceback

                traceback.print_exc()
                raise
        return self._template_service

    @classmethod
    def _is_duplicate_write(cls, file_path: str, content: str, node_id: str) -> bool:
        """Check if this is a duplicate write within the deduplication window."""
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
                logger.warning(
                    f"[DEDUPLICATION] Skipping duplicate write to {file_path} "
                    f"from node {node_id} (already written by {last_node_id} "
                    f"{time_diff:.2f}s ago)"
                )
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
        envelope_inputs = self.consume_token_inputs(request, inputs)

        node = request.node
        template_vars = {}

        # Add default variables
        template_vars["now"] = datetime.now().isoformat()

        # Add node-defined variables
        if node.variables:
            template_vars.update(node.variables)

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

        # Store template variables for building representations
        self._template_vars = template_vars.copy()

        # Use services from instance variables (set in pre_execute)
        filesystem_adapter = self._current_filesystem_adapter
        engine = self._current_engine
        template_service = self._current_template_service
        template_processor = self._current_template_processor

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

        # Helper function to render and write a single file
        async def render_to_path(output_path_template: str, local_context: dict) -> str:
            """Render template and write to file specified by path template."""
            # Render the template content
            if engine == "internal":
                rendered = await template_service.render_string(template_content, local_context)
            elif engine == "jinja2":
                try:
                    rendered = await template_service.render_string(template_content, local_context)
                except Exception as e:
                    # Fall back to standard Jinja2
                    rendered = self._render_jinja2(template_content, local_context)
                    logger.debug(f"Enhancement fallback: {e}")
            else:
                rendered = template_content  # Fallback

            # Render output path via Jinja2 as well
            output_path_str = (
                await template_service.render_string(output_path_template, local_context)
            ).strip()
            output_path = Path(output_path_str)

            # Add detailed trace logging for foreach mode
            if "generated_nodes.py" in str(output_path):
                logger.warning(
                    f"[GENERATED_NODES WRITE FOREACH] Node {node.id} writing to {output_path} in foreach mode"
                )
                # logger.debug(
                #     f"[GENERATED_NODES FOREACH CONTEXT] Item index: {local_context.get('index')}, Item var: {var_name}"
                # )

            # Check for duplicate write
            if self._is_duplicate_write(str(output_path), rendered, str(node.id)):
                logger.info(f"[DEDUP] Skipping duplicate write to {output_path}")
                return str(output_path)  # Return path without writing

            # Create parent directories if needed
            parent_dir = output_path.parent
            if parent_dir != Path() and not filesystem_adapter.exists(parent_dir):
                filesystem_adapter.mkdir(parent_dir, parents=True)

            # Write the file
            with filesystem_adapter.open(output_path, "wb") as f:
                f.write(rendered.encode("utf-8"))

            return str(output_path)

        # Single file mode (foreach not currently implemented)
        # Render template
        if engine == "internal":
            rendered = await template_service.render_string(template_content, template_vars)
        elif engine == "jinja2":
            try:
                rendered = await template_service.render_string(template_content, template_vars)
            except Exception as e:
                # Fall back to standard Jinja2
                rendered = await self._render_jinja2(template_content, template_vars)
                logger.debug(f"Enhancement fallback: {e}")
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
            if "generated_nodes.py" in str(output_path):
                logger.warning(f"[GENERATED_NODES WRITE] Node {node.id} writing to {output_path}")
                if "batch_item" in template_vars:
                    logger.debug("[GENERATED_NODES BATCH] Batch item detected in context")

            # Check for duplicate write
            if self._is_duplicate_write(str(output_path), rendered, str(node.id)):
                logger.info(f"[DEDUP] Skipping duplicate write to {output_path}")
                # Store output path for metadata but don't write
                self._current_output_path = output_path
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
        template_vars = getattr(self, "_template_vars", {})

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
            "engine": self._current_engine,
            "template_path": node.template_path,
            "template_vars": template_vars,
        }

        # Add output path if available
        if hasattr(self, "_current_output_path") and self._current_output_path:
            meta["output_path"] = str(self._current_output_path)

        # Add file write info if available
        if isinstance(result, dict) and "written" in result:
            meta["files"] = result["written"]
            meta["file_count"] = result["count"]
        elif hasattr(self, "_current_output_path") and self._current_output_path:
            meta["files"] = [str(self._current_output_path)]
            meta["file_count"] = 1

        # Add metadata to envelope
        envelope = envelope.with_meta(**meta)

        return envelope

    async def _render_jinja2(self, template: str, variables: dict[str, Any]) -> str:
        """Render template using Jinja2 with custom filters."""
        try:
            from jinja2 import Environment

            # Create Jinja2 environment with custom filters
            env = Environment()

            # Add custom filters from the registry
            from dipeo.infrastructure.codegen.templates.filters import create_filter_registry

            registry = create_filter_registry()
            for name, func in registry.get_all_filters().items():
                env.filters[name] = func

            # Create and render template
            jinja_template = env.from_string(template)
            return jinja_template.render(**variables)
        except ImportError as e:
            raise ImportError("Jinja2 is not installed. Install it with: pip install jinja2") from e

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
