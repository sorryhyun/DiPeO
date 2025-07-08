"""Example usage of refactored domain services with proper separation of concerns.

This example demonstrates how the refactored services follow hexagonal architecture:
- Domain services contain only business logic (no I/O)
- Infrastructure services handle all I/O operations
- Clear separation between business rules and technical implementation
"""

import asyncio
from pathlib import Path

# Domain services (pure business logic)
from dipeo.domain.services.diagram import DiagramDomainService
from dipeo.domain.services.file import FileDomainService
from dipeo.domain.services.api import APIDomainService

# Infrastructure services (I/O operations)
from dipeo.infra.persistence.diagram import DiagramFileRepository
from dipeo.infra.persistence.file import FileRepository, FileOperationsService
from dipeo.infra.http import APIClient, APIService


async def example_diagram_operations():
    """Example of diagram operations with separated concerns."""
    
    # 1. Create domain service (business logic only)
    diagram_domain = DiagramDomainService()
    
    # 2. Create infrastructure service with domain service injected
    diagram_repo = DiagramFileRepository(
        domain_service=diagram_domain,
        base_dir=Path("/tmp/dipeo_example")
    )
    
    # Initialize repository (creates directories)
    await diagram_repo.initialize()
    
    # Example diagram data
    diagram_data = {
        "nodes": [
            {"id": "start", "type": "start", "position": {"x": 0, "y": 0}},
            {"id": "person1", "type": "person", "position": {"x": 100, "y": 0}},
            {"id": "end", "type": "endpoint", "position": {"x": 200, "y": 0}}
        ],
        "edges": [
            {"source": "start", "target": "person1"},
            {"source": "person1", "target": "end"}
        ]
    }
    
    # Write diagram (validation happens in domain service, I/O in repository)
    await diagram_repo.write_file("example.json", diagram_data)
    
    # Read diagram back
    loaded_data = await diagram_repo.read_file("example.json")
    print(f"Loaded diagram: {loaded_data}")
    
    # List all diagrams
    files = await diagram_repo.list_files()
    print(f"Found {len(files)} diagram files")


async def example_file_operations():
    """Example of file operations with separated concerns."""
    
    # 1. Create domain service
    file_domain = FileDomainService()
    
    # 2. Create repository (low-level I/O)
    file_repo = FileRepository(domain_service=file_domain)
    
    # 3. Create operations service (combines domain + infrastructure)
    file_ops = FileOperationsService(
        repository=file_repo,
        domain_service=file_domain
    )
    
    # Example: Write JSON with validation and backup
    data = {"users": ["alice", "bob"], "count": 2}
    await file_ops.write_json_pretty(
        path="/tmp/dipeo_example/users.json",
        data=data,
        indent=4
    )
    
    # Example: Read JSON with validation
    loaded_data = await file_ops.read_json_safe(
        path="/tmp/dipeo_example/users.json",
        default={}  # Return empty dict if file doesn't exist
    )
    print(f"Loaded data: {loaded_data}")
    
    # Example: Append to log with timestamp
    await file_ops.append_with_timestamp(
        path="/tmp/dipeo_example/activity.log",
        content="User logged in",
        add_timestamp=True
    )


async def example_api_operations():
    """Example of API operations with separated concerns."""
    
    # 1. Create domain service
    api_domain = APIDomainService()
    
    # 2. Create infrastructure client
    api_client = APIClient(domain_service=api_domain)
    
    # 3. Create API service (combines domain + infrastructure)
    api_service = APIService(
        client=api_client,
        domain_service=api_domain
    )
    
    try:
        # Example: Simple API call with retry
        result = await api_service.execute_with_retry(
            url="https://api.example.com/users",
            method="GET",
            max_retries=3,
            retry_delay=1.0
        )
        print(f"API result: {result}")
        
        # Example: Multi-step workflow
        workflow = {
            "steps": [
                {
                    "name": "authenticate",
                    "url": "https://api.example.com/auth",
                    "method": "POST",
                    "data": {"username": "user", "password": "pass"}
                },
                {
                    "name": "get_profile",
                    "url": "https://api.example.com/profile",
                    "method": "GET",
                    "headers": {"Authorization": "Bearer {authenticate.token}"},
                    "success_condition": "status == active"
                }
            ]
        }
        
        workflow_results = await api_service.execute_workflow(workflow)
        print(f"Workflow results: {workflow_results}")
        
    finally:
        # Clean up HTTP session
        await api_client.close()


def demonstrate_pure_domain_logic():
    """Examples of using domain services without any I/O."""
    
    # 1. Diagram domain logic
    diagram_domain = DiagramDomainService()
    
    # Validate diagram structure (no I/O)
    try:
        diagram_domain.validate_diagram_data({
            "nodes": [{"id": "n1"}],  # Missing edges field
        })
    except ValidationError as e:
        print(f"Validation error: {e}")
    
    # Transform diagram for export (no I/O)
    transformed = diagram_domain.transform_diagram_for_export(
        {"nodes": [], "edges": []},
        target_format="light"
    )
    
    # 2. File domain logic
    file_domain = FileDomainService()
    
    # Calculate checksum (no I/O)
    checksum = file_domain.calculate_checksum("Hello, World!")
    print(f"Checksum: {checksum}")
    
    # Filter files by criteria (no I/O)
    filtered = file_domain.filter_files_by_criteria(
        file_paths=["/tmp/a.txt", "/tmp/b.json", "/tmp/c.yaml"],
        extensions=[".json", ".yaml"]
    )
    print(f"Filtered files: {filtered}")
    
    # 3. API domain logic
    api_domain = APIDomainService()
    
    # Calculate retry delay (no I/O)
    delay = api_domain.calculate_retry_delay(
        attempt=2,
        base_delay=1.0,
        max_delay=60.0
    )
    print(f"Retry delay: {delay}s")
    
    # Evaluate condition (no I/O)
    result = api_domain.evaluate_condition(
        "response.status == success",
        {"response": {"status": "success"}}
    )
    print(f"Condition result: {result}")


async def main():
    """Run all examples."""
    print("=== Diagram Operations Example ===")
    await example_diagram_operations()
    
    print("\n=== File Operations Example ===")
    await example_file_operations()
    
    print("\n=== API Operations Example ===")
    # await example_api_operations()  # Commented out as it needs real API
    
    print("\n=== Pure Domain Logic Examples ===")
    demonstrate_pure_domain_logic()


if __name__ == "__main__":
    asyncio.run(main())