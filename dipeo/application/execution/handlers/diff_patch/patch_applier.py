import hashlib
import os
import shutil
from pathlib import Path
from typing import Any

from dipeo.application.execution.handlers.diff_patch.diff_processor import parse_hunks
from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)


def create_backup(target_path: Path, backup_dir: Path | None) -> Path:
    if backup_dir:
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"{target_path.name}.backup.{os.getpid()}"
    else:
        backup_path = target_path.with_suffix(f"{target_path.suffix}.backup.{os.getpid()}")

    shutil.copy2(target_path, backup_path)
    return backup_path


def apply_diff(
    original_lines: list[str],
    diff_content: str,
    format_type: str,
    strip_level: int,
    fuzz_factor: int,
    ignore_whitespace: bool,
) -> tuple[list[str], list[dict[str, Any]]]:
    if format_type not in ["unified", "git"]:
        logger.warning(f"Format {format_type} not fully supported, treating as unified")

    hunks = parse_hunks(diff_content)
    patched_lines = original_lines.copy()
    rejected_hunks = []
    offset = 0

    for hunk in hunks:
        old_start = hunk["old_start"] - 1 + offset
        old_lines = hunk["old_lines"]
        new_lines = []
        old_content = []

        for line in hunk["lines"]:
            if line.startswith("-"):
                old_content.append(line[1:])
            elif line.startswith("+"):
                new_lines.append(line[1:])
            elif line.startswith(" "):
                old_content.append(line[1:])
                new_lines.append(line[1:])

        applied = False
        for fuzz in range(fuzz_factor + 1):
            for direction in [0, -1, 1]:
                test_start = old_start + direction * fuzz
                if test_start < 0 or test_start >= len(patched_lines):
                    continue

                if _match_content(
                    patched_lines[test_start : test_start + len(old_content)],
                    old_content,
                    ignore_whitespace,
                ):
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


def save_rejected_hunks(reject_file: Path, rejected_hunks: list[dict[str, Any]]) -> None:
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


def calculate_file_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def _match_content(
    actual_lines: list[str], expected_lines: list[str], ignore_whitespace: bool
) -> bool:
    if len(actual_lines) != len(expected_lines):
        return False

    for actual, expected in zip(actual_lines, expected_lines, strict=True):
        if ignore_whitespace:
            if actual.strip() != expected.strip():
                return False
        elif actual != expected:
            return False

    return True
