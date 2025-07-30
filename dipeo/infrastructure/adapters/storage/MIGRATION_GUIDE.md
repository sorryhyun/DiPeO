# Storage Adapter Migration Guide

This guide helps migrate from the old file service implementations to the new port-based storage adapters.

## Migration Status

### ✅ Completed

- Service registrations in persistence containers
- DBOperationsAdapter migrated to FileSystemPort
- EndpointNodeHandler migrated to FileSystemPort
- FILESYSTEM_ADAPTER service key added to registry
- SubDiagramNodeHandler migrated (uses diagram_service instead of direct file access)
- GraphQL resolvers migrated (queries.py, mutations/upload.py)
- DiagramStorageAdapter implemented (replaced DiagramLoaderAdapter)
- Removed ModularFileService imports from all containers
- Updated all service registrations to remove file_service
- FileOperationError replaced with StorageError in server exceptions
- template_job handler migrated to use filesystem_adapter
- json_schema_validator handler migrated to use filesystem_adapter
- hook handler migrated to use filesystem_adapter
- code_job handler updated to include filesystem_adapter
- Removed old infra/persistence/file directory (ModularFileService, BaseFileService, etc.)
- Removed old domain/file/services directory (FileBusinessLogic, BackupService)
- Updated container configurations and exports

### 🚧 In Progress / TODO

#### ✅ Priority 1: Complete File Service Migration - COMPLETED

All file service migrations have been completed. The old file_service has been fully replaced with the new port-based storage adapters.

**What was migrated:**
- SubDiagramNodeHandler now uses diagram_service instead of direct file access
- GraphQL queries.py prompt file operations now use filesystem_adapter
- GraphQL mutations/upload.py file uploads now use filesystem_adapter  
- All ModularFileService imports removed from containers
- APIService updated to work without file_service (save_response method won't work)
- Service registrations updated to exclude file_service

#### ✅ Priority 2: Error Handling - COMPLETED

**What was migrated:**
- Removed FileOperationError import from server exceptions.py
- Added StorageError import to server exceptions.py
- FileOperationError is now only used in legacy file services that are being phased out

#### ✅ Priority 3: Service Wiring - COMPLETED

**What was migrated:**
- template_job handler now uses filesystem_adapter for reading templates and writing output
- json_schema_validator handler now uses filesystem_adapter for reading schema and data files
- hook handler now uses filesystem_adapter for file operations in file hooks
- code_job handler updated to include filesystem_adapter in services (minimal migration)
- All handlers properly request filesystem_adapter in their requires_services property

#### Priority 4: Integration Tests

- [ ] Update integration tests to use new storage adapters
- [ ] Add tests for error handling with StorageError
- [ ] Verify all handlers work with filesystem_adapter

#### Future Enhancements

- [ ] Migrate diagram storage to BlobStorePort for versioning
- [ ] Implement S3 adapter for cloud deployments
- [ ] Add artifact management for ML models

## Quick Decision Guide

### Which Storage Port to Use?

| Use Case                | Port                | Example            |
| ----------------------- | ------------------- | ------------------ |
| Config files, JSON data | `FileSystemPort`    | API keys, DB files |
| User uploads, outputs   | `FileSystemPort`    | Endpoint outputs   |
| Versioned diagrams      | `BlobStorePort`     | Diagram history    |
| ML models               | `ArtifactStorePort` | Model versions     |
| Temporary files         | `FileSystemPort`    | Processing cache   |
| S3 uploads              | `S3Adapter`         | Cloud storage      |

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

## Completed Migration Examples

### 1. DBOperationsAdapter (✅ COMPLETED)

**Migration Pattern:**

```python
# Old
def __init__(self, file_service: FileServicePort, ...):
    self.file_service = file_service

# New
def __init__(self, file_system: FileSystemPort, ...):
    self.file_system = file_system

# File operations updated
with self.file_system.open(file_path, "rb") as f:
    raw_content = f.read()
```

### 2. EndpointNodeHandler (✅ COMPLETED)

**Migration Pattern:**

```python
# Service requirement changed
@property
def requires_services(self) -> list[str]:
    return ["filesystem_adapter"]  # was "file_service"

# File writing updated
with filesystem_adapter.open(file_path, "wb") as f:
    f.write(content.encode('utf-8'))
```

## Future Migration Patterns

### Blob Storage for Versioning (TODO)

```python
# When you need version history
blob_adapter = LocalBlobAdapter(base_path="/data/blobs")
version_id = await blob_adapter.put("diagrams/workflow.json", data_bytes)

# Retrieve specific version
data_io = await blob_adapter.get("diagrams/workflow.json", version=version_id)
```

### S3 for Cloud Deployment (Future)

```python
# For cloud deployments
s3_adapter = S3Adapter(bucket="dipeo-bucket", region="us-west-2")
version_id = await s3_adapter.put("diagrams/workflow.json", diagram_data)
url = s3_adapter.presign_url("diagrams/workflow.json", expires_in=3600)
```

### Artifact Management (When Needed)

```python
# For ML models, trained artifacts, etc.
artifact = Artifact(
    name="trained-model",
    version="v1.2.0",
    data=model_bytes,
    metadata={"accuracy": "0.95"}
)
ref = await artifact_store.push(artifact)
await artifact_store.promote(ref, "prod")
```

## Service Registration (✅ COMPLETED)

### Updated Container Registration

```python
# In ServerPersistenceContainer
filesystem_adapter = providers.Singleton(_create_server_filesystem_adapter)
blob_adapter = providers.Singleton(_create_server_blob_adapter)
artifact_adapter = providers.Singleton(
    _create_server_artifact_adapter,
    blob_store=blob_adapter
)
```

### New Service Keys

```python
from dipeo.application.registry import FILESYSTEM_ADAPTER, BLOB_STORE, ARTIFACT_STORE

# Use in handlers/services
filesystem = registry.resolve(FILESYSTEM_ADAPTER)
blob_store = registry.resolve(BLOB_STORE)
```

## Remaining Migration Steps

### 1. **Error Handling Update (Priority 2)**

```python
# Old
from dipeo.core import FileOperationError
try:
    # file operation
except FileOperationError as e:
    # handle

# New
from dipeo.core import StorageError
try:
    # storage operation
except StorageError as e:
    # handle
```

### 2. **Diagram Storage Migration (Optional)**

Consider migrating to versioned storage:

```python
# Current: filesystem-based
diagram_loader = DiagramLoaderAdapter(file_service)

# Future: blob-based with versioning
diagram_loader = DiagramBlobAdapter(blob_store)
```

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

## Migration Patterns for Remaining Work

### Pattern 1: Service Resolution

```python
# In handlers requiring file operations
from dipeo.application.registry import FILESYSTEM_ADAPTER

filesystem = request.services.get("filesystem_adapter")
# or
filesystem = registry.resolve(FILESYSTEM_ADAPTER)
```

### Pattern 2: Path Handling

```python
# Always use Path objects
from pathlib import Path

file_path = Path(filename)
parent_dir = file_path.parent

# Check parent directory exists
if not filesystem.exists(parent_dir):
    filesystem.mkdir(parent_dir, parents=True)
```

### Pattern 3: File I/O with Context Managers

```python
# Reading
with filesystem.open(path, "rb") as f:
    content = f.read().decode('utf-8')

# Writing
with filesystem.open(path, "wb") as f:
    f.write(content.encode('utf-8'))
```

### Pattern 4: Format-Specific Handling

```python
# Handle different file formats in application layer
if path.suffix == ".json":
    content = json.dumps(data, indent=2)
elif path.suffix in [".yaml", ".yml"]:
    content = yaml.dump(data)
else:
    content = str(data)
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
