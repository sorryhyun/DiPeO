"""Prompt file resolution utility for PersonJob handler."""

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PromptFileResolver:
    """Resolves prompt file paths and loads prompt content."""

    def __init__(self, filesystem_adapter: Any, diagram: Any = None):
        self.filesystem = filesystem_adapter
        self.diagram = diagram
        self._base_dir = os.getenv("DIPEO_BASE_DIR", os.getcwd())
        self._diagram_source_path = self._resolve_diagram_source_path()

    def _resolve_diagram_source_path(self) -> Path | None:
        source_path = None

        if self.diagram and hasattr(self.diagram, "metadata") and self.diagram.metadata:
            source_path = self.diagram.metadata.get("diagram_source_path")

            if not source_path:
                source_path = self.diagram.metadata.get("diagram_id")

            logger.debug(f"[PromptResolver] Found source path in metadata: {source_path}")

        if source_path:
            if not os.path.isabs(source_path):
                source_path = os.path.join(self._base_dir, source_path)

            if os.path.exists(source_path):
                resolved_path = Path(source_path).parent
                logger.debug(f"[PromptResolver] Resolved diagram source path: {resolved_path}")
                return resolved_path
            else:
                logger.warning(f"[PromptResolver] Source path does not exist: {source_path}")
        else:
            logger.debug("[PromptResolver] No source path found in diagram metadata")
        return None

    def load_prompt_file(self, prompt_filename: str, node_label: str | None = None) -> str | None:
        """Load prompt content from file."""
        if not self.filesystem:
            logger.error(
                f"[PromptResolver] No filesystem adapter available! Cannot load prompt file: {prompt_filename}"
            )
            return None
        if not prompt_filename:
            logger.warning("[PromptResolver] No prompt filename provided")
            return None

        try:
            prompt_path = self._resolve_prompt_path(prompt_filename)

            if self.filesystem.exists(prompt_path):
                with self.filesystem.open(prompt_path, "rb") as f:
                    return f.read().decode("utf-8")
            else:
                logger.warning(
                    f"[PersonJob {node_label or 'unknown'}] Prompt file not found: {prompt_path}"
                )
                return None

        except Exception as e:
            logger.error(f"Error loading prompt file {prompt_filename}: {e}")
            return None

    def _resolve_prompt_path(self, prompt_filename: str) -> Path:
        if prompt_filename.startswith(("projects/", "files/")):
            base_relative_path = Path(self._base_dir) / prompt_filename
            if self.filesystem.exists(base_relative_path):
                logger.debug(
                    f"[PromptResolver] Found prompt at base-relative path: {base_relative_path}"
                )
                return base_relative_path

        if self._diagram_source_path:
            local_path = self._diagram_source_path / "prompts" / prompt_filename
            if self.filesystem.exists(local_path):
                logger.debug(
                    f"[PromptResolver] Found prompt at diagram-relative path: {local_path}"
                )
                return local_path
            else:
                logger.debug(
                    f"[PromptResolver] Prompt not found at diagram-relative path: {local_path}"
                )

        global_path = Path(self._base_dir) / "files" / "prompts" / prompt_filename
        logger.debug(f"[PromptResolver] Falling back to global prompts directory: {global_path}")
        return global_path
