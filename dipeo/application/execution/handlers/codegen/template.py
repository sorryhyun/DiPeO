import hashlib
import time
from importlib import import_module
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER, TEMPLATE_RENDERER
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.unified_nodes.template_job_node import NodeType, TemplateJobNode
from dipeo.domain.execution.messaging.envelope import Envelope, EnvelopeFactory

logger = get_module_logger(__name__)


@register_handler
@requires_services(
    filesystem_adapter=FILESYSTEM_ADAPTER,
    template_renderer=TEMPLATE_RENDERER,
)
class TemplateJobNodeHandler(TypedNodeHandler[TemplateJobNode]):
    """Renders templates using Jinja2 syntax and outputs the result."""

    NODE_TYPE = NodeType.TEMPLATE_JOB

    _recent_writes: ClassVar[dict[tuple[str, str], tuple[float, str]]] = {}
    _DEDUP_WINDOW_SECONDS = 2.0

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
        node = request.node

        if not node.template_path and not node.template_content:
            return "Either template_path or template_content must be provided"

        return None

    async def pre_execute(self, request: ExecutionRequest[TemplateJobNode]) -> Envelope | None:
        node = request.node

        engine = node.engine or "internal"
        if engine not in ["internal", "jinja2"]:
            return EnvelopeFactory.create(
                body={"error": f"Unsupported template engine: {engine}", "type": "ValueError"},
                produced_by=str(node.id),
            )
        request.set_handler_state("engine", engine)

        return None

    @classmethod
    def _is_duplicate_write(cls, file_path: str, content: str, node_id: str) -> bool:
        if "diagram_generated_staged" in str(file_path) or "diagram_generated" in str(file_path):
            return False

        normalized_content = content
        if "generated_nodes.py" in str(file_path):
            import re

            normalized_content = re.sub(
                r"Generated at: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+",
                "Generated at: [TIMESTAMP]",
                content,
            )
            normalized_content = re.sub(
                r"# Available variables: now: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+",
                "# Available variables: now: [TIMESTAMP]",
                normalized_content,
            )

        content_hash = hashlib.md5(normalized_content.encode()).hexdigest()
        cache_key = (str(file_path), content_hash)

        current_time = time.time()

        if cache_key in cls._recent_writes:
            last_write_time, last_node_id = cls._recent_writes[cache_key]
            time_diff = current_time - last_write_time

            if time_diff < cls._DEDUP_WINDOW_SECONDS:
                return True

        cls._recent_writes[cache_key] = (current_time, node_id)

        cutoff_time = current_time - cls._DEDUP_WINDOW_SECONDS * 2
        cls._recent_writes = {k: v for k, v in cls._recent_writes.items() if v[0] > cutoff_time}

        return False

    async def prepare_inputs(
        self, request: ExecutionRequest[TemplateJobNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        from datetime import datetime

        envelope_inputs = self.get_effective_inputs(request, inputs)

        template_vars = {}

        template_vars["generated_at"] = datetime.now().isoformat()

        if request.node.variables:
            template_vars.update(request.node.variables)

        if envelope_inputs:
            for key, envelope in envelope_inputs.items():
                try:
                    value = envelope.as_json()
                except ValueError:
                    value = envelope.as_text()

                if key == "default" and isinstance(value, dict):
                    template_vars.update(value)
                else:
                    template_vars[key] = value
        return template_vars

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[TemplateJobNode]) -> Any:
        node = request.node
        template_vars = request.context.build_template_context(inputs=inputs, globals_win=True)

        request.set_handler_state("template_vars", template_vars.copy())

        filesystem_adapter = self._filesystem_adapter
        template_service = self._template_renderer
        engine = request.get_handler_state("engine")

        preprocessor = getattr(node, "preprocessor", None)
        if preprocessor:
            preprocessor_config = preprocessor if isinstance(preprocessor, dict) else {}
            module_name = preprocessor_config.get("module")
            function_name = preprocessor_config.get("function")

            if module_name and function_name:
                try:
                    module = import_module(module_name)
                    func = getattr(module, function_name)

                    preprocessor_args = preprocessor_config.get("args", {})
                    extra_context = func(context=template_vars, **preprocessor_args)

                    if isinstance(extra_context, dict):
                        template_vars.update(extra_context)
                except Exception as e:
                    logger.warning(f"Preprocessor failed: {e}")

        if node.template_content:
            template_content = node.template_content
        else:
            if not isinstance(node.template_path, str):
                raise TypeError(f"template_path must be a string, got {type(node.template_path)}")

            processed_template_path = (
                await template_service.render_string(node.template_path, template_vars)
            ).strip()

            template_path = Path(processed_template_path)

            if not filesystem_adapter.exists(template_path):
                raise FileNotFoundError(f"Template file not found: {node.template_path}")

            with filesystem_adapter.open(template_path, "rb") as f:
                template_content = f.read().decode("utf-8")

        if engine in ("internal", "jinja2"):
            rendered = await template_service.render_string(template_content, template_vars)
        else:
            rendered = template_content

        if node.output_path:
            processed_output_path = (
                await template_service.render_string(node.output_path, template_vars)
            ).strip()

            output_path = Path(processed_output_path)

            if self._is_duplicate_write(str(output_path), rendered, str(node.id)):
                request.set_handler_state("current_output_path", output_path)
                return rendered

            parent_dir = output_path.parent
            if parent_dir != Path() and not filesystem_adapter.exists(parent_dir):
                filesystem_adapter.mkdir(parent_dir, parents=True)

            with filesystem_adapter.open(output_path, "wb") as f:
                f.write(rendered.encode("utf-8"))
            request.set_handler_state("current_output_path", output_path)

        return rendered

    def serialize_output(self, result: Any, request: ExecutionRequest[TemplateJobNode]) -> Envelope:
        node = request.node
        trace_id = request.execution_id or ""
        template_vars = request.get_handler_state("template_vars", {})
        engine = request.get_handler_state("engine")
        current_output_path = request.get_handler_state("current_output_path")

        if isinstance(result, dict) and "written" in result:
            body = f"Written {result['count']} files: {', '.join(result['written'])}"
        else:
            body = result if isinstance(result, str) else str(result)

        envelope = EnvelopeFactory.create(body=body, produced_by=node.id, trace_id=trace_id)

        meta = {
            "engine": engine,
            "template_path": node.template_path,
            "template_vars": template_vars,
        }

        if current_output_path:
            meta["output_path"] = str(current_output_path)

        if isinstance(result, dict) and "written" in result:
            meta["files"] = result["written"]
            meta["file_count"] = result["count"]
        elif current_output_path:
            meta["files"] = [str(current_output_path)]
            meta["file_count"] = 1

        envelope = envelope.with_meta(**meta)

        return envelope

    def post_execute(
        self, request: ExecutionRequest[TemplateJobNode], output: Envelope
    ) -> Envelope:
        self.emit_token_outputs(request, output)
        return output
