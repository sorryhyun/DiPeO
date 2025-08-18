"""Backward compatibility adapter for FileServicePort.

This adapter wraps the new domain storage ports to implement the old
FileServicePort interface, enabling gradual migration.
"""

import json
from pathlib import Path
from typing import Any, Optional

from dipeo.application.migration.compat_imports import FileServicePort
from dipeo.domain.ports.storage import BlobStorePort as BlobStorage, FileSystemPort


class FileServiceAdapter(FileServicePort):
    """Adapter implementing FileServicePort using new domain storage ports.
    
    This provides backward compatibility for code still using the old
    FileServicePort interface while the system migrates to domain ports.
    """
    
    def __init__(
        self,
        blob_storage: BlobStorage,
        file_system: FileSystemPort,
        base_dir: Optional[Path] = None,
    ):
        """Initialize file service adapter.
        
        Args:
            blob_storage: Domain blob storage port for content storage
            file_system: Domain file system port for file operations
            base_dir: Base directory for file operations
        """
        self._blob_storage = blob_storage
        self._file_system = file_system
        self._base_dir = base_dir or Path.cwd()
    
    def _make_namespace(
        self,
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> str:
        """Create namespace from person_id and directory."""
        parts = []
        if directory:
            parts.append(directory)
        if person_id:
            parts.append(f"persons/{person_id}")
        return "/".join(parts) if parts else "default"
    
    def read(
        self,
        file_id: str,
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> dict[str, Any]:
        """Read file synchronously (compatibility method).
        
        Note: This blocks on the async operation for backward compatibility.
        Consider migrating to async blob storage directly.
        """
        import asyncio
        
        namespace = self._make_namespace(person_id, directory)
        
        # Run async method in sync context
        loop = asyncio.new_event_loop()
        try:
            content = loop.run_until_complete(
                self._blob_storage.get(
                    key=file_id,
                    person_id=person_id,
                    namespace=namespace,
                )
            )
            
            # Try to parse as JSON for backward compatibility
            try:
                data = json.loads(content.decode("utf-8"))
                return {"content": data, "file_id": file_id, "status": "success"}
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Return raw content if not JSON
                return {"content": content, "file_id": file_id, "status": "success"}
                
        except Exception as e:
            return {"error": str(e), "file_id": file_id, "status": "error"}
        finally:
            loop.close()
    
    async def write(
        self,
        file_id: str,
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
        content: Optional[str] = None,
    ) -> dict[str, Any]:
        """Write file asynchronously."""
        if content is None:
            return {"error": "No content provided", "file_id": file_id, "status": "error"}
        
        namespace = self._make_namespace(person_id, directory)
        
        try:
            # Convert string content to bytes
            content_bytes = content.encode("utf-8") if isinstance(content, str) else content
            
            metadata = await self._blob_storage.put(
                key=file_id,
                content=content_bytes,
                person_id=person_id,
                namespace=namespace,
                metadata={"content_type": "application/json"},
            )
            
            return {
                "file_id": file_id,
                "size": metadata.size,
                "checksum": metadata.checksum,
                "status": "success",
            }
        except Exception as e:
            return {"error": str(e), "file_id": file_id, "status": "error"}
    
    async def save_file(
        self,
        content: bytes,
        filename: str,
        target_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """Save file with specific path."""
        try:
            if target_path:
                # Use file system for specific path operations
                full_path = self._base_dir / target_path / filename
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                with self._file_system.open(full_path, "wb") as f:
                    f.write(content)
                
                return {
                    "filename": filename,
                    "path": str(full_path),
                    "size": len(content),
                    "status": "success",
                }
            else:
                # Use blob storage for general storage
                metadata = await self._blob_storage.put(
                    key=filename,
                    content=content,
                    namespace="uploads",
                )
                
                return {
                    "filename": filename,
                    "size": metadata.size,
                    "checksum": metadata.checksum,
                    "status": "success",
                }
        except Exception as e:
            return {"error": str(e), "filename": filename, "status": "error"}