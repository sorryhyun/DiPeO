"""Compile-time prompt file resolution for diagrams.

This module handles resolving prompt file references to their actual content
during diagram compilation, eliminating runtime filesystem I/O.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.config.paths import BASE_DIR
from dipeo.diagram_generated import DomainNode, NodeType

logger = get_module_logger(__name__)


def _try_project_files_path(
    filename: str, base_path: Path, diagram_dir: Path | None
) -> Path | None:
    """Try resolving paths starting with 'projects/' or 'files/'."""
    if filename.startswith(("projects/", "files/")):
        full_path = base_path / filename
        if full_path.exists():
            return full_path
    return None


def _try_diagram_dir_paths(filename: str, base_path: Path, diagram_dir: Path | None) -> Path | None:
    """Try resolving paths relative to diagram directory."""
    if not diagram_dir:
        return None

    for path_candidate in [
        diagram_dir / filename,
        diagram_dir / "prompts" / filename,
        diagram_dir / "prompts" / filename.replace("prompts/", "")
        if "prompts/" in filename
        else None,
    ]:
        if path_candidate and path_candidate.exists():
            return path_candidate
    return None


def _try_global_prompts(filename: str, base_path: Path, diagram_dir: Path | None) -> Path | None:
    """Try resolving from global prompts directory."""
    global_path = base_path / "files" / "prompts" / filename
    return global_path if global_path.exists() else None


def _try_absolute_path(filename: str, base_path: Path, diagram_dir: Path | None) -> Path | None:
    """Try resolving as absolute path."""
    abs_path = Path(filename)
    return abs_path if abs_path.is_absolute() and abs_path.exists() else None


PATH_RESOLVERS = [
    _try_project_files_path,
    _try_diagram_dir_paths,
    _try_global_prompts,
    _try_absolute_path,
]


class PromptFileCompiler:
    """Resolves prompt file references to actual content during compilation.

    This is a pure domain component that resolves prompt files at compile time,
    embedding the content directly into the node data. This eliminates runtime
    filesystem operations and infrastructure dependencies.
    """

    def __init__(self, base_dir: str | None = None, filesystem_reader: Any | None = None):
        self._base_dir = base_dir or str(BASE_DIR)
        self._filesystem_reader = filesystem_reader or self._default_file_reader
        self._resolved_cache: dict[str, str] = {}

    def _default_file_reader(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            raise

    def resolve_prompt_files(
        self, nodes: list[dict[str, Any]], diagram_path: str | None = None
    ) -> list[dict[str, Any]]:
        diagram_dir = None
        if diagram_path:
            if not os.path.isabs(diagram_path):
                diagram_path = os.path.join(self._base_dir, diagram_path)
            if os.path.exists(diagram_path):
                diagram_dir = Path(diagram_path).parent
            else:
                logger.warning(f"[PromptCompiler] diagram_path does not exist: {diagram_path}")

        for node in nodes:
            node_type = node.get("type", "")
            if node_type not in ["person_job", "PersonJob", NodeType.PERSON_JOB]:
                continue

            data = node.get("data", {})

            if data.get("prompt_file"):
                resolved_content = self._resolve_single_prompt(
                    data["prompt_file"], diagram_dir, node.get("label", node.get("id", "unknown"))
                )
                if resolved_content:
                    data["resolved_prompt"] = resolved_content

            if data.get("first_prompt_file"):
                resolved_content = self._resolve_single_prompt(
                    data["first_prompt_file"],
                    diagram_dir,
                    node.get("label", node.get("id", "unknown")),
                )
                if resolved_content:
                    data["resolved_first_prompt"] = resolved_content

        return nodes

    def _resolve_single_prompt(
        self, prompt_filename: str, diagram_dir: Path | None, node_label: str
    ) -> str | None:
        cache_key = f"{diagram_dir}:{prompt_filename}" if diagram_dir else prompt_filename
        if cache_key in self._resolved_cache:
            logger.debug(
                f"[PromptCompiler] Using cached prompt for {node_label}: {prompt_filename}"
            )
            return self._resolved_cache[cache_key]

        prompt_path = self._resolve_prompt_path(prompt_filename, diagram_dir)

        if prompt_path and prompt_path.exists():
            try:
                content = self._filesystem_reader(prompt_path)
                self._resolved_cache[cache_key] = content
                return content
            except Exception as e:
                logger.error(
                    f"[PromptCompiler] Error reading prompt file {prompt_path} for {node_label}: {e}"
                )
                return None
        else:
            logger.warning(
                f"[PromptCompiler] Prompt file not found for {node_label}: {prompt_filename}"
            )
            return None

    def _resolve_prompt_path(self, prompt_filename: str, diagram_dir: Path | None) -> Path | None:
        base_path = Path(self._base_dir)

        for resolver in PATH_RESOLVERS:
            if result := resolver(prompt_filename, base_path, diagram_dir):
                return result

        logger.debug(f"[PromptCompiler] No valid path found for {prompt_filename}")
        return None

    def compile_domain_nodes(
        self, domain_nodes: list[DomainNode], diagram_path: str | None = None
    ) -> list[DomainNode]:
        diagram_dir = None
        if diagram_path:
            if not os.path.isabs(diagram_path):
                diagram_path = os.path.join(self._base_dir, diagram_path)
            if os.path.exists(diagram_path):
                diagram_dir = Path(diagram_path).parent

        for node in domain_nodes:
            if node.type != NodeType.PERSON_JOB:
                continue

            if not node.data:
                continue

            if node.data.get("prompt_file"):
                resolved_content = self._resolve_single_prompt(
                    node.data["prompt_file"], diagram_dir, node.data.get("label", str(node.id))
                )
                if resolved_content:
                    node.data["resolved_prompt"] = resolved_content

            if node.data.get("first_prompt_file"):
                resolved_content = self._resolve_single_prompt(
                    node.data["first_prompt_file"],
                    diagram_dir,
                    node.data.get("label", str(node.id)),
                )
                if resolved_content:
                    node.data["resolved_first_prompt"] = resolved_content

        return domain_nodes
