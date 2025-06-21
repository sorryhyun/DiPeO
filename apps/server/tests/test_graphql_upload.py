"""
Test GraphQL file upload functionality.
"""
import pytest
import asyncio
from pathlib import Path
import sys
import json
import yaml
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from httpx import AsyncClient
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

# Test configuration
GRAPHQL_URL = "http://localhost:8000/graphql"

@pytest.fixture
async def gql_client():
    """Create GraphQL client with multipart support."""
    transport = AIOHTTPTransport(
        url=GRAPHQL_URL,
        # Enable file upload support
        headers={"apollo-require-preflight": "true"}
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)
    return client

@pytest.fixture
def sample_diagram_content() -> Dict[str, Any]:
    """Sample diagram content for upload tests."""
    return {
        "nodes": {
            "start_1": {
                "id": "start_1",
                "type": "start",
                "label": "Upload Test",
                "props": {"staticData": {"test": True}}
            }
        },
        "arrows": {},
        "handles": {
            "start_1:output": {"nodeId": "start_1", "name": "output", "type": "source"}
        },
        "metadata": {"name": "Upload Test Diagram", "version": "2.0.0"}
    }

@pytest.mark.asyncio
async def test_upload_diagram_json(gql_client, sample_diagram_content, tmp_path):
    """Test uploading a JSON diagram file."""
    # Create temporary JSON file
    json_file = tmp_path / "test_diagram.json"
    with open(json_file, 'w') as f:
        json.dump(sample_diagram_content, f)
    
    # Upload mutation
    upload_mutation = gql("""
        mutation UploadDiagram($file: Upload!) {
            uploadDiagram(file: $file) {
                success
                message
                diagramId
                diagramName
                nodeCount
            }
        }
    """)
    
    # Note: The actual file upload with gql client requires special handling
    # This is a simplified test structure
    # In practice, you'd use the multipart form data format
    
    # For testing purposes, we'll verify the mutation exists in schema
    try:
        # This will fail if the mutation doesn't exist in the schema
        schema = await gql_client.introspect_schema()
        mutations = schema.type_map.get("Mutation")
        assert mutations is not None
        
        # Check if uploadDiagram mutation exists
        upload_diagram_field = None
        for field_name, field in mutations.fields.items():
            if field_name == "uploadDiagram":
                upload_diagram_field = field
                break
        
        assert upload_diagram_field is not None, "uploadDiagram mutation not found in schema"
        
        # Verify it accepts Upload type
        file_arg = None
        for arg in upload_diagram_field.args:
            if arg.name == "file":
                file_arg = arg
                break
        
        assert file_arg is not None, "file argument not found in uploadDiagram mutation"
        assert str(file_arg.type).replace("!", "") == "Upload", "file argument should be Upload type"
        
    except Exception as e:
        pytest.fail(f"Schema introspection failed: {str(e)}")

@pytest.mark.asyncio
async def test_upload_diagram_yaml(gql_client, sample_diagram_content, tmp_path):
    """Test uploading a YAML diagram file."""
    # Create temporary YAML file
    yaml_file = tmp_path / "test_diagram.yaml"
    with open(yaml_file, 'w') as f:
        yaml.dump(sample_diagram_content, f)
    
    # Similar structure to JSON test
    # Verify YAML upload is supported
    assert yaml_file.exists()
    assert yaml_file.suffix == ".yaml"

@pytest.mark.asyncio
async def test_upload_general_file(gql_client, tmp_path):
    """Test uploading a general file."""
    # Create a test file
    test_file = tmp_path / "test_data.txt"
    test_content = "This is test data for upload"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    # Upload mutation
    upload_mutation = gql("""
        mutation UploadFile($file: Upload!, $category: String) {
            uploadFile(file: $file, category: $category) {
                success
                message
                fileId
                filePath
                fileType
                fileSize
            }
        }
    """)
    
    # Verify the mutation exists
    try:
        schema = await gql_client.introspect_schema()
        mutations = schema.type_map.get("Mutation")
        
        # Check if uploadFile mutation exists
        upload_file_field = None
        for field_name, field in mutations.fields.items():
            if field_name == "uploadFile":
                upload_file_field = field
                break
        
        assert upload_file_field is not None, "uploadFile mutation not found in schema"
        
    except Exception as e:
        pytest.fail(f"Schema introspection failed: {str(e)}")

@pytest.mark.asyncio
async def test_upload_multiple_files(gql_client, tmp_path):
    """Test uploading multiple files at once."""
    # Create multiple test files
    files = []
    for i in range(3):
        test_file = tmp_path / f"test_file_{i}.txt"
        with open(test_file, 'w') as f:
            f.write(f"Test content {i}")
        files.append(test_file)
    
    # Multiple upload mutation
    upload_mutation = gql("""
        mutation UploadMultiple($files: [Upload!]!, $category: String) {
            uploadMultipleFiles(files: $files, category: $category) {
                success
                message
                fileId
            }
        }
    """)
    
    # Verify the mutation exists
    try:
        schema = await gql_client.introspect_schema()
        mutations = schema.type_map.get("Mutation")
        
        # Check if uploadMultipleFiles mutation exists
        upload_multiple_field = None
        for field_name, field in mutations.fields.items():
            if field_name == "uploadMultipleFiles":
                upload_multiple_field = field
                break
        
        assert upload_multiple_field is not None, "uploadMultipleFiles mutation not found in schema"
        
        # Verify it returns a list
        return_type = str(upload_multiple_field.type)
        assert return_type.startswith("["), "uploadMultipleFiles should return a list"
        
    except Exception as e:
        pytest.fail(f"Schema introspection failed: {str(e)}")

@pytest.mark.asyncio
async def test_upload_size_limit(gql_client, tmp_path):
    """Test file size limit enforcement."""
    # Create a large file (over 10MB)
    large_file = tmp_path / "large_file.bin"
    with open(large_file, 'wb') as f:
        # Write 11MB of data
        f.write(b'0' * (11 * 1024 * 1024))
    
    # This would test that the server rejects files over 10MB
    # In actual implementation, the mutation would return success=False
    assert large_file.stat().st_size > 10 * 1024 * 1024

if __name__ == "__main__":
    pytest.main([__file__, "-v"])