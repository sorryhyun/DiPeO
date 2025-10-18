"""Prompt file management query resolvers."""

import logging
from pathlib import Path

from strawberry.scalars import JSON

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER
from dipeo.config import FILES_DIR
from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)


async def list_prompt_files(registry: ServiceRegistry) -> list[JSON]:
    """List available prompt files."""
    filesystem = registry.get(FILESYSTEM_ADAPTER)
    if not filesystem:
        return []

    prompts_dir = Path(FILES_DIR) / "prompts"
    if not filesystem.exists(prompts_dir):
        return []

    prompt_files = []
    valid_extensions = {".txt", ".md", ".csv", ".json", ".yaml"}

    for item in filesystem.listdir(prompts_dir):
        if item.suffix in valid_extensions:
            try:
                file_info = filesystem.stat(prompts_dir / item.name)
                prompt_files.append(
                    {
                        "name": item.name,
                        "path": str(item.relative_to(prompts_dir)),
                        "extension": item.suffix[1:],
                        "size": file_info.size,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to process prompt file {item}: {e}")

    return prompt_files


async def get_prompt_file(registry: ServiceRegistry, filename: str) -> JSON:
    """Get a specific prompt file."""
    filesystem = registry.get(FILESYSTEM_ADAPTER)
    if not filesystem:
        return {
            "success": False,
            "error": "Filesystem adapter not available",
            "filename": filename,
        }

    prompts_dir = Path(FILES_DIR) / "prompts"
    file_path = prompts_dir / filename

    if not filesystem.exists(file_path):
        return {
            "success": False,
            "error": f"Prompt file not found: {filename}",
            "filename": filename,
        }

    try:
        with filesystem.open(file_path, "rb") as f:
            raw_content = f.read()
            content = raw_content.decode("utf-8")

        file_info = filesystem.stat(file_path)

        return {
            "success": True,
            "filename": filename,
            "content": content,
            "raw_content": content,
            "extension": file_path.suffix[1:],
            "size": file_info.size,
        }
    except Exception as e:
        logger.error(f"Failed to read prompt file {filename}: {e}")
        return {
            "success": False,
            "error": f"Failed to read file: {e!s}",
            "filename": filename,
        }
