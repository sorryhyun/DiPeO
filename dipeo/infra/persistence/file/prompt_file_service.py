"""Prompt file operations service."""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PromptFileService:
    """Service for prompt-specific file operations."""
    
    def __init__(self, file_service, base_dir: Path | None = None):
        """Initialize with dependencies.
        
        Args:
            file_service: Core file service for basic operations
            base_dir: Base directory for operations
        """
        self.file_service = file_service
        self.base_dir = base_dir or Path.cwd()
        self.prompts_dir = self.base_dir / "prompts"
    
    async def list_prompt_files(self) -> list[dict[str, Any]]:
        """List all prompt files in the prompts directory.
        
        Returns:
            List of prompt file information
        """
        if not self.prompts_dir.exists():
            return []
        
        prompt_files = []
        valid_extensions = {'.txt', '.md', '.csv', '.json', '.yaml'}
        
        for file_path in self.prompts_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in valid_extensions:
                try:
                    relative_path = file_path.relative_to(self.prompts_dir)
                    prompt_files.append({
                        "name": file_path.name,
                        "path": str(relative_path),
                        "extension": file_path.suffix[1:],
                        "size": file_path.stat().st_size,
                    })
                except Exception as e:
                    logger.warning(f"Failed to process prompt file {file_path}: {e}")
        
        return prompt_files
    
    async def read_prompt_file(self, filename: str) -> dict[str, Any]:
        """Read a prompt file from the prompts directory.
        
        Args:
            filename: Name or relative path of the prompt file
            
        Returns:
            Dictionary with file content and metadata
        """
        file_path = self.prompts_dir / filename
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"Prompt file not found: {filename}",
                "filename": filename,
            }
        
        try:
            # Use file service to read
            result = self.file_service.read(str(file_path.relative_to(self.base_dir)))
            
            if result["success"]:
                return {
                    "success": True,
                    "filename": filename,
                    "content": result["content"],
                    "raw_content": result["raw_content"],
                    "extension": file_path.suffix[1:],
                    "size": file_path.stat().st_size,
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Failed to read file"),
                    "filename": filename,
                }
                
        except Exception as e:
            logger.error(f"Failed to read prompt file {filename}: {e}")
            return {
                "success": False,
                "error": str(e),
                "filename": filename,
            }
    
    async def save_prompt_file(
        self,
        filename: str,
        content: str,
        subdirectory: str | None = None
    ) -> dict[str, Any]:
        """Save a new prompt file.
        
        Args:
            filename: Name of the prompt file
            content: Content to save
            subdirectory: Optional subdirectory within prompts
            
        Returns:
            Dictionary with save result
        """
        # Determine target directory
        target_dir = self.prompts_dir
        if subdirectory:
            target_dir = target_dir / subdirectory
        
        # Ensure directory exists
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = target_dir / filename
        relative_path = file_path.relative_to(self.base_dir)
        
        result = await self.file_service.write(
            file_id=str(relative_path),
            content=content
        )
        
        if result["success"]:
            return {
                "success": True,
                "filename": filename,
                "path": str(relative_path),
                "size": len(content),
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to save file"),
                "filename": filename,
            }
    
    async def organize_prompts_by_category(self) -> dict[str, list[str]]:
        """Organize prompt files by their extension/category.
        
        Returns:
            Dictionary mapping categories to file lists
        """
        prompts = await self.list_prompt_files()
        
        organized = {}
        for prompt in prompts:
            category = prompt["extension"]
            if category not in organized:
                organized[category] = []
            organized[category].append(prompt["name"])
        
        return organized