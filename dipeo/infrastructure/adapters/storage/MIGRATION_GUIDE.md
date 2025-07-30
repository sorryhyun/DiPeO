# Storage Adapter Migration Guide

This guide helps migrate from the old file service implementations to the new port-based storage adapters.

## Overview of Changes

### Old Structure
```
dipeo/infra/persistence/file/
├── base_file_service.py
├── file_operations_service.py
├── json_file_service.py
├── modular_file_service.py
├── prompt_file_service.py
└── async_adapter.py

dipeo/domain/file/services/
├── backup_service.py
└── file_business_logic.py
```

### New Structure
```
dipeo/domain/ports/
└── storage.py (Protocol definitions)

dipeo/infrastructure/adapters/storage/
├── local_adapter.py (LocalBlobAdapter, LocalFileSystemAdapter)
├── s3_adapter.py (S3Adapter)
└── artifact_adapter.py (ArtifactStoreAdapter)
```

## Migration Examples

### 1. Basic File Operations

**Old Code:**
```python
from dipeo.infra.persistence.file import BaseFileService

file_service = BaseFileService(base_dir="/data")
await file_service.initialize()

# Read file
result = file_service.read("config.json")
content = result["content"]

# Write file
await file_service.write("output.json", content=json_data)

# Check existence
exists = await file_service.file_exists("data.txt")
```

**New Code:**
```python
from dipeo.infrastructure.adapters.storage import LocalFileSystemAdapter

fs_adapter = LocalFileSystemAdapter(base_path="/data")
await fs_adapter.initialize()

# Read file
with fs_adapter.open(Path("config.json"), "r") as f:
    content = f.read()

# Write file
with fs_adapter.open(Path("output.json"), "w") as f:
    f.write(json_data)

# Check existence
exists = fs_adapter.exists(Path("data.txt"))
```

### 2. Blob Storage Operations

**Old Code:**
```python
# Storing versioned content (not directly supported)
await file_service.save_file(
    content=data_bytes,
    filename="model.pkl",
    create_backup=True
)
```

**New Code:**
```python
from dipeo.infrastructure.adapters.storage import LocalBlobAdapter

blob_adapter = LocalBlobAdapter(base_path="/data/blobs")
await blob_adapter.initialize()

# Store with automatic versioning
version_id = await blob_adapter.put("models/model.pkl", data_bytes)

# Retrieve specific version
data_io = await blob_adapter.get("models/model.pkl", version=version_id)
data = data_io.read()

# List objects
async for key in blob_adapter.list("models/"):
    print(key)
```

### 3. S3 Storage

**New Code (no old equivalent):**
```python
from dipeo.infrastructure.adapters.storage import S3Adapter

s3_adapter = S3Adapter(bucket="my-dipeo-bucket", region="us-west-2")
await s3_adapter.initialize()

# Store in S3
version_id = await s3_adapter.put("diagrams/workflow.json", diagram_data)

# Generate presigned URL
url = s3_adapter.presign_url("diagrams/workflow.json", expires_in=3600)
```

### 4. Artifact Management

**Old Code:**
```python
# Manual version management
backup_path = backup_service.create_backup_name(file_path)
await file_service.copy_file(file_path, backup_path)
```

**New Code:**
```python
from dipeo.infrastructure.adapters.storage import ArtifactStoreAdapter
from dipeo.domain.ports.storage import Artifact

artifact_store = ArtifactStoreAdapter(blob_store=blob_adapter)
await artifact_store.initialize()

# Push versioned artifact
artifact = Artifact(
    name="trained-model",
    version="v1.2.0",
    data=model_bytes,
    metadata={"accuracy": "0.95", "dataset": "production"}
)
ref = await artifact_store.push(artifact)

# Promote to production
await artifact_store.promote(ref, "prod")

# Get latest production version
latest = await artifact_store.get_latest("trained-model", stage="prod")
```

## Service Registration

### Old Registry Pattern
```python
from dipeo.domain.service_registry import get_domain_service_registry

registry = get_domain_service_registry()
file_service = registry.get_file_service()
```

### New Registry Pattern
```python
from dipeo.application.registry import ServiceRegistry, BLOB_STORE, FILE_SYSTEM

registry = ServiceRegistry()

# Register adapters
registry.register(BLOB_STORE, LocalBlobAdapter("/data/blobs"))
registry.register(FILE_SYSTEM, LocalFileSystemAdapter("/data"))

# Resolve when needed
blob_store = registry.resolve(BLOB_STORE)
fs = registry.resolve(FILE_SYSTEM)
```

## Migration Steps

1. **Identify Usage Patterns**
   - Simple file I/O → Use `FileSystemPort`
   - Versioned storage → Use `BlobStorePort`
   - Artifact management → Use `ArtifactStorePort`

2. **Update Service Registration**
   - Replace old file service registrations with new adapters
   - Update dependency injection to use new ports

3. **Refactor File Operations**
   - Replace `read()`/`write()` with `open()` and context managers
   - Use Path objects instead of strings
   - Handle binary mode explicitly

4. **Add Error Handling**
   - Catch `StorageError` instead of `FileOperationError` for storage operations
   - Handle specific storage scenarios (S3 permissions, local disk space, etc.)

## Benefits of Migration

1. **Clear Separation of Concerns**
   - Blob storage vs filesystem operations
   - Infrastructure adapters separate from domain logic

2. **Better Testability**
   - Mock protocols instead of concrete implementations
   - Easier to test with in-memory adapters

3. **Cloud-Ready**
   - S3 adapter for cloud deployments
   - Presigned URLs for direct client access

4. **Version Management**
   - Built-in versioning for blob storage
   - Artifact promotion workflows

## Common Patterns

### File Format Handling
```python
# Old: Format handlers were built into file service
content, raw = file_service.formats.read_file(path)

# New: Handle formats in application layer
with fs.open(path, "rb") as f:
    raw_content = f.read()
    
# Parse based on extension
if path.suffix == ".json":
    content = json.loads(raw_content)
elif path.suffix == ".yaml":
    content = yaml.safe_load(raw_content)
```

### Backup Management
```python
# Old: Built-in backup on write
await file_service.write(file_id, content, create_backup=True)

# New: Explicit backup using blob versioning
version_before = await blob_store.put(key, original_data)
version_after = await blob_store.put(key, new_data)
# Both versions are retained
```

### Directory Operations
```python
# Old: Mixed file/directory operations
files = await file_service.list_files(directory)

# New: Clear filesystem operations
for path in fs.listdir(Path(directory)):
    if path.is_file():
        info = fs.stat(path)
        print(f"{path.name}: {info.size} bytes")
```

## Testing

### Mock Implementations
```python
from dipeo.domain.ports.storage import BlobStorePort

class MockBlobStore(BlobStorePort):
    def __init__(self):
        self.storage = {}
    
    async def put(self, key: str, data: bytes | BinaryIO, metadata: dict[str, str] | None = None) -> str:
        version = f"v{len(self.storage.get(key, []))}"
        if key not in self.storage:
            self.storage[key] = []
        self.storage[key].append((version, data, metadata))
        return version
    
    # ... implement other methods
```

## Gradual Migration

For a gradual migration, you can create adapter wrappers:

```python
from dipeo.domain.ports.storage import FileSystemPort

class LegacyFileServiceAdapter(FileSystemPort):
    """Adapter to use old file service with new port interface."""
    
    def __init__(self, legacy_service):
        self.legacy = legacy_service
    
    def open(self, path: Path, mode: str = "r") -> BinaryIO:
        # Adapt old read() to new open()
        if "r" in mode:
            result = self.legacy.read(str(path))
            return io.BytesIO(result["raw_content"].encode())
        # ... handle write mode
```

This allows using old services while migrating to the new architecture gradually.