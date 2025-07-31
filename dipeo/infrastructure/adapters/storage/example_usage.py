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
    DiagramStorageAdapter,
)


async def filesystem_example():
    print("\n=== FileSystem Adapter Example ===")
    
    fs = LocalFileSystemAdapter(base_path="/tmp/dipeo_example")
    await fs.initialize()
    
    fs.mkdir(Path("configs"))
    
    config_data = {"model": "gpt-4.1-nano", "temperature": 0.7}
    config_path = Path("configs/llm_config.json")
    
    with fs.open(config_path, "w") as f:
        f.write(json.dumps(config_data, indent=2).encode())
    
    if fs.exists(config_path):
        print(f"✓ Created {config_path}")
    
    info = fs.stat(config_path)
    print(f"  Size: {info.size} bytes")
    print(f"  Modified: {info.modified}")
    
    print("\nDirectory contents:")
    for path in fs.listdir(Path("configs")):
        print(f"  - {path.name}")
    
    with fs.open(config_path, "r") as f:
        loaded_config = json.loads(f.read().decode())
        print(f"\nLoaded config: {loaded_config}")


async def blob_storage_example():
    print("\n=== Blob Storage Example ===")
    
    blob_store = LocalBlobAdapter(base_path="/tmp/dipeo_blobs")
    await blob_store.initialize()
    
    diagram_v1 = {"nodes": ["A", "B"], "edges": [{"from": "A", "to": "B"}]}
    v1_id = await blob_store.put(
        "diagrams/workflow.json",
        json.dumps(diagram_v1).encode(),
        metadata={"author": "alice", "description": "Initial version"}
    )
    print(f"✓ Stored v1 with ID: {v1_id}")
    
    diagram_v2 = {"nodes": ["A", "B", "C"], "edges": [{"from": "A", "to": "B"}, {"from": "B", "to": "C"}]}
    v2_id = await blob_store.put(
        "diagrams/workflow.json",
        json.dumps(diagram_v2).encode(),
        metadata={"author": "alice", "description": "Added node C"}
    )
    print(f"✓ Stored v2 with ID: {v2_id}")
    
    latest_io = await blob_store.get("diagrams/workflow.json")
    latest_data = json.loads(latest_io.read().decode())
    print(f"\nLatest version: {latest_data}")
    
    v1_io = await blob_store.get("diagrams/workflow.json", version=v1_id)
    v1_data = json.loads(v1_io.read().decode())
    print(f"Version 1: {v1_data}")
    
    print("\nAll stored objects:")
    async for key in blob_store.list():
        print(f"  - {key}")


async def artifact_management_example():
    print("\n=== Artifact Management Example ===")
    
    blob_store = LocalBlobAdapter(base_path="/tmp/dipeo_artifacts")
    await blob_store.initialize()
    
    artifact_store = ArtifactStoreAdapter(blob_store)
    await artifact_store.initialize()
    
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
    
    print(f"\nAll versions of {artifact.name}:")
    versions = await artifact_store.list_versions("sentiment-analyzer")
    for v in versions:
        print(f"  - {v.version} (created: {v.created})")
    
    await artifact_store.promote(ref_v2, "prod")
    print(f"\n✓ Promoted {ref_v2.version} to production")
    
    prod_version = await artifact_store.get_latest("sentiment-analyzer", stage="prod")
    if prod_version:
        print(f"\nCurrent production version: {prod_version.version}")
    
    print("\nArtifacts tagged with 'nlp':")
    nlp_artifacts = await artifact_store.find_by_tag("nlp")
    for a in nlp_artifacts:
        print(f"  - {a.name}:{a.version}")
    
    local_path = await artifact_store.pull(ref_v2)
    print(f"\n✓ Downloaded artifact to: {local_path}")


async def diagram_storage_example():
    print("\n=== Diagram Storage Example ===")
    
    fs = LocalFileSystemAdapter(base_path="/tmp/dipeo_diagrams")
    await fs.initialize()
    
    diagram_storage = DiagramStorageAdapter(fs, "/tmp/dipeo_diagrams")
    await diagram_storage.initialize()
    
    native_content = json.dumps({
        "nodes": {
            "node_1": {
                "type": "person_job",
                "position": {"x": 100, "y": 200},
                "data": {"personId": "alice", "prompt": "Analyze data"}
            }
        },
        "arrows": {
            "arrow_1": {
                "source": "node_1",
                "target": "output",
                "data": {"label": "results"}
            }
        }
    }, indent=2)
    
    info = await diagram_storage.save_diagram("analysis_workflow", native_content, "native")
    print(f"✓ Saved native format diagram: {info.path}")
    print(f"  Format: {info.format}")
    print(f"  Size: {info.size} bytes")
    
    light_content = """version: light
nodes:
  - id: start
    type: person_job
    personId: bob
    prompt: Generate report
connections:
  - from: start
    to: review
    label: draft
persons:
  - id: bob
    name: Bob Smith
    role: Analyst"""
    
    info2 = await diagram_storage.save_diagram("report_workflow", light_content, "light")
    print(f"\n✓ Saved light format diagram: {info2.path}")
    
    readable_content = """format: readable
title: Data Processing Pipeline
nodes:
  - Collect user feedback
  - Analyze sentiment
  - Generate insights
flow:
  - Collect user feedback -> Analyze sentiment: raw feedback
  - Analyze sentiment -> Generate insights: sentiment scores"""
    
    info3 = await diagram_storage.save_diagram("feedback_pipeline", readable_content, "readable")
    print(f"✓ Saved readable format diagram: {info3.path}")
    
    print("\nAll stored diagrams:")
    diagrams = await diagram_storage.list_diagrams()
    for diag in diagrams:
        print(f"  - {diag.id} ({diag.format}) - {diag.path}")
    
    content, format = await diagram_storage.load_diagram("analysis_workflow")
    print(f"\nLoaded analysis_workflow:")
    print(f"  Format: {format}")
    print(f"  Content preview: {content[:100]}...")
    
    print("\nConverting report_workflow from light to native format...")
    converted_info = await diagram_storage.convert_format("report_workflow", "native")
    print(f"✓ Converted to: {converted_info.path}")
    
    exists = await diagram_storage.exists("feedback_pipeline")
    print(f"\nDoes feedback_pipeline exist? {exists}")
    
    info = await diagram_storage.get_info("feedback_pipeline")
    if info:
        print(f"Feedback pipeline info:")
        print(f"  Modified: {info.modified}")
        print(f"  Size: {info.size} bytes")


async def s3_example():
    print("\n=== S3 Adapter Example ===")
    print("Note: This example requires AWS credentials and a valid S3 bucket")
    
    try:
        s3 = S3Adapter(bucket="dipeo-storage", region="us-west-2")
        await s3.initialize()
        
        diagram_data = {"name": "cloud-workflow", "nodes": ["Lambda", "DynamoDB"]}
        version_id = await s3.put(
            "diagrams/cloud-workflow.json",
            json.dumps(diagram_data).encode(),
            metadata={"environment": "production"}
        )
        print(f"✓ Stored in S3 with version: {version_id}")
        
        url = s3.presign_url("diagrams/cloud-workflow.json", expires_in=3600)
        print(f"\nPresigned URL (valid for 1 hour):")
        print(f"  {url}")
        
        print("\nObjects in S3:")
        async for key in s3.list("diagrams/", limit=10):
            print(f"  - {key}")
            
    except Exception as e:
        print(f"S3 example skipped: {e}")


async def main():
    print("Storage Adapter Examples")
    print("========================")
    
    await filesystem_example()
    await blob_storage_example()
    await artifact_management_example()
    await diagram_storage_example()
    
    # await s3_example()
    
    print("\n✓ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())