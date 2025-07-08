# Domain Services Refactoring Summary

## Overview

This refactoring separates I/O operations from business logic following hexagonal architecture principles. Each original service has been split into:

1. **Domain Service** - Contains only business logic (validation, transformation, calculations)
2. **Infrastructure Service** - Handles all I/O operations (file system, HTTP calls, etc.)

## Refactored Services

### 1. DiagramFileRepository → DiagramDomainService + DiagramFileRepository

**Domain Service** (`dipeo/domain/services/diagram/diagram_service.py`):
- `validate_diagram_data()` - Validates diagram structure
- `clean_enum_values()` - Transforms enum values to strings
- `determine_format_type()` - Determines format from path
- `generate_file_info()` - Creates file metadata
- `construct_search_paths()` - Generates search paths for diagram lookup
- `transform_diagram_for_export()` - Transforms diagram based on target format

**Infrastructure Service** (`dipeo/infra/persistence/diagram/file_repository.py`):
- `read_file()` - Reads diagram from filesystem
- `write_file()` - Writes diagram to filesystem
- `delete_file()` - Deletes diagram file
- `list_files()` - Lists diagram files
- `exists()` - Checks if file exists
- `find_by_id()` - Finds diagram by ID

### 2. FileOperationsDomainService → FileDomainService + FileRepository

**Domain Service** (`dipeo/domain/services/file/file_domain_service.py`):
- `validate_file_size()` - Validates file size limits
- `validate_file_extension()` - Validates allowed extensions
- `create_backup_filename()` - Generates backup filename
- `format_log_entry()` - Formats log entries with timestamps
- `parse_json_safe()` - Parses JSON with validation
- `format_json_pretty()` - Formats JSON for output
- `filter_files_by_criteria()` - Filters file lists
- `calculate_checksum()` - Calculates MD5 checksums
- `validate_copy_operation()` - Validates copy parameters

**Infrastructure Service** (`dipeo/infra/persistence/file/file_repository.py`):
- `FileRepository` - Low-level file I/O operations
  - `aread()` - Async file read
  - `write()` - Async file write
  - `exists()` - Check file existence
  - `size()` - Get file size
  - `list()` - List directory contents
  - `delete()` - Delete file
- `FileOperationsService` - Higher-level operations combining domain + infrastructure

### 3. APIIntegrationDomainService → APIDomainService + APIClient

**Domain Service** (`dipeo/domain/services/api/api_domain_service.py`):
- `validate_api_response()` - Validates response status codes
- `should_retry()` - Determines retry logic
- `calculate_retry_delay()` - Calculates exponential backoff
- `substitute_variables()` - Variable substitution in templates
- `evaluate_condition()` - Evaluates workflow conditions
- `validate_workflow_step()` - Validates workflow configuration
- `format_api_response()` - Formats responses for storage
- `extract_rate_limit_info()` - Extracts rate limit headers
- `build_request_config()` - Builds request configuration

**Infrastructure Service** (`dipeo/infra/http/api_client.py`):
- `APIClient` - Low-level HTTP operations
  - `execute_request()` - Single HTTP request execution
  - `_ensure_session()` - Session management
- `APIService` - Higher-level operations combining domain + infrastructure
  - `execute_with_retry()` - API calls with retry logic
  - `execute_workflow()` - Multi-step API workflows

## Key Design Principles

1. **Pure Functions in Domain Services**
   - No I/O operations (file system, network, database)
   - All data passed as parameters
   - Return transformed/validated data
   - Can be easily unit tested

2. **Infrastructure Services Handle I/O**
   - All file system operations
   - All HTTP/network calls
   - Delegate business logic to domain services
   - Can be mocked for testing

3. **Dependency Injection**
   - Infrastructure services receive domain services via constructor
   - Allows easy testing and swapping implementations

4. **Clear Separation of Concerns**
   - Business rules in domain layer
   - Technical implementation in infrastructure layer
   - Application layer orchestrates both

## Migration Guide

### Before (Mixed Concerns):
```python
# Old approach - I/O mixed with business logic
class DiagramFileRepository:
    async def read_file(self, path: str) -> dict:
        # I/O operation
        with open(path) as f:
            data = yaml.load(f)
        
        # Business logic
        if "nodes" not in data:
            raise ValidationError("Missing nodes")
            
        return data
```

### After (Separated Concerns):
```python
# Domain service - pure business logic
class DiagramDomainService:
    def validate_diagram_data(self, data: dict) -> None:
        if "nodes" not in data:
            raise ValidationError("Missing nodes")

# Infrastructure service - I/O only
class DiagramFileRepository:
    def __init__(self, domain_service: DiagramDomainService):
        self.domain_service = domain_service
        
    async def read_file(self, path: str) -> dict:
        # I/O operation
        with open(path) as f:
            data = yaml.load(f)
            
        # Delegate validation to domain service
        self.domain_service.validate_diagram_data(data)
        return data
```

## Benefits

1. **Testability** - Domain logic can be tested without mocking I/O
2. **Maintainability** - Clear separation of concerns
3. **Flexibility** - Easy to swap infrastructure implementations
4. **Reusability** - Domain logic can be reused across different infrastructure adapters
5. **Architecture** - Follows hexagonal/clean architecture principles