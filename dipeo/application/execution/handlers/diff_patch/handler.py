import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.execution.handlers.diff_patch.diff_processor import (
    parse_hunks,
    reverse_diff,
    validate_diff,
)
from dipeo.application.execution.handlers.diff_patch.patch_applier import (
    apply_diff,
    calculate_file_hash,
    create_backup,
    save_rejected_hunks,
)
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.enums import NodeType
from dipeo.diagram_generated.unified_nodes import DiffPatchNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    pass

logger = get_module_logger(__name__)


@register_handler
@requires_services()
class DiffPatchHandler(TypedNodeHandler[DiffPatchNode]):
    """Handler for applying diff patches to files with safety controls."""

    NODE_TYPE = NodeType.DIFF_PATCH

    @property
    def node_class(self) -> type[DiffPatchNode]:
        return DiffPatchNode

    @property
    def node_type(self) -> str:
        return NodeType.DIFF_PATCH.value

    @property
    def description(self) -> str:
        return "Applies diff patches to files with validation and safety controls"

    async def run(
        self, inputs: dict[str, Any], request: ExecutionRequest[DiffPatchNode]
    ) -> dict[str, Any]:
        """Apply a diff patch to a file with validation and safety features."""
        node = request.node
        target_path = Path(node.target_path)

        diff_content = node.diff
        format_type = node.format or "unified"
        apply_mode = node.apply_mode or "normal"
        create_backup_flag = node.backup if node.backup is not None else True
        validate_patch = node.validate_patch if node.validate_patch is not None else True
        backup_dir = Path(node.backup_dir) if node.backup_dir else None
        strip_level = node.strip_level or 1
        fuzz_factor = node.fuzz_factor or 2
        reject_file_path = Path(node.reject_file) if node.reject_file else None
        ignore_whitespace = node.ignore_whitespace or False
        create_missing = node.create_missing or False

        logger.info(f"Applying {format_type} diff to {target_path}")
        logger.debug(
            f"Mode: {apply_mode}, Backup: {create_backup_flag}, Validate: {validate_patch}"
        )

        result = {
            "status": "pending",
            "target_path": str(target_path),
            "applied_hunks": 0,
            "rejected_hunks": [],
            "backup_path": None,
            "file_hash": None,
            "dry_run": apply_mode == "dry_run",
            "errors": [],
        }

        if not target_path.exists():
            if create_missing:
                logger.info(f"Creating missing file: {target_path}")
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text("")
            else:
                error_msg = f"Target file does not exist: {target_path}"
                logger.error(error_msg)
                result["status"] = "error"
                result["errors"].append(error_msg)
                return result

        original_content = target_path.read_text()
        original_lines = original_content.splitlines(keepends=True)

        backup_path = None
        if create_backup_flag and apply_mode != "dry_run":
            backup_path = create_backup(target_path, backup_dir)
            result["backup_path"] = str(backup_path)
            logger.info(f"Created backup at: {backup_path}")

        if validate_patch:
            validation_errors = validate_diff(diff_content, format_type)
            if validation_errors:
                result["status"] = "invalid"
                result["errors"].extend(validation_errors)
                logger.error(f"Diff validation failed: {validation_errors}")
                return result

        if apply_mode == "reverse":
            diff_content = reverse_diff(diff_content, format_type)

        patched_lines, rejected_hunks = apply_diff(
            original_lines,
            diff_content,
            format_type,
            strip_level,
            fuzz_factor,
            ignore_whitespace,
        )

        result["applied_hunks"] = len(parse_hunks(diff_content)) - len(rejected_hunks)
        result["rejected_hunks"] = rejected_hunks

        if rejected_hunks:
            logger.warning(f"Rejected {len(rejected_hunks)} hunks")
            if reject_file_path:
                save_rejected_hunks(reject_file_path, rejected_hunks)
                logger.info(f"Saved rejected hunks to: {reject_file_path}")

            if apply_mode == "force":
                logger.warning("Force mode: Continuing despite rejected hunks")
            elif apply_mode != "dry_run":
                result["status"] = "partial"
                if backup_path:
                    logger.info("Restoring from backup due to rejected hunks")
                    shutil.copy2(backup_path, target_path)
                return result

        patched_content = "".join(patched_lines)
        if apply_mode != "dry_run":
            target_path.write_text(patched_content)
            logger.info(f"Successfully patched {target_path}")

        file_hash = calculate_file_hash(patched_content)
        result["file_hash"] = file_hash
        result["status"] = "success" if not rejected_hunks else "partial"

        return result

    async def prepare_inputs(
        self, request: ExecutionRequest[DiffPatchNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Prepare inputs from envelopes."""
        return self.get_effective_inputs(request, inputs)

    def serialize_output(
        self, output: dict[str, Any], request: ExecutionRequest[DiffPatchNode]
    ) -> Envelope:
        """Serialize the output to an envelope."""
        return EnvelopeFactory.create(
            body=output, produced_by=str(request.node.id), trace_id=request.execution_id
        )

    async def pre_execute(self, request: ExecutionRequest[DiffPatchNode]) -> Envelope | None:
        """Validate the diff patch configuration before execution."""
        node = request.node

        if not node.target_path:
            return EnvelopeFactory.create(
                body={"error": "No target path provided", "type": "ValueError"},
                produced_by=str(node.id),
            )

        if not node.diff:
            return EnvelopeFactory.create(
                body={"error": "No diff content provided", "type": "ValueError"},
                produced_by=str(node.id),
            )

        return None
