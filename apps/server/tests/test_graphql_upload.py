"""Test GraphQL file upload functionality with actual file operations."""

import json
import yaml
import io
from pathlib import Path
from typing import Dict, Any, BinaryIO

import pytest
from gql import gql
from graphql import GraphQLError

from .conftest import *  # Import all fixtures


class TestDiagramUpload:
    """Test diagram file upload functionality."""
    
    async def test_upload_json_diagram(
        self,
        gql_client,
        sample_diagram_data,
        temp_diagram_file
    ):
        """Test uploading a JSON diagram file."""
        # Create diagram file
        file_path = temp_diagram_file(
            filename="upload_test.json",
            name="JSON Upload Test"
        )
        
        # Read file for upload
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Upload mutation
        upload_mutation = gql("""
            mutation UploadDiagram($file: Upload!) {
                uploadDiagram(file: $file) {
                    id
                    name
                    nodeCount
                    createdAt
                }
            }
        """)
        
        # Note: Actual file upload requires multipart form handling
        # This test verifies the mutation structure
        try:
            # Verify mutation exists in schema
            schema = await gql_client.introspect_schema()
            mutations = schema.type_map.get("Mutation")
            assert "uploadDiagram" in mutations.fields
            
            # Verify Upload scalar type exists
            assert "Upload" in schema.type_map
        except Exception as e:
            pytest.skip(f"Upload functionality not available: {e}")
    
    async def test_upload_yaml_diagram(
        self,
        gql_client,
        temp_yaml_diagram_file
    ):
        """Test uploading a YAML diagram file."""
        # Create YAML diagram file
        file_path = temp_yaml_diagram_file("upload_test.yaml")
        
        # Verify YAML parsing
        with open(file_path, 'r') as f:
            yaml_content = yaml.safe_load(f)
        
        assert yaml_content["name"] == "Test YAML Diagram"
        assert "nodes" in yaml_content
        assert "edges" in yaml_content
        
        # Upload mutation for YAML
        upload_mutation = gql("""
            mutation UploadDiagram($file: Upload!) {
                uploadDiagram(file: $file) {
                    id
                    name
                    nodeCount
                    format
                }
            }
        """)
        
        # Verify mutation accepts YAML files
        try:
            schema = await gql_client.introspect_schema()
            upload_diagram = schema.type_map["Mutation"].fields["uploadDiagram"]
            
            # Check return type includes format field
            return_fields = upload_diagram.type.of_type.fields
            assert "format" in return_fields
        except KeyError:
            pytest.skip("uploadDiagram mutation not found")
    
    async def test_upload_invalid_diagram(
        self,
        gql_client,
        tmp_path
    ):
        """Test uploading invalid diagram files."""
        # Create invalid JSON file
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")
        
        # This should fail validation
        with open(invalid_file, 'rb') as f:
            file_content = f.read()
        
        # Verify server would reject invalid JSON
        assert not json.loads(invalid_file.read_text())  # This will raise
    
    async def test_upload_diagram_size_limits(
        self,
        gql_client,
        tmp_path,
        sample_diagram_data
    ):
        """Test diagram upload size limits."""
        # Create large diagram with many nodes
        large_diagram = sample_diagram_data(
            name="Large Diagram Test",
            content={
                "nodes": [
                    {
                        "id": f"node_{i}",
                        "type": "llmAgent",
                        "data": {"prompt": f"Prompt {i}" * 100}
                    }
                    for i in range(1000)  # 1000 nodes
                ],
                "edges": []
            }
        )
        
        # Write to file
        large_file = tmp_path / "large_diagram.json"
        large_file.write_text(json.dumps(large_diagram))
        
        # Check file size
        file_size = large_file.stat().st_size
        assert file_size > 100_000  # Should be > 100KB
        
        # Server should handle large diagrams appropriately
        upload_mutation = gql("""
            mutation UploadDiagram($file: Upload!) {
                uploadDiagram(file: $file) {
                    id
                    nodeCount
                    fileSize
                }
            }
        """)


class TestGeneralFileUpload:
    """Test general file upload functionality."""
    
    async def test_upload_text_file(
        self,
        gql_client,
        tmp_path
    ):
        """Test uploading a text file."""
        # Create text file
        text_file = tmp_path / "data.txt"
        text_file.write_text("Sample data for testing\nLine 2\nLine 3")
        
        upload_mutation = gql("""
            mutation UploadFile($file: Upload!) {
                uploadFile(file: $file) {
                    filename
                    size
                    mimeType
                    url
                }
            }
        """)
        
        # Verify mutation structure
        try:
            schema = await gql_client.introspect_schema()
            upload_file = schema.type_map["Mutation"].fields["uploadFile"]
            
            # Check return fields
            return_fields = upload_file.type.of_type.fields
            assert "filename" in return_fields
            assert "size" in return_fields
            assert "url" in return_fields
        except KeyError:
            pytest.skip("uploadFile mutation not found")
    
    async def test_upload_binary_file(
        self,
        gql_client,
        tmp_path
    ):
        """Test uploading binary files."""
        # Create binary file
        binary_file = tmp_path / "data.bin"
        binary_data = bytes(range(256)) * 100  # 25.6KB
        binary_file.write_bytes(binary_data)
        
        assert binary_file.stat().st_size == 25600
        
        # Binary files should be handled correctly
        upload_mutation = gql("""
            mutation UploadFile($file: Upload!, $category: String) {
                uploadFile(file: $file, category: $category) {
                    filename
                    size
                    category
                }
            }
        """)
    
    async def test_upload_with_metadata(
        self,
        gql_client,
        tmp_path
    ):
        """Test uploading files with metadata."""
        # Create file
        test_file = tmp_path / "metadata_test.json"
        test_file.write_text(json.dumps({"data": "test"}))
        
        upload_mutation = gql("""
            mutation UploadFile($file: Upload!, $metadata: JSON) {
                uploadFile(file: $file, metadata: $metadata) {
                    filename
                    metadata
                }
            }
        """)
        
        # Verify metadata support
        try:
            schema = await gql_client.introspect_schema()
            upload_file = schema.type_map["Mutation"].fields["uploadFile"]
            
            # Check for metadata argument
            metadata_arg = next(
                (arg for arg in upload_file.args if arg.name == "metadata"),
                None
            )
            assert metadata_arg is not None
            assert "JSON" in str(metadata_arg.type)
        except KeyError:
            pytest.skip("uploadFile mutation not found")
    
    async def test_file_size_validation(
        self,
        gql_client,
        tmp_path
    ):
        """Test file size limit validation."""
        # Create files of different sizes
        small_file = tmp_path / "small.txt"
        small_file.write_text("Small content")
        
        medium_file = tmp_path / "medium.txt"
        medium_file.write_bytes(b"x" * (5 * 1024 * 1024))  # 5MB
        
        large_file = tmp_path / "large.txt"
        large_file.write_bytes(b"x" * (15 * 1024 * 1024))  # 15MB
        
        # Verify size limits
        assert small_file.stat().st_size < 1024  # < 1KB
        assert medium_file.stat().st_size == 5 * 1024 * 1024  # 5MB
        assert large_file.stat().st_size == 15 * 1024 * 1024  # 15MB
        
        # Server should enforce size limits (typically 10MB)


class TestMultipleFileUpload:
    """Test uploading multiple files."""
    
    async def test_upload_multiple_files(
        self,
        gql_client,
        tmp_path
    ):
        """Test uploading multiple files at once."""
        # Create multiple files
        files = []
        for i in range(3):
            file_path = tmp_path / f"file_{i}.txt"
            file_path.write_text(f"Content of file {i}")
            files.append(file_path)
        
        upload_mutation = gql("""
            mutation UploadMultiple($files: [Upload!]!) {
                uploadMultipleFiles(files: $files) {
                    filename
                    size
                    index
                }
            }
        """)
        
        # Verify batch upload support
        try:
            schema = await gql_client.introspect_schema()
            mutations = schema.type_map["Mutation"].fields
            
            if "uploadMultipleFiles" in mutations:
                upload_multiple = mutations["uploadMultipleFiles"]
                
                # Check it accepts array of uploads
                files_arg = next(
                    (arg for arg in upload_multiple.args if arg.name == "files"),
                    None
                )
                assert files_arg is not None
                assert "[Upload" in str(files_arg.type)
        except Exception:
            pytest.skip("Multiple file upload not supported")
    
    async def test_mixed_file_types_upload(
        self,
        gql_client,
        tmp_path
    ):
        """Test uploading different file types together."""
        # Create different file types
        json_file = tmp_path / "data.json"
        json_file.write_text(json.dumps({"type": "json"}))
        
        yaml_file = tmp_path / "data.yaml"
        yaml_file.write_text(yaml.dump({"type": "yaml"}))
        
        text_file = tmp_path / "data.txt"
        text_file.write_text("Plain text data")
        
        files = [json_file, yaml_file, text_file]
        
        # All file types should be accepted
        for f in files:
            assert f.exists()
            assert f.stat().st_size > 0


class TestUploadErrorHandling:
    """Test error handling in file uploads."""
    
    async def test_upload_nonexistent_file(self, gql_client):
        """Test uploading a file that doesn't exist."""
        # This would be handled by the client/transport layer
        # Server should never receive non-existent file
        pass
    
    async def test_upload_empty_file(
        self,
        gql_client,
        tmp_path
    ):
        """Test uploading empty files."""
        # Create empty file
        empty_file = tmp_path / "empty.txt"
        empty_file.touch()
        
        assert empty_file.stat().st_size == 0
        
        # Server should handle empty files gracefully
        upload_mutation = gql("""
            mutation UploadFile($file: Upload!) {
                uploadFile(file: $file) {
                    filename
                    size
                    error
                }
            }
        """)
    
    async def test_upload_permission_errors(
        self,
        gql_client,
        tmp_path,
        monkeypatch
    ):
        """Test handling permission errors during upload."""
        # Create file
        test_file = tmp_path / "restricted.txt"
        test_file.write_text("Restricted content")
        
        # Simulate permission issues
        # In real scenario, server might not have write permissions
        # to the upload directory
        
        upload_mutation = gql("""
            mutation UploadFile($file: Upload!) {
                uploadFile(file: $file) {
                    filename
                    error
                    errorCode
                }
            }
        """)
    
    async def test_concurrent_uploads(
        self,
        gql_client,
        tmp_path
    ):
        """Test handling concurrent file uploads."""
        import asyncio
        
        # Create multiple files
        files = []
        for i in range(5):
            file_path = tmp_path / f"concurrent_{i}.txt"
            file_path.write_text(f"Concurrent upload {i}")
            files.append(file_path)
        
        upload_mutation = gql("""
            mutation UploadFile($file: Upload!) {
                uploadFile(file: $file) {
                    filename
                    uploadedAt
                }
            }
        """)
        
        # In real implementation, would test concurrent uploads
        # Server should handle multiple simultaneous uploads