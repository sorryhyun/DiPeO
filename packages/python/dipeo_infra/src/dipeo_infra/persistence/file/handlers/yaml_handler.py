"""YAML file format handler."""

from typing import Any
from pathlib import Path

import yaml
import aiofiles


class YamlHandler:
    """Handler for YAML files."""
    
    @property
    def supported_extensions(self) -> list[str]:
        """List of supported file extensions."""
        return [".yaml", ".yml", ".YAML", ".YML"]
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file."""
        return file_path.suffix.lower() in (".yaml", ".yml")
    
    def read(self, file_path: Path) -> tuple[Any, str]:
        """Read YAML file and return (parsed_content, raw_content)."""
        with open(file_path, encoding="utf-8") as f:
            content = yaml.safe_load(f)
            raw = yaml.dump(content, default_flow_style=False, allow_unicode=True)
            return content, raw
    
    async def write(self, file_path: Path, content: Any) -> None:
        """Write content to YAML file."""
        formatted = self.format_content(content)
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(formatted)
    
    def format_content(self, content: Any) -> str:
        """Format content as YAML string."""
        if isinstance(content, str):
            # If already a string, parse and re-format for consistency
            try:
                parsed = yaml.safe_load(content)
                return yaml.dump(
                    parsed,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )
            except yaml.YAMLError:
                # If not valid YAML, write as-is
                return content
        return yaml.dump(
            content,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )