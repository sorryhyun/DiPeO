"""Artifact store adapter implementing ArtifactStorePort."""

import json
import logging
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from dipeo.domain.base import StorageError
from dipeo.domain.base.mixins import InitializationMixin, LoggingMixin
from dipeo.domain.base.storage_port import Artifact, ArtifactRef, ArtifactStorePort, BlobStorePort

logger = logging.getLogger(__name__)


class ArtifactStoreAdapter(LoggingMixin, InitializationMixin, ArtifactStorePort):
    """High-level artifact management built on BlobStorePort."""

    def __init__(self, blob_store: BlobStorePort, metadata_prefix: str = ".metadata"):
        # Initialize mixins
        InitializationMixin.__init__(self)
        self.blob_store = blob_store
        self.metadata_prefix = metadata_prefix
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return

        if hasattr(self.blob_store, "initialize"):
            await self.blob_store.initialize()

        self._initialized = True
        logger.info("ArtifactStoreAdapter initialized")

    def _artifact_key(self, name: str, version: str) -> str:
        return f"artifacts/{name}/{version}/data"

    def _metadata_key(self, name: str, version: str) -> str:
        return f"{self.metadata_prefix}/artifacts/{name}/{version}/metadata.json"

    def _manifest_key(self, name: str) -> str:
        return f"{self.metadata_prefix}/artifacts/{name}/manifest.json"

    async def _save_metadata(self, ref: ArtifactRef) -> None:
        metadata = {
            "name": ref.name,
            "version": ref.version,
            "uri": ref.uri,
            "size": ref.size,
            "created": ref.created.isoformat(),
            "metadata": ref.metadata,
        }

        metadata_bytes = json.dumps(metadata, indent=2).encode("utf-8")
        await self.blob_store.put(self._metadata_key(ref.name, ref.version), metadata_bytes)

    async def _load_metadata(self, name: str, version: str) -> ArtifactRef | None:
        try:
            data_io = await self.blob_store.get(self._metadata_key(name, version))
            data = json.loads(data_io.read().decode("utf-8"))

            return ArtifactRef(
                name=data["name"],
                version=data["version"],
                uri=data["uri"],
                size=data["size"],
                created=datetime.fromisoformat(data["created"]),
                metadata=data["metadata"],
            )
        except Exception:
            return None

    async def _update_manifest(self, ref: ArtifactRef, stage: str | None = None) -> None:
        manifest_key = self._manifest_key(ref.name)

        try:
            manifest_io = await self.blob_store.get(manifest_key)
            manifest = json.loads(manifest_io.read().decode("utf-8"))
        except:
            manifest = {"name": ref.name, "versions": [], "latest": None, "stages": {}}

        version_entry = {
            "version": ref.version,
            "created": ref.created.isoformat(),
            "size": ref.size,
        }

        if version_entry not in manifest["versions"]:
            manifest["versions"].append(version_entry)
            manifest["versions"].sort(key=lambda v: v["created"], reverse=True)

        manifest["latest"] = manifest["versions"][0]["version"]

        if stage:
            manifest["stages"][stage] = ref.version

        manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
        await self.blob_store.put(manifest_key, manifest_bytes)

    async def push(self, artifact: Artifact) -> ArtifactRef:
        if not self._initialized:
            await self.initialize()

        try:
            artifact_key = self._artifact_key(artifact.name, artifact.version)

            version_id = await self.blob_store.put(artifact_key, artifact.data, artifact.metadata)

            if isinstance(artifact.data, bytes):
                size = len(artifact.data)
            else:
                artifact.data.seek(0, 2)
                size = artifact.data.tell()
                artifact.data.seek(0)

            ref = ArtifactRef(
                name=artifact.name,
                version=artifact.version,
                uri=artifact_key,
                size=size,
                created=datetime.now(UTC),
                metadata=artifact.metadata,
            )

            await self._save_metadata(ref)

            await self._update_manifest(ref)

            logger.info(f"Pushed artifact {artifact.name}:{artifact.version}")
            return ref

        except Exception as e:
            raise StorageError(f"Failed to push artifact {artifact.name}:{artifact.version}: {e}")

    async def pull(self, ref: ArtifactRef) -> Path:
        if not self._initialized:
            await self.initialize()

        try:
            temp_dir = tempfile.mkdtemp()
            local_path = Path(temp_dir) / f"{ref.name}-{ref.version}"

            data_io = await self.blob_store.get(ref.uri)

            with open(local_path, "wb") as f:
                f.write(data_io.read())

            logger.info(f"Pulled artifact {ref.name}:{ref.version} to {local_path}")
            return local_path

        except Exception as e:
            raise StorageError(f"Failed to pull artifact {ref.name}:{ref.version}: {e}")

    async def list_versions(self, name: str) -> list[ArtifactRef]:
        if not self._initialized:
            await self.initialize()

        try:
            manifest_io = await self.blob_store.get(self._manifest_key(name))
            manifest = json.loads(manifest_io.read().decode("utf-8"))

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
        if not self._initialized:
            await self.initialize()

        try:
            valid_stages = ["dev", "staging", "prod", "latest"]
            if stage not in valid_stages:
                raise ValueError(f"Invalid stage: {stage}. Must be one of {valid_stages}")

            await self._update_manifest(ref, stage)

            ref.metadata[f"promoted_to_{stage}"] = datetime.now(UTC).isoformat()
            await self._save_metadata(ref)

            logger.info(f"Promoted {ref.name}:{ref.version} to {stage}")

        except Exception as e:
            raise StorageError(f"Failed to promote artifact: {e}")

    async def tag(self, ref: ArtifactRef, tags: list[str]) -> None:
        if not self._initialized:
            await self.initialize()

        try:
            current = await self._load_metadata(ref.name, ref.version)
            if not current:
                raise StorageError(f"Artifact not found: {ref.name}:{ref.version}")

            existing_tags = current.metadata.get("tags", [])
            all_tags = list(set(existing_tags + tags))
            current.metadata["tags"] = all_tags

            await self._save_metadata(current)

            logger.info(f"Tagged {ref.name}:{ref.version} with {tags}")

        except Exception as e:
            raise StorageError(f"Failed to tag artifact: {e}")

    async def find_by_tag(self, tag: str) -> list[ArtifactRef]:
        if not self._initialized:
            await self.initialize()

        results = []

        try:
            async for key in self.blob_store.list(f"{self.metadata_prefix}/artifacts/"):
                if key.endswith("/metadata.json"):
                    data_io = await self.blob_store.get(key)
                    data = json.loads(data_io.read().decode("utf-8"))

                    if tag in data.get("metadata", {}).get("tags", []):
                        ref = ArtifactRef(
                            name=data["name"],
                            version=data["version"],
                            uri=data["uri"],
                            size=data["size"],
                            created=datetime.fromisoformat(data["created"]),
                            metadata=data["metadata"],
                        )
                        results.append(ref)

            return results

        except Exception as e:
            logger.warning(f"Failed to find artifacts by tag {tag}: {e}")
            return []

    async def get_latest(self, name: str, stage: str | None = None) -> ArtifactRef | None:
        if not self._initialized:
            await self.initialize()

        try:
            manifest_io = await self.blob_store.get(self._manifest_key(name))
            manifest = json.loads(manifest_io.read().decode("utf-8"))

            if stage and stage in manifest.get("stages", {}):
                version = manifest["stages"][stage]
            else:
                version = manifest.get("latest")

            if not version:
                return None

            return await self._load_metadata(name, version)

        except Exception as e:
            logger.warning(f"Failed to get latest version of {name}: {e}")
            return None
