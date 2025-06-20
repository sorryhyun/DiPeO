"""Consolidated services module."""
import json
import csv
import os
import uuid
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from docx import Document
import aiofiles
import io

from config import BASE_DIR, UPLOAD_DIR, RESULT_DIR, CONVERSATION_LOG_DIR
from .exceptions import APIKeyError, ValidationError, FileOperationError
from .base import BaseService
from .constants import VALID_LLM_SERVICES


class APIKeyService(BaseService):
    """Service for managing API keys."""
    
    # Include both LLM services and other external services
    VALID_SERVICES = VALID_LLM_SERVICES | {"notion"}
    
    def __init__(self, store_file: Optional[str] = None):
        super().__init__()
        self.store_file = store_file or os.getenv("API_KEY_STORE_FILE", f"{BASE_DIR}/files/apikeys.json")
        self._store: Dict[str, dict] = {}
        self._load_store()
    
    def _load_store(self) -> None:
        """Load API keys from disk storage."""
        if os.path.exists(self.store_file):
            try:
                with open(self.store_file, "r") as f:
                    self._store.update(json.load(f))
            except (json.JSONDecodeError, IOError) as e:
                raise APIKeyError(f"Failed to load API key store: {e}")
    
    def _save_store(self) -> None:
        """Save API keys to disk storage."""
        try:
            with open(self.store_file, "w") as f:
                json.dump(self._store, f, indent=2)
        except IOError as e:
            raise APIKeyError(f"Failed to save API key store: {e}")
    
    def _validate_service(self, service: str) -> None:
        """Validate service name."""
        normalized_service = self.normalize_service_name(service)
        if normalized_service not in self.VALID_SERVICES:
            raise ValidationError(f"Invalid service. Must be one of: {self.VALID_SERVICES}")
    
    def get_api_key(self, key_id: str) -> dict:
        """Get API key details by ID."""
        if key_id not in self._store:
            raise APIKeyError(f"API key '{key_id}' not found")
        
        info = self._store[key_id]
        # Ensure the returned format is consistent
        if isinstance(info, dict):
            return {
                "id": key_id,
                "label": info.get("label", key_id),
                "service": info.get("service", "unknown"),
                "key": info.get("key", "")
            }
        return info
    
    def list_api_keys(self) -> List[dict]:
        """List all stored API keys."""
        result = []
        for key_id, info in self._store.items():
            # Handle both old and new format API keys
            if isinstance(info, dict) and "service" in info:
                result.append({
                    "id": key_id,
                    "label": info.get("label", key_id),  # Use key_id as fallback name
                    "service": info["service"]
                })
        return result
    
    def create_api_key(self, label: str, service: str, key: str) -> dict:
        """Create a new API key entry."""
        self.validate_required_fields(
            {"label": label, "service": service, "key": key},
            ["label", "service", "key"]
        )
        
        self._validate_service(service)
        
        key_id = f"APIKEY_{uuid.uuid4().hex[:6].upper()}"
        normalized_service = self.normalize_service_name(service)
        
        self._store[key_id] = {
            "label": label,
            "service": normalized_service,
            "key": key
        }
        
        self._save_store()
        
        return {
            "id": key_id,
            "label": label,
            "service": normalized_service
        }
    
    def delete_api_key(self, key_id: str) -> None:
        """Delete an API key by ID."""
        if key_id not in self._store:
            raise APIKeyError(f"API key '{key_id}' not found")
        
        del self._store[key_id]
        self._save_store()
    
    def update_api_key(self, key_id: str, label: Optional[str] = None,
                      service: Optional[str] = None, key: Optional[str] = None) -> dict:
        """Update an existing API key."""
        if key_id not in self._store:
            raise APIKeyError(f"API key '{key_id}' not found")
        
        api_key_data = self._store[key_id].copy()
        
        if label is not None:
            api_key_data["label"] = label
        if service is not None:
            self._validate_service(service)
            api_key_data["service"] = self.normalize_service_name(service)
        if key is not None:
            api_key_data["key"] = key
        
        self._store[key_id] = api_key_data
        self._save_store()
        
        return {
            "id": key_id,
            "label": api_key_data["label"],
            "service": api_key_data["service"]
        }


class FileService(BaseService):
    """Unified file service for all file operations."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        super().__init__()
        self.base_dir = base_dir or Path.cwd()
        # Use directories from config.py instead of creating them
        self.upload_dir = UPLOAD_DIR
        self.result_dir = RESULT_DIR
        self.log_dir = CONVERSATION_LOG_DIR
    
    def read(self, 
             path: str, 
             relative_to: str = "base",
             encoding: str = "utf-8") -> Union[str, Dict[str, Any]]:
        """Read file with automatic format detection."""
        file_path = self._resolve_and_validate_path(path, relative_to)
        
        if not file_path.exists():
            raise FileOperationError(f"File not found: {path}")
        
        if file_path.suffix.lower() == '.docx':
            return self._read_docx(file_path)
        elif file_path.suffix.lower() == '.json':
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        elif file_path.suffix.lower() in ('.yaml', '.yml'):
            with open(file_path, 'r', encoding=encoding) as f:
                return yaml.safe_load(f)
        elif file_path.suffix.lower() == '.csv':
            return self._read_csv(file_path, encoding)
        else:
            return file_path.read_text(encoding=encoding)
    
    async def write(self,
              path: str,
              content: Any,
              relative_to: str = "",
              format: Optional[str] = None,
              encoding: str = "utf-8") -> str:
        """Write file with automatic format handling."""
        file_path = self._resolve_and_validate_path(path, relative_to, create_parents=True)
        
        if not format:
            suffix = file_path.suffix.lower()
            if suffix == '.json':
                format = 'json'
            elif suffix in ('.yaml', '.yml'):
                format = 'yaml'
            elif suffix == '.csv':
                format = 'csv'
            else:
                format = 'text'
        
        # Write based on format
        if format == 'json':
            await self._write_json(file_path, content, encoding)
        elif format == 'yaml':
            await self._write_yaml(file_path, content, encoding)
        elif format == 'csv':
            await self._write_csv(file_path, content, encoding)
        else:
            await self._write_text(file_path, content, encoding)
        
        # Return relative path from base directory
        return str(file_path.relative_to(self.base_dir))
    
    def _resolve_and_validate_path(self, 
                                   path: str, 
                                   relative_to: str,
                                   create_parents: bool = False) -> Path:
        """Resolve and validate path security."""
        base_map = {
            "base": self.base_dir,
            "uploads": self.upload_dir,
            "results": self.result_dir,
            "logs": self.log_dir
        }
        
        base_path = base_map.get(relative_to, self.base_dir)
        
        # Resolve the path
        if Path(path).is_absolute():
            resolved = Path(path).resolve()
        else:
            resolved = (base_path / path).resolve()
        
        # Validate it's within allowed directory
        try:
            resolved.relative_to(self.base_dir)
        except ValueError:
            raise ValidationError(f"Path outside allowed directory: {path}")
        
        # Create parent directories if requested
        if create_parents and not resolved.parent.exists():
            resolved.parent.mkdir(parents=True, exist_ok=True)
        
        return resolved
    
    def _read_docx(self, file_path: Path) -> str:
        """Read content from DOCX file."""
        doc = Document(str(file_path))
        return "\n".join([para.text for para in doc.paragraphs])
    
    def _read_csv(self, file_path: Path, encoding: str) -> List[Dict[str, Any]]:
        """Read CSV file and return as list of dictionaries."""
        with open(file_path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    async def _write_json(self, file_path: Path, content: Any, encoding: str):
        """Write content as formatted JSON."""
        async with aiofiles.open(file_path, 'w', encoding=encoding) as f:
            await f.write(json.dumps(content, indent=2, ensure_ascii=False))
    
    async def _write_yaml(self, file_path: Path, content: Any, encoding: str):
        """Write content as YAML."""
        yaml_content = yaml.dump(
            content,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            indent=2
        )
        async with aiofiles.open(file_path, 'w', encoding=encoding) as f:
            await f.write(yaml_content)
    
    async def _write_csv(self, file_path: Path, content: Any, encoding: str):
        """Write content as CSV."""
        if isinstance(content, dict):
            rows = [content]
        elif isinstance(content, list) and all(isinstance(r, dict) for r in content):
            rows = content
        else:
            raise ValidationError("CSV content must be a dict or list of dicts")
        
        if not rows:
            raise ValidationError("No data to write to CSV")
        
        # Get all unique keys
        all_keys = set()
        for row in rows:
            all_keys.update(row.keys())
        
        fieldnames = sorted(all_keys)
        
        async with aiofiles.open(file_path, 'w', encoding=encoding, newline='') as f:
            # Write CSV content as string
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            await f.write(output.getvalue())
    
    async def _write_text(self, file_path: Path, content: Any, encoding: str):
        """Write content as plain text."""
        text_content = str(content) if not isinstance(content, str) else content
        async with aiofiles.open(file_path, 'w', encoding=encoding) as f:
            await f.write(text_content)
    
    async def save_file(self, content: bytes, filename: str, target_path: Optional[str] = None) -> Dict[str, Any]:
        """Save uploaded file to the uploads directory."""
        if target_path:
            file_path = self._resolve_and_validate_path(
                os.path.join(target_path, filename), 
                "uploads", 
                create_parents=True
            )
        else:
            file_path = self._resolve_and_validate_path(
                filename, 
                "uploads", 
                create_parents=True
            )
        
        # Write file content
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        return {
            "path": str(file_path.relative_to(self.base_dir)),
            "size": len(content)
        }