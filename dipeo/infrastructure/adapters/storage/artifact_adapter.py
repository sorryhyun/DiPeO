"""Artifact store adapter implementing ArtifactStorePort."""

import json
import logging
import tempfile
from typing import BinaryIO
from pathlib import Path
from datetime import datetime, timezone

from dipeo.domain.ports.storage import (
    ArtifactStorePort, 
    BlobStorePort,
    Artifact, 
    ArtifactRef
)
from dipeo.core import BaseService, StorageError

logger = logging.getLogger(__name__)


class ArtifactStoreAdapter(BaseService, ArtifactStorePort):
    """High-level artifact management built on BlobStorePort."""
    
    def __init__(self, blob_store: BlobStorePort, metadata_prefix: str = ".metadata"):
        """Initialize artifact store.
        
        Args:
            blob_store: Underlying blob storage implementation
            metadata_prefix: Prefix for metadata objects
        """
        super().__init__()
        self.blob_store = blob_store
        self.metadata_prefix = metadata_prefix
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize artifact store."""
        if self._initialized:
            return
            
        # Ensure blob store is initialized
        if hasattr(self.blob_store, 'initialize'):
            await self.blob_store.initialize()
            
        self._initialized = True
        logger.info("ArtifactStoreAdapter initialized")
    
    def _artifact_key(self, name: str, version: str) -> str:
        """Generate blob key for artifact."""
        return f"artifacts/{name}/{version}/data"
    
    def _metadata_key(self, name: str, version: str) -> str:
        """Generate blob key for artifact metadata."""
        return f"{self.metadata_prefix}/artifacts/{name}/{version}/metadata.json"
    
    def _manifest_key(self, name: str) -> str:
        """Generate blob key for artifact manifest."""
        return f"{self.metadata_prefix}/artifacts/{name}/manifest.json"
    
    async def _save_metadata(self, ref: ArtifactRef) -> None:
        """Save artifact metadata."""
        metadata = {
            "name": ref.name,
            "version": ref.version,
            "uri": ref.uri,
            "size": ref.size,
            "created": ref.created.isoformat(),
            "metadata": ref.metadata
        }
        
        metadata_bytes = json.dumps(metadata, indent=2).encode('utf-8')
        await self.blob_store.put(
            self._metadata_key(ref.name, ref.version),
            metadata_bytes
        )
    
    async def _load_metadata(self, name: str, version: str) -> ArtifactRef | None:
        """Load artifact metadata."""
        try:
            data_io = await self.blob_store.get(self._metadata_key(name, version))
            data = json.loads(data_io.read().decode('utf-8'))
            
            return ArtifactRef(
                name=data["name"],
                version=data["version"],
                uri=data["uri"],
                size=data["size"],
                created=datetime.fromisoformat(data["created"]),
                metadata=data["metadata"]
            )
        except Exception:
            return None
    
    async def _update_manifest(self, ref: ArtifactRef, stage: str | None = None) -> None:
        """Update artifact manifest with version info."""
        manifest_key = self._manifest_key(ref.name)
        
        # Load existing manifest
        try:
            manifest_io = await self.blob_store.get(manifest_key)
            manifest = json.loads(manifest_io.read().decode('utf-8'))
        except:
            manifest = {
                "name": ref.name,
                "versions": [],
                "latest": None,
                "stages": {}
            }
        
        # Add version if not exists
        version_entry = {
            "version": ref.version,
            "created": ref.created.isoformat(),
            "size": ref.size
        }
        
        if version_entry not in manifest["versions"]:
            manifest["versions"].append(version_entry)
            manifest["versions"].sort(key=lambda v: v["created"], reverse=True)
        
        # Update latest
        manifest["latest"] = manifest["versions"][0]["version"]
        
        # Update stage if provided
        if stage:
            manifest["stages"][stage] = ref.version
        
        # Save manifest
        manifest_bytes = json.dumps(manifest, indent=2).encode('utf-8')
        await self.blob_store.put(manifest_key, manifest_bytes)
    
    async def push(self, artifact: Artifact) -> ArtifactRef:
        """Store versioned artifact."""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Generate artifact key
            artifact_key = self._artifact_key(artifact.name, artifact.version)
            
            # Store artifact data
            version_id = await self.blob_store.put(
                artifact_key,
                artifact.data,
                artifact.metadata
            )
            
            # Determine size
            if isinstance(artifact.data, bytes):
                size = len(artifact.data)
            else:
                # For file-like objects, seek to end to get size
                artifact.data.seek(0, 2)
                size = artifact.data.tell()
                artifact.data.seek(0)
            
            # Create artifact reference
            ref = ArtifactRef(
                name=artifact.name,
                version=artifact.version,
                uri=artifact_key,
                size=size,
                created=datetime.now(timezone.utc),
                metadata=artifact.metadata
            )
            
            # Save metadata
            await self._save_metadata(ref)
            
            # Update manifest
            await self._update_manifest(ref)
            
            logger.info(f"Pushed artifact {artifact.name}:{artifact.version}")
            return ref
            
        except Exception as e:
            raise StorageError(f"Failed to push artifact {artifact.name}:{artifact.version}: {e}")
    
    async def pull(self, ref: ArtifactRef) -> Path:
        """Retrieve artifact to local path."""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            local_path = Path(temp_dir) / f"{ref.name}-{ref.version}"
            
            # Download artifact
            data_io = await self.blob_store.get(ref.uri)
            
            # Write to local file
            with open(local_path, 'wb') as f:
                f.write(data_io.read())
            
            logger.info(f"Pulled artifact {ref.name}:{ref.version} to {local_path}")
            return local_path
            
        except Exception as e:
            raise StorageError(f"Failed to pull artifact {ref.name}:{ref.version}: {e}")
    
    async def list_versions(self, name: str) -> list[ArtifactRef]:
        """List all versions of an artifact."""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Load manifest
            manifest_io = await self.blob_store.get(self._manifest_key(name))
            manifest = json.loads(manifest_io.read().decode('utf-8'))
            
            # Load metadata for each version
            refs = []
            for version_info in manifest["versions"]:
                ref = await self._load_metadata(name, version_info["version"])
                if ref:
                    refs.append(ref)
            
            return refs
            
        except Exception as e:
            logger.warning(f"Failed to list versions for {name}: {e}")
            return []
    
    async def promote(self, ref: ArtifactRef, stage: str) -> None:
        """Promote artifact to stage."""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Validate stage
            valid_stages = ["dev", "staging", "prod", "latest"]
            if stage not in valid_stages:
                raise ValueError(f"Invalid stage: {stage}. Must be one of {valid_stages}")
            
            # Update manifest with stage
            await self._update_manifest(ref, stage)
            
            # Update metadata with promotion info
            ref.metadata[f"promoted_to_{stage}"] = datetime.now(timezone.utc).isoformat()
            await self._save_metadata(ref)
            
            logger.info(f"Promoted {ref.name}:{ref.version} to {stage}")
            
        except Exception as e:
            raise StorageError(f"Failed to promote artifact: {e}")
    
    async def tag(self, ref: ArtifactRef, tags: list[str]) -> None:
        """Add tags to artifact."""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Load current metadata
            current = await self._load_metadata(ref.name, ref.version)
            if not current:
                raise StorageError(f"Artifact not found: {ref.name}:{ref.version}")
            
            # Update tags
            existing_tags = current.metadata.get("tags", [])
            all_tags = list(set(existing_tags + tags))
            current.metadata["tags"] = all_tags
            
            # Save updated metadata
            await self._save_metadata(current)
            
            logger.info(f"Tagged {ref.name}:{ref.version} with {tags}")
            
        except Exception as e:
            raise StorageError(f"Failed to tag artifact: {e}")
    
    async def find_by_tag(self, tag: str) -> list[ArtifactRef]:
        """Find artifacts by tag."""
        if not self._initialized:
            await self.initialize()
            
        results = []
        
        try:
            # List all metadata files
            async for key in self.blob_store.list(f"{self.metadata_prefix}/artifacts/"):
                if key.endswith("/metadata.json"):
                    # Load metadata
                    data_io = await self.blob_store.get(key)
                    data = json.loads(data_io.read().decode('utf-8'))
                    
                    # Check tags
                    if tag in data.get("metadata", {}).get("tags", []):
                        ref = ArtifactRef(
                            name=data["name"],
                            version=data["version"],
                            uri=data["uri"],
                            size=data["size"],
                            created=datetime.fromisoformat(data["created"]),
                            metadata=data["metadata"]
                        )
                        results.append(ref)
            
            return results
            
        except Exception as e:
            logger.warning(f"Failed to find artifacts by tag {tag}: {e}")
            return []
    
    async def get_latest(self, name: str, stage: str | None = None) -> ArtifactRef | None:
        """Get latest version of an artifact."""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Load manifest
            manifest_io = await self.blob_store.get(self._manifest_key(name))
            manifest = json.loads(manifest_io.read().decode('utf-8'))
            
            # Get version based on stage
            if stage and stage in manifest.get("stages", {}):
                version = manifest["stages"][stage]
            else:
                version = manifest.get("latest")
            
            if not version:
                return None
            
            # Load metadata for version
            return await self._load_metadata(name, version)
            
        except Exception as e:
            logger.warning(f"Failed to get latest version of {name}: {e}")
            return None