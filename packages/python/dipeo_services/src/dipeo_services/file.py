"""Simple file system implementation of the SupportsFile protocol."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from dipeo_core import SupportsFile


class SimpleFileService(SupportsFile):
    """File operations for local execution."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the file service.
        
        Args:
            base_dir: Base directory for file operations. Defaults to current directory.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _resolve_path(self, file_id: str, person_id: Optional[str] = None, directory: Optional[str] = None) -> Path:
        """Resolve the full file path based on parameters."""
        # Start with base directory
        path = self.base_dir
        
        # Add directory if specified
        if directory:
            path = path / directory
        
        # Add person-specific subdirectory if specified
        if person_id:
            path = path / f"person_{person_id}"
        
        # Ensure directory exists
        path.mkdir(parents=True, exist_ok=True)
        
        # Add filename
        return path / file_id
    
    def read(self, file_id: str, person_id: Optional[str] = None, directory: Optional[str] = None) -> Dict[str, Any]:
        """Read a file."""
        try:
            file_path = self._resolve_path(file_id, person_id, directory)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_id}",
                    "file_id": file_id,
                    "path": str(file_path)
                }
            
            # Read file content
            content = file_path.read_text(encoding="utf-8")
            
            # Try to parse as JSON if possible
            try:
                parsed_content = json.loads(content)
                is_json = True
            except json.JSONDecodeError:
                parsed_content = content
                is_json = False
            
            return {
                "success": True,
                "file_id": file_id,
                "path": str(file_path),
                "content": parsed_content,
                "raw_content": content,
                "is_json": is_json,
                "size": file_path.stat().st_size,
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_id": file_id
            }
    
    async def write(
        self,
        file_id: str,
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Write content to a file."""
        try:
            file_path = self._resolve_path(file_id, person_id, directory)
            
            # Backup existing file if it exists
            backup_path = None
            if file_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_suffix(f".{timestamp}.bak")
                backup_path.write_bytes(file_path.read_bytes())
            
            # Write content
            if content is None:
                content = ""
            
            # If content is a dict/list, serialize to JSON
            if isinstance(content, (dict, list)):
                content = json.dumps(content, indent=2, ensure_ascii=False)
            
            file_path.write_text(content, encoding="utf-8")
            
            return {
                "success": True,
                "file_id": file_id,
                "path": str(file_path),
                "size": len(content),
                "backup_path": str(backup_path) if backup_path else None,
                "created": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_id": file_id
            }
    
    async def save_file(
        self,
        content: bytes,
        filename: str,
        target_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save binary content to a file."""
        try:
            # Determine target directory
            if target_path:
                target_dir = self.base_dir / target_path
            else:
                target_dir = self.base_dir
            
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Full file path
            file_path = target_dir / filename
            
            # Backup if exists
            backup_path = None
            if file_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_suffix(f".{timestamp}.bak")
                backup_path.write_bytes(file_path.read_bytes())
            
            # Write binary content
            file_path.write_bytes(content)
            
            return {
                "success": True,
                "filename": filename,
                "path": str(file_path),
                "size": len(content),
                "backup_path": str(backup_path) if backup_path else None,
                "created": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }