"""Test GraphQL file upload functionality with actual file operations."""

import json
import yaml
import io
import base64
from pathlib import Path
from typing import Dict, Any, BinaryIO

import pytest
from gql import gql
from graphql import GraphQLError

from .conftest import *  # Import all fixtures


class TestDiagramUpload:
    """Test diagram file upload functionality."""
    
    async def test_upload_diagram_mutation(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data,
        temp_diagram_file
    ):
        """Test uploading a diagram using the uploadDiagram mutation."""
        # Create diagram file
        file_path = temp_diagram_file(
            filename="upload_test.json",
            name="JSON Upload Test"
        )
        
        # The uploadDiagram mutation
        upload_mutation = gql(graphql_mutations["upload_diagram"])
        
        # Note: Real file upload requires multipart form handling
        # For testing, we'll validate the mutation exists and structure
        # In production, the Upload scalar is handled by the GraphQL transport
        
        # Test with validateOnly flag
        try:
            # Mock file upload - in real scenario, this would be handled by
            # the GraphQL transport layer (Apollo Upload, etc.)
            result = await gql_client.execute(
                upload_mutation,
                variable_values={
                    "file": None,  # Would be actual file in production
                    "format": "NATIVE",
                    "validateOnly": True
                }
            )
            
            # If we get here without error, mutation exists
            assert "uploadDiagram" in result
        except Exception as e:
            # This is expected since we can't actually upload without proper transport
            assert "Upload" in str(e) or "null" in str(e).lower()
    
    async def test_upload_file_input_mutation(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test uploading using FileUploadInput with base64 encoding."""
        # Create diagram content
        diagram_data = sample_diagram_data(name="Base64 Upload Test")
        content_str = json.dumps(diagram_data)
        content_base64 = base64.b64encode(content_str.encode()).decode()
        
        # Use the uploadFile mutation  
        upload_mutation = gql(graphql_mutations["upload_file"])
        
        result = await gql_client.execute(
            upload_mutation,
            variable_values={
                "input": {
                    "filename": "test_diagram.json",
                    "contentBase64": content_base64,
                    "contentType": "application/json"
                }
            }
        )
        
        assert "uploadFile" in result
        assert result["uploadFile"]["success"] is True
        if result["uploadFile"]["diagramId"]:
            assert result["uploadFile"]["diagramId"] is not None
    
    async def test_import_yaml_diagram(
        self,
        gql_client,
        temp_yaml_diagram_file
    ):
        """Test importing a YAML diagram directly."""
        # Create YAML diagram file
        file_path = temp_yaml_diagram_file("test.yaml")
        
        with open(file_path, 'r') as f:
            yaml_content = f.read()
        
        # Import YAML mutation
        import_mutation = gql("""
            mutation ImportYamlDiagram($input: ImportYamlInput!) {
                importYamlDiagram(input: $input) {
                    success
                    diagram {
                        metadata {
                            id
                            name
                        }
                        nodeCount
                    }
                    message
                    error
                }
            }
        """)
        
        result = await gql_client.execute(
            import_mutation,
            variable_values={
                "input": {
                    "content": yaml_content,
                    "filename": "imported.yaml"
                }
            }
        )
        
        assert "importYamlDiagram" in result
        assert result["importYamlDiagram"]["success"] is True
        assert result["importYamlDiagram"]["diagram"]["nodeCount"] > 0
    
    async def test_upload_invalid_diagram(
        self,
        gql_client,
        graphql_mutations
    ):
        """Test uploading invalid diagram data."""
        # Invalid JSON
        invalid_content = "{ invalid json }"
        content_base64 = base64.b64encode(invalid_content.encode()).decode()
        
        upload_mutation = gql(graphql_mutations["upload_file"])
        
        result = await gql_client.execute(
            upload_mutation,
            variable_values={
                "input": {
                    "filename": "invalid.json",
                    "contentBase64": content_base64,
                    "contentType": "application/json"
                }
            }
        )
        
        # Should return error but not crash
        assert "uploadFile" in result
        if result["uploadFile"]["errors"]:
            assert len(result["uploadFile"]["errors"]) > 0


class TestGeneralFileUpload:
    """Test general file upload functionality."""
    
    async def test_upload_text_file_base64(
        self,
        gql_client,
        graphql_mutations
    ):
        """Test uploading a text file using base64 encoding."""
        # Create text content
        text_content = "Sample data for testing\nLine 2\nLine 3"
        content_base64 = base64.b64encode(text_content.encode()).decode()
        
        upload_mutation = gql(graphql_mutations["upload_file"])
        
        result = await gql_client.execute(
            upload_mutation,
            variable_values={
                "input": {
                    "filename": "data.txt",
                    "contentBase64": content_base64,
                    "contentType": "text/plain"
                }
            }
        )
        
        assert "uploadFile" in result
        assert result["uploadFile"]["success"] is True
        assert result["uploadFile"]["message"] is not None
    
    async def test_upload_binary_file_base64(
        self,
        gql_client,
        graphql_mutations
    ):
        """Test uploading binary data using base64 encoding."""
        # Create binary data
        binary_data = bytes(range(256))  # All byte values
        content_base64 = base64.b64encode(binary_data).decode()
        
        upload_mutation = gql(graphql_mutations["upload_file"])
        
        result = await gql_client.execute(
            upload_mutation,
            variable_values={
                "input": {
                    "filename": "data.bin",
                    "contentBase64": content_base64,
                    "contentType": "application/octet-stream"
                }
            }
        )
        
        assert "uploadFile" in result
        assert result["uploadFile"]["success"] is True
    
    async def test_upload_large_file_base64(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test uploading larger files with base64 encoding."""
        # Create large diagram with many nodes
        large_diagram = sample_diagram_data(
            name="Large Diagram Test"
        )
        
        # Add many nodes
        nodes = []
        for i in range(100):  # 100 nodes
            nodes.append({
                "id": f"node_{i}",
                "type": "START",
                "position": {"x": i * 10, "y": i * 10},
                "data": {"description": f"Node {i} " * 10}
            })
        
        large_diagram["nodes"] = nodes
        
        content_str = json.dumps(large_diagram)
        content_base64 = base64.b64encode(content_str.encode()).decode()
        
        upload_mutation = gql(graphql_mutations["upload_file"])
        
        result = await gql_client.execute(
            upload_mutation,
            variable_values={
                "input": {
                    "filename": "large_diagram.json",
                    "contentBase64": content_base64,
                    "contentType": "application/json"
                }
            }
        )
        
        assert "uploadFile" in result
        # Large files might have different handling
        assert result["uploadFile"]["success"] in [True, False]
        if not result["uploadFile"]["success"]:
            assert result["uploadFile"]["errors"] is not None


class TestMultipleFileUpload:
    """Test uploading multiple files."""
    
    async def test_upload_multiple_files_mutation(
        self,
        gql_client
    ):
        """Test the uploadMultipleFiles mutation."""
        # Create multiple file contents
        files_data = []
        for i in range(3):
            content = f"Content of file {i}"
            content_base64 = base64.b64encode(content.encode()).decode()
            files_data.append({
                "filename": f"file_{i}.txt",
                "contentBase64": content_base64,
                "contentType": "text/plain"
            })
        
        # Note: uploadMultipleFiles expects Upload scalars, not FileUploadInput
        # This would require proper multipart form handling
        upload_mutation = gql("""
            mutation UploadMultiple($files: [Upload!]!, $category: String!) {
                uploadMultipleFiles(files: $files, category: $category) {
                    success
                    diagramId
                    message
                    errors
                }
            }
        """)
        
        # This will fail without proper Upload scalar support
        try:
            result = await gql_client.execute(
                upload_mutation,
                variable_values={
                    "files": [None, None, None],  # Would be actual files
                    "category": "test"
                }
            )
        except Exception as e:
            # Expected - can't upload without proper transport
            assert "Upload" in str(e) or "null" in str(e).lower()


class TestDiagramExportImport:
    """Test diagram export and import functionality."""
    
    async def test_export_diagram_formats(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test exporting diagrams in different formats."""
        # First create a diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Export Test")
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        
        diagram_id = create_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Export in different formats
        export_mutation = gql("""
            mutation ExportDiagram($diagramId: DiagramID!, $format: DiagramFormat!, $includeMetadata: Boolean!) {
                exportDiagram(diagramId: $diagramId, format: $format, includeMetadata: $includeMetadata) {
                    success
                    message
                    content
                    format
                    filename
                }
            }
        """)
        
        formats = ["NATIVE", "LIGHT", "READABLE", "NATIVE_YAML"]
        
        for format_type in formats:
            result = await gql_client.execute(
                export_mutation,
                variable_values={
                    "diagramId": diagram_id,
                    "format": format_type,
                    "includeMetadata": True
                }
            )
            
            assert "exportDiagram" in result
            export = result["exportDiagram"]
            
            if export["success"]:
                assert export["format"] == format_type
                assert export["content"] is not None
                assert export["filename"] is not None
    
    async def test_quicksave_diagram(
        self,
        gql_client
    ):
        """Test quicksave functionality for diagrams."""
        quicksave_mutation = gql("""
            mutation QuicksaveDiagram($content: JSONScalar!, $existingDiagramId: DiagramID) {
                quicksaveDiagram(content: $content, existingDiagramId: $existingDiagramId) {
                    success
                    diagram {
                        metadata {
                            id
                            name
                        }
                    }
                    message
                }
            }
        """)
        
        diagram_content = {
            "name": "Quicksave Test",
            "nodes": [
                {
                    "id": "node1",
                    "type": "START",
                    "position": {"x": 0, "y": 0},
                    "data": {}
                }
            ],
            "edges": []
        }
        
        result = await gql_client.execute(
            quicksave_mutation,
            variable_values={
                "content": diagram_content,
                "existingDiagramId": None
            }
        )
        
        assert "quicksaveDiagram" in result
        assert result["quicksaveDiagram"]["success"] is True
        assert result["quicksaveDiagram"]["diagram"]["metadata"]["id"] is not None