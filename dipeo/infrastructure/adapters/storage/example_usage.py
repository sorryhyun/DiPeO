"""Example usage of the new storage adapters."""

import asyncio
import json
from pathlib import Path
from datetime import datetime

from dipeo.domain.ports.storage import Artifact
from dipeo.infrastructure.adapters.storage import (
    LocalBlobAdapter,
    LocalFileSystemAdapter,
    ArtifactStoreAdapter,
    S3Adapter,
)


async def filesystem_example():
    """Example using FileSystemPort for basic file operations."""
    print("\n=== FileSystem Adapter Example ===")
    
    # Initialize adapter
    fs = LocalFileSystemAdapter(base_path="/tmp/dipeo_example")
    await fs.initialize()
    
    # Create a directory
    fs.mkdir(Path("configs"))
    
    # Write a file
    config_data = {"model": "gpt-4.1-nano", "temperature": 0.7}
    config_path = Path("configs/llm_config.json")
    
    with fs.open(config_path, "w") as f:
        f.write(json.dumps(config_data, indent=2).encode())
    
    # Check if file exists
    if fs.exists(config_path):
        print(f"✓ Created {config_path}")
    
    # Get file info
    info = fs.stat(config_path)
    print(f"  Size: {info.size} bytes")
    print(f"  Modified: {info.modified}")
    
    # List directory
    print("\nDirectory contents:")
    for path in fs.listdir(Path("configs")):
        print(f"  - {path.name}")
    
    # Read the file
    with fs.open(config_path, "r") as f:
        loaded_config = json.loads(f.read().decode())
        print(f"\nLoaded config: {loaded_config}")


async def blob_storage_example():
    """Example using BlobStorePort for versioned storage."""
    print("\n=== Blob Storage Example ===")
    
    # Initialize adapter
    blob_store = LocalBlobAdapter(base_path="/tmp/dipeo_blobs")
    await blob_store.initialize()
    
    # Store versioned content
    diagram_v1 = {"nodes": ["A", "B"], "edges": [{"from": "A", "to": "B"}]}
    v1_id = await blob_store.put(
        "diagrams/workflow.json",
        json.dumps(diagram_v1).encode(),
        metadata={"author": "alice", "description": "Initial version"}
    )
    print(f"✓ Stored v1 with ID: {v1_id}")
    
    # Update and store new version
    diagram_v2 = {"nodes": ["A", "B", "C"], "edges": [{"from": "A", "to": "B"}, {"from": "B", "to": "C"}]}
    v2_id = await blob_store.put(
        "diagrams/workflow.json",
        json.dumps(diagram_v2).encode(),
        metadata={"author": "alice", "description": "Added node C"}
    )
    print(f"✓ Stored v2 with ID: {v2_id}")
    
    # Retrieve latest version
    latest_io = await blob_store.get("diagrams/workflow.json")
    latest_data = json.loads(latest_io.read().decode())
    print(f"\nLatest version: {latest_data}")
    
    # Retrieve specific version
    v1_io = await blob_store.get("diagrams/workflow.json", version=v1_id)
    v1_data = json.loads(v1_io.read().decode())
    print(f"Version 1: {v1_data}")
    
    # List all objects
    print("\nAll stored objects:")
    async for key in blob_store.list():
        print(f"  - {key}")


async def artifact_management_example():
    """Example using ArtifactStorePort for high-level artifact management."""
    print("\n=== Artifact Management Example ===")
    
    # Set up blob storage backend
    blob_store = LocalBlobAdapter(base_path="/tmp/dipeo_artifacts")
    await blob_store.initialize()
    
    # Initialize artifact store
    artifact_store = ArtifactStoreAdapter(blob_store)
    await artifact_store.initialize()
    
    # Create and push an artifact
    model_data = b"<serialized model data>"
    artifact = Artifact(
        name="sentiment-analyzer",
        version="1.0.0",
        data=model_data,
        metadata={
            "framework": "pytorch",
            "accuracy": "0.92",
            "training_date": datetime.now().isoformat()
        },
        tags=["nlp", "production-ready"]
    )
    
    ref = await artifact_store.push(artifact)
    print(f"✓ Pushed artifact: {ref.name}:{ref.version}")
    print(f"  URI: {ref.uri}")
    print(f"  Size: {ref.size} bytes")
    
    # Push another version
    artifact_v2 = Artifact(
        name="sentiment-analyzer",
        version="1.1.0",
        data=b"<improved model data>",
        metadata={
            "framework": "pytorch",
            "accuracy": "0.95",
            "training_date": datetime.now().isoformat(),
            "improvements": "Better handling of negations"
        },
        tags=["nlp", "experimental"]
    )
    
    ref_v2 = await artifact_store.push(artifact_v2)
    print(f"\n✓ Pushed new version: {ref_v2.name}:{ref_v2.version}")
    
    # List all versions
    print(f"\nAll versions of {artifact.name}:")
    versions = await artifact_store.list_versions("sentiment-analyzer")
    for v in versions:
        print(f"  - {v.version} (created: {v.created})")
    
    # Promote to production
    await artifact_store.promote(ref_v2, "prod")
    print(f"\n✓ Promoted {ref_v2.version} to production")
    
    # Get latest production version
    prod_version = await artifact_store.get_latest("sentiment-analyzer", stage="prod")
    if prod_version:
        print(f"\nCurrent production version: {prod_version.version}")
    
    # Find by tag
    print("\nArtifacts tagged with 'nlp':")
    nlp_artifacts = await artifact_store.find_by_tag("nlp")
    for a in nlp_artifacts:
        print(f"  - {a.name}:{a.version}")
    
    # Pull artifact to local path
    local_path = await artifact_store.pull(ref_v2)
    print(f"\n✓ Downloaded artifact to: {local_path}")


async def s3_example():
    """Example using S3 adapter (requires AWS credentials)."""
    print("\n=== S3 Adapter Example ===")
    print("Note: This example requires AWS credentials and a valid S3 bucket")
    
    try:
        # Initialize S3 adapter
        s3 = S3Adapter(bucket="dipeo-storage", region="us-west-2")
        await s3.initialize()
        
        # Store a diagram
        diagram_data = {"name": "cloud-workflow", "nodes": ["Lambda", "DynamoDB"]}
        version_id = await s3.put(
            "diagrams/cloud-workflow.json",
            json.dumps(diagram_data).encode(),
            metadata={"environment": "production"}
        )
        print(f"✓ Stored in S3 with version: {version_id}")
        
        # Generate presigned URL for direct access
        url = s3.presign_url("diagrams/cloud-workflow.json", expires_in=3600)
        print(f"\nPresigned URL (valid for 1 hour):")
        print(f"  {url}")
        
        # List objects
        print("\nObjects in S3:")
        async for key in s3.list("diagrams/", limit=10):
            print(f"  - {key}")
            
    except Exception as e:
        print(f"S3 example skipped: {e}")


async def main():
    """Run all examples."""
    print("Storage Adapter Examples")
    print("========================")
    
    await filesystem_example()
    await blob_storage_example()
    await artifact_management_example()
    
    # Uncomment to run S3 example (requires AWS setup)
    # await s3_example()
    
    print("\n✓ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())