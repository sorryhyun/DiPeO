"""Diff/Patch handler for applying unified diffs to files with safety controls."""

import difflib
import hashlib
import logging
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.diagram_generated.enums import NodeType
from dipeo.diagram_generated.unified_nodes import DiffPatchNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


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

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[DiffPatchNode]) -> Envelope:
        """Apply a diff patch to a file with validation and safety features."""
        node = request.node
        target_path = Path(node.target_path)

        try:
            # Extract node configuration
            diff_content = node.diff
            format_type = node.format or "unified"
            apply_mode = node.apply_mode or "normal"
            create_backup = node.backup if node.backup is not None else True
            validate_patch = node.validate_patch if node.validate_patch is not None else True
            backup_dir = Path(node.backup_dir) if node.backup_dir else None
            strip_level = node.strip_level or 1
            fuzz_factor = node.fuzz_factor or 2
            reject_file_path = Path(node.reject_file) if node.reject_file else None
            ignore_whitespace = node.ignore_whitespace or False
            create_missing = node.create_missing or False

            logger.info(f"Applying {format_type} diff to {target_path}")
            logger.debug(f"Mode: {apply_mode}, Backup: {create_backup}, Validate: {validate_patch}")

            # Initialize result tracking
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

            # Check if target file exists
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
                    return self.serialize_output(result, request)

            # Read original file content
            original_content = target_path.read_text()
            original_lines = original_content.splitlines(keepends=True)

            # Create backup if requested
            backup_path = None
            if create_backup and apply_mode != "dry_run":
                backup_path = self._create_backup(target_path, backup_dir)
                result["backup_path"] = str(backup_path)
                logger.info(f"Created backup at: {backup_path}")

            # Parse and validate the diff
            if validate_patch:
                validation_errors = self._validate_diff(diff_content, format_type)
                if validation_errors:
                    result["status"] = "invalid"
                    result["errors"].extend(validation_errors)
                    logger.error(f"Diff validation failed: {validation_errors}")
                    return self.serialize_output(result, request)

            # Apply the diff based on format and mode
            if apply_mode == "reverse":
                # Reverse the diff before applying
                diff_content = self._reverse_diff(diff_content, format_type)

            # Apply the patch
            patched_lines, rejected_hunks = self._apply_diff(
                original_lines,
                diff_content,
                format_type,
                strip_level,
                fuzz_factor,
                ignore_whitespace,
            )

            result["applied_hunks"] = len(self._parse_hunks(diff_content)) - len(rejected_hunks)
            result["rejected_hunks"] = rejected_hunks

            # Handle rejected hunks
            if rejected_hunks:
                logger.warning(f"Rejected {len(rejected_hunks)} hunks")
                if reject_file_path:
                    self._save_rejected_hunks(reject_file_path, rejected_hunks)
                    logger.info(f"Saved rejected hunks to: {reject_file_path}")

                if apply_mode == "force":
                    logger.warning("Force mode: Continuing despite rejected hunks")
                elif apply_mode != "dry_run":
                    # In normal mode, fail if there are rejected hunks
                    result["status"] = "partial"
                    if backup_path:
                        logger.info("Restoring from backup due to rejected hunks")
                        shutil.copy2(backup_path, target_path)
                    return self.serialize_output(result, request)

            # Write the patched content (unless dry run)
            patched_content = "".join(patched_lines)
            if apply_mode != "dry_run":
                target_path.write_text(patched_content)
                logger.info(f"Successfully patched {target_path}")

            # Calculate file hash for verification
            file_hash = hashlib.sha256(patched_content.encode()).hexdigest()
            result["file_hash"] = file_hash
            result["status"] = "success" if not rejected_hunks else "partial"

            return self.serialize_output(result, request)

        except Exception as exc:
            logger.exception("Failed to apply diff patch for %s", target_path)
            error_result = {
                "status": "error",
                "target_path": str(target_path),
                "errors": [str(exc)],
            }
            return EnvelopeFactory.create(
                body=error_result,
                produced_by=str(node.id),
                trace_id=request.execution_id or "",
            )

    async def prepare_inputs(
        self, request: ExecutionRequest[DiffPatchNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Prepare inputs from envelopes."""
        return self.get_effective_inputs(request, inputs)

    def serialize_output(self, output: dict[str, Any], request: ExecutionRequest[DiffPatchNode]) -> Envelope:
        """Serialize the output to an envelope."""
        return EnvelopeFactory.create(
            body=output,
            produced_by=str(request.node.id),
            trace_id=request.execution_id
        )

    async def pre_execute(self, request: ExecutionRequest[DiffPatchNode]) -> Envelope | None:
        """Validate the diff patch configuration before execution."""
        node = request.node

        # Validate target path
        if not node.target_path:
            return EnvelopeFactory.create(
                body={"error": "No target path provided", "type": "ValueError"},
                produced_by=str(node.id)
            )

        # Validate diff content
        if not node.diff:
            return EnvelopeFactory.create(
                body={"error": "No diff content provided", "type": "ValueError"},
                produced_by=str(node.id)
            )

        return None

    def _create_backup(self, target_path: Path, backup_dir: Optional[Path]) -> Path:
        """Create a backup of the target file."""
        if backup_dir:
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / f"{target_path.name}.backup.{os.getpid()}"
        else:
            backup_path = target_path.with_suffix(f"{target_path.suffix}.backup.{os.getpid()}")

        shutil.copy2(target_path, backup_path)
        return backup_path

    def _validate_diff(self, diff_content: str, format_type: str) -> list[str]:
        """Validate the diff content for basic structure."""
        errors = []

        if not diff_content.strip():
            errors.append("Diff content is empty")
            return errors

        if format_type == "unified" or format_type == "git":
            # Check for unified diff headers
            if not re.search(r"^---\s+", diff_content, re.MULTILINE):
                errors.append("Missing '---' header for original file")
            if not re.search(r"^\+\+\+\s+", diff_content, re.MULTILINE):
                errors.append("Missing '+++' header for new file")
            if not re.search(r"^@@\s+-\d+", diff_content, re.MULTILINE):
                errors.append("Missing hunk headers (@@)")
        elif format_type == "context":
            # Check for context diff headers
            if not re.search(r"^\*\*\*\s+", diff_content, re.MULTILINE):
                errors.append("Missing '***' header for original file")
            if not re.search(r"^---\s+", diff_content, re.MULTILINE):
                errors.append("Missing '---' header for new file")

        return errors

    def _parse_hunks(self, diff_content: str) -> list[dict[str, Any]]:
        """Parse diff content into hunks."""
        hunks = []
        current_hunk = None

        for line in diff_content.splitlines():
            if line.startswith("@@"):
                # Parse hunk header
                match = re.match(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@", line)
                if match:
                    current_hunk = {
                        "old_start": int(match.group(1)),
                        "old_lines": int(match.group(2) or 1),
                        "new_start": int(match.group(3)),
                        "new_lines": int(match.group(4) or 1),
                        "lines": [],
                    }
                    hunks.append(current_hunk)
            elif current_hunk:
                current_hunk["lines"].append(line)

        return hunks

    def _apply_diff(
        self,
        original_lines: list[str],
        diff_content: str,
        format_type: str,
        strip_level: int,
        fuzz_factor: int,
        ignore_whitespace: bool,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Apply diff to original lines and return patched lines and rejected hunks."""
        # For simplicity, use Python's difflib for unified format
        # In production, you might want to use the actual patch command

        if format_type not in ["unified", "git"]:
            logger.warning(f"Format {format_type} not fully supported, treating as unified")

        hunks = self._parse_hunks(diff_content)
        patched_lines = original_lines.copy()
        rejected_hunks = []
        offset = 0  # Track line number offset due to previous patches

        for hunk in hunks:
            old_start = hunk["old_start"] - 1 + offset  # Convert to 0-based index
            old_lines = hunk["old_lines"]
            new_lines = []
            old_content = []

            # Parse hunk lines
            for line in hunk["lines"]:
                if line.startswith("-"):
                    old_content.append(line[1:])
                elif line.startswith("+"):
                    new_lines.append(line[1:])
                elif line.startswith(" "):
                    old_content.append(line[1:])
                    new_lines.append(line[1:])

            # Try to find and apply the hunk with fuzzing
            applied = False
            for fuzz in range(fuzz_factor + 1):
                for direction in [0, -1, 1]:  # Try exact, before, after
                    test_start = old_start + direction * fuzz
                    if test_start < 0 or test_start >= len(patched_lines):
                        continue

                    # Check if the old content matches (with optional whitespace ignoring)
                    if self._match_content(
                        patched_lines[test_start : test_start + len(old_content)],
                        old_content,
                        ignore_whitespace,
                    ):
                        # Apply the patch
                        patched_lines = (
                            patched_lines[:test_start]
                            + new_lines
                            + patched_lines[test_start + len(old_content) :]
                        )
                        offset += len(new_lines) - len(old_content)
                        applied = True
                        break

                if applied:
                    break

            if not applied:
                rejected_hunks.append(hunk)

        return patched_lines, rejected_hunks

    def _match_content(
        self, actual_lines: list[str], expected_lines: list[str], ignore_whitespace: bool
    ) -> bool:
        """Check if actual lines match expected lines."""
        if len(actual_lines) != len(expected_lines):
            return False

        for actual, expected in zip(actual_lines, expected_lines, strict=False):
            if ignore_whitespace:
                if actual.strip() != expected.strip():
                    return False
            else:
                if actual != expected:
                    return False

        return True

    def _reverse_diff(self, diff_content: str, format_type: str) -> str:
        """Reverse a diff (swap additions and deletions)."""
        reversed_lines = []

        for line in diff_content.splitlines():
            if line.startswith("---"):
                # Swap --- and +++ headers
                reversed_lines.append(
                    line.replace("---", "+++temp").replace("+++", "---").replace("+++temp", "+++")
                )
            elif line.startswith("+++"):
                reversed_lines.append(
                    line.replace("+++", "---temp").replace("---", "+++").replace("---temp", "---")
                )
            elif line.startswith("-"):
                # Change deletions to additions
                reversed_lines.append("+" + line[1:])
            elif line.startswith("+"):
                # Change additions to deletions
                reversed_lines.append("-" + line[1:])
            else:
                # Keep context lines and headers unchanged
                reversed_lines.append(line)

        return "\n".join(reversed_lines)

    def _save_rejected_hunks(self, reject_file: Path, rejected_hunks: list[dict[str, Any]]) -> None:
        """Save rejected hunks to a file."""
        reject_content = []

        for i, hunk in enumerate(rejected_hunks, 1):
            reject_content.append(f"# Rejected hunk {i}")
            reject_content.append(
                f"@@ -{hunk['old_start']},{hunk['old_lines']} "
                f"+{hunk['new_start']},{hunk['new_lines']} @@"
            )
            reject_content.extend(hunk["lines"])
            reject_content.append("")

        reject_file.parent.mkdir(parents=True, exist_ok=True)
        reject_file.write_text("\n".join(reject_content))
