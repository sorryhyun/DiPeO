"""Use case for loading prompts from files or inline content."""

import logging
import os
from pathlib import Path
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.config.paths import BASE_DIR

logger = get_module_logger(__name__)


class PromptLoadingUseCase:
    """Centralized use case for loading prompts from various sources.

    This use case handles:
    - Loading prompts from external files
    - Resolving prompt file paths (diagram-relative, base-relative, global)
    - Caching loaded prompts for performance
    """

    def __init__(self, filesystem_adapter: Any):
        """Initialize the prompt loading use case.

        Args:
            filesystem_adapter: Adapter for filesystem operations
        """
        self.filesystem = filesystem_adapter
        self._base_dir = str(BASE_DIR)
        self._prompt_cache: dict[str, str] = {}

    def load_prompt(
        self,
        prompt_file: str | None = None,
        inline_prompt: str | None = None,
        diagram_source_path: str | None = None,
        node_label: str | None = None,
    ) -> str | None:
        """Load prompt content from file or inline.

        Args:
            prompt_file: Path to external prompt file
            inline_prompt: Inline prompt content
            diagram_source_path: Path to the diagram source for relative resolution
            node_label: Optional node label for logging

        Returns:
            Prompt content as string, or None if not found
        """
        # Prefer inline prompt if provided
        if inline_prompt:
            return inline_prompt

        # Load from file if specified
        if prompt_file:
            return self.load_prompt_file(prompt_file, diagram_source_path, node_label)

        return None

    def load_prompt_file(
        self,
        prompt_filename: str,
        diagram_source_path: str | None = None,
        node_label: str | None = None,
    ) -> str | None:
        """Load prompt content from external file.

        Args:
            prompt_filename: Name of the prompt file
            diagram_source_path: Path to diagram source for relative resolution
            node_label: Optional node label for logging

        Returns:
            Prompt content as string, or None if file not found
        """
        if not self.filesystem:
            logger.error(
                f"[PromptLoadingUseCase] No filesystem adapter available! "
                f"Cannot load prompt file: {prompt_filename}"
            )
            return None

        if not prompt_filename:
            logger.warning("[PromptLoadingUseCase] No prompt filename provided")
            return None

        # Check cache first
        cache_key = (
            f"{diagram_source_path}:{prompt_filename}" if diagram_source_path else prompt_filename
        )
        if cache_key in self._prompt_cache:
            logger.debug(f"[PromptLoadingUseCase] Using cached prompt for: {cache_key}")
            return self._prompt_cache[cache_key]

        try:
            prompt_path = self._resolve_prompt_path(prompt_filename, diagram_source_path)

            if self.filesystem.exists(prompt_path):
                with self.filesystem.open(prompt_path, "rb") as f:
                    content = f.read().decode("utf-8")
                    # Cache the loaded content
                    self._prompt_cache[cache_key] = content
                    logger.debug(
                        f"[PromptLoadingUseCase] Loaded prompt from: {prompt_path} "
                        f"for node: {node_label or 'unknown'}"
                    )
                    return content
            else:
                logger.warning(
                    f"[PromptLoadingUseCase] Prompt file not found: {prompt_path} "
                    f"for node: {node_label or 'unknown'}"
                )
                return None

        except Exception as e:
            logger.error(f"Error loading prompt file {prompt_filename}: {e}")
            return None

    def _resolve_prompt_path(
        self, prompt_filename: str, diagram_source_path: str | None = None
    ) -> Path:
        """Resolve the full path to a prompt file.

        Resolution order:
        1. If path starts with 'projects/' or 'files/', treat as relative to base directory
        2. Relative to diagram directory (diagram_dir/prompts/filename)
        3. Global prompts directory (DIPEO_BASE_DIR/files/prompts/filename)

        Args:
            prompt_filename: Name of the prompt file
            diagram_source_path: Optional diagram source path for relative resolution

        Returns:
            Resolved path to the prompt file
        """
        # Check if path is already relative to base directory
        if prompt_filename.startswith(("projects/", "files/")):
            base_relative_path = Path(self._base_dir) / prompt_filename
            if self.filesystem.exists(base_relative_path):
                return base_relative_path

        # Try relative to diagram directory if diagram source path is provided
        if diagram_source_path:
            # Convert to absolute path if relative
            if not os.path.isabs(diagram_source_path):
                diagram_source_path = os.path.join(self._base_dir, diagram_source_path)

            if os.path.exists(diagram_source_path):
                diagram_dir = Path(diagram_source_path).parent
                local_path = diagram_dir / "prompts" / prompt_filename
                if self.filesystem.exists(local_path):
                    return local_path
                else:
                    logger.debug(
                        f"[PromptLoadingUseCase] Prompt not found at diagram-relative path: {local_path}"
                    )

        # Fall back to global prompts directory
        global_path = Path(self._base_dir) / "files" / "prompts" / prompt_filename
        logger.debug(
            f"[PromptLoadingUseCase] Falling back to global prompts directory: {global_path}"
        )
        return global_path

    def clear_cache(self):
        """Clear the prompt cache."""
        self._prompt_cache.clear()
        logger.debug("[PromptLoadingUseCase] Prompt cache cleared")

    def get_diagram_source_path(self, diagram: Any) -> str | None:
        """Extract diagram source path from diagram metadata.

        Args:
            diagram: The diagram object with metadata

        Returns:
            The diagram source path, or None if not found
        """
        if diagram and hasattr(diagram, "metadata") and diagram.metadata:
            # Try diagram_source_path first (set by PrepareDiagramForExecutionUseCase)
            source_path = diagram.metadata.get("diagram_source_path")

            # Fall back to diagram_id if diagram_source_path not found
            if not source_path:
                source_path = diagram.metadata.get("diagram_id")

            if source_path:
                return source_path

        logger.debug("[PromptLoadingUseCase] No source path found in diagram metadata")
        return None
