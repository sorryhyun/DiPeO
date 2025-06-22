"""Test diagram-related GraphQL mutations."""

import json
from typing import Dict, Any

import pytest
from gql import gql
from graphql import GraphQLError

from ..conftest import *  # Import all fixtures


class TestDiagramCRUD:
    """Test basic diagram CRUD operations."""
    
    async def test_create_diagram(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test creating a new diagram."""
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Test Create Diagram")
        
        result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        
        assert "createDiagram" in result
        assert result["createDiagram"]["success"] is True
        created = result["createDiagram"]["diagram"]
        assert created["metadata"]["id"] is not None
        assert created["metadata"]["name"] == "Test Create Diagram"
        assert created["metadata"]["created"] is not None
    
    async def test_get_diagram(
        self,
        gql_client,
        graphql_queries,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test retrieving a diagram by ID."""
        # First create a diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Test Get Diagram")
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Now retrieve it
        get_query = gql(graphql_queries["get_diagram"])
        result = await gql_client.execute(
            get_query,
            variable_values={"id": diagram_id}
        )
        
        assert "diagram" in result
        diagram = result["diagram"]
        assert diagram["metadata"]["id"] == diagram_id
        assert diagram["metadata"]["name"] == "Test Get Diagram"
        assert "nodes" in diagram
        assert "arrows" in diagram
    
    async def test_save_diagram(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test saving/updating an existing diagram."""
        # Create diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Original Name")
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Save/update diagram
        save_mutation = gql("""
            mutation SaveDiagram($diagramId: DiagramID!, $format: DiagramFormat) {
                saveDiagram(diagramId: $diagramId, format: $format) {
                    success
                    diagram {
                        metadata {
                            id
                            name
                            modified
                        }
                    }
                    message
                }
            }
        """)
        
        result = await gql_client.execute(
            save_mutation,
            variable_values={
                "diagramId": diagram_id,
                "format": "NATIVE"
            }
        )
        
        assert "saveDiagram" in result
        assert result["saveDiagram"]["success"] is True
        saved = result["saveDiagram"]["diagram"]
        assert saved["metadata"]["id"] == diagram_id
        assert saved["metadata"]["modified"] is not None
    
    async def test_delete_diagram(
        self,
        gql_client,
        graphql_mutations,
        graphql_queries,
        sample_diagram_data
    ):
        """Test deleting a diagram."""
        # Create diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="To Be Deleted")
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Delete diagram
        delete_mutation = gql("""
            mutation DeleteDiagram($id: DiagramID!) {
                deleteDiagram(id: $id) {
                    success
                    message
                }
            }
        """)
        
        result = await gql_client.execute(
            delete_mutation,
            variable_values={"id": diagram_id}
        )
        
        assert "deleteDiagram" in result
        assert result["deleteDiagram"]["success"] is True
        
        # Verify it's deleted - should return null
        get_query = gql(graphql_queries["get_diagram"])
        result = await gql_client.execute(
            get_query,
            variable_values={"id": diagram_id}
        )
        assert result["diagram"] is None
    
    async def test_list_diagrams(
        self,
        gql_client,
        graphql_queries,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test listing diagrams with pagination."""
        # Create multiple diagrams
        create_mutation = gql(graphql_mutations["create_diagram"])
        
        for i in range(5):
            diagram_data = sample_diagram_data(name=f"List Test {i}")
            await gql_client.execute(
                create_mutation,
                variable_values={"input": diagram_data}
            )
        
        # List with pagination
        list_query = gql(graphql_queries["list_diagrams"])
        
        # Test with limit
        result = await gql_client.execute(
            list_query,
            variable_values={"limit": 3, "offset": 0}
        )
        assert "diagrams" in result
        assert len(result["diagrams"]) <= 3
        
        # Test with offset
        result = await gql_client.execute(
            list_query,
            variable_values={"limit": 2, "offset": 2}
        )
        assert len(result["diagrams"]) <= 2


class TestDiagramImportExport:
    """Test diagram import/export functionality."""
    
    async def test_import_yaml_diagram(
        self,
        gql_client,
        temp_yaml_diagram_file
    ):
        """Test importing a diagram from YAML."""
        yaml_file = temp_yaml_diagram_file()
        
        with open(yaml_file, 'r') as f:
            yaml_content = f.read()
        
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
                        arrowCount
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
                    "filename": "test.yaml"
                }
            }
        )
        
        assert "importYamlDiagram" in result
        assert result["importYamlDiagram"]["success"] is True
        imported = result["importYamlDiagram"]["diagram"]
        assert imported["metadata"]["id"] is not None
        assert imported["metadata"]["name"] == "Test YAML Diagram"
        assert imported["nodeCount"] > 0
    
    async def test_export_diagram(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test exporting a diagram to different formats."""
        # Create diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Export Test")
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Export diagram
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
        
        # Test export as NATIVE format
        result = await gql_client.execute(
            export_mutation,
            variable_values={
                "diagramId": diagram_id,
                "format": "NATIVE",
                "includeMetadata": True
            }
        )
        
        assert "exportDiagram" in result
        export = result["exportDiagram"]
        assert export["success"] is True
        assert export["format"] == "NATIVE"
        assert export["content"] is not None
        
        # Test export as LIGHT format
        result = await gql_client.execute(
            export_mutation,
            variable_values={
                "diagramId": diagram_id,
                "format": "LIGHT",
                "includeMetadata": False
            }
        )
        
        assert result["exportDiagram"]["success"] is True
        assert result["exportDiagram"]["format"] == "LIGHT"
    
    async def test_convert_diagram(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test converting diagram between formats."""
        # Create diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Convert Test")
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Convert diagram
        convert_mutation = gql("""
            mutation ConvertDiagram($diagramId: DiagramID!, $targetFormat: DiagramFormat!) {
                convertDiagram(diagramId: $diagramId, targetFormat: $targetFormat) {
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
        
        result = await gql_client.execute(
            convert_mutation,
            variable_values={
                "diagramId": diagram_id,
                "targetFormat": "READABLE"
            }
        )
        
        assert "convertDiagram" in result
        assert result["convertDiagram"]["success"] is True


class TestDiagramNodeOperations:
    """Test diagram node operations."""
    
    async def test_create_node(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test adding nodes to a diagram."""
        # Create diagram first
        create_diagram_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Node Test Diagram")
        
        diagram_result = await gql_client.execute(
            create_diagram_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = diagram_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Create node
        create_node_mutation = gql(graphql_mutations["create_node"])
        
        node_input = {
            "type": "START",
            "position": {"x": 100, "y": 100},
            "label": "Start Node",
            "properties": {}
        }
        
        result = await gql_client.execute(
            create_node_mutation,
            variable_values={
                "diagramId": diagram_id,
                "input": node_input
            }
        )
        
        assert "createNode" in result
        assert result["createNode"]["success"] is True
        node = result["createNode"]["node"]
        assert node["id"] is not None
        assert node["type"] == "START"
        assert node["position"]["x"] == 100
        assert node["position"]["y"] == 100
    
    async def test_create_arrow(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test creating arrows between nodes."""
        # Create diagram
        create_diagram_mutation = gql(graphql_mutations["create_diagram"])
        diagram_result = await gql_client.execute(
            create_diagram_mutation,
            variable_values={"input": sample_diagram_data()}
        )
        diagram_id = diagram_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Create two nodes
        create_node_mutation = gql(graphql_mutations["create_node"])
        
        node1_result = await gql_client.execute(
            create_node_mutation,
            variable_values={
                "diagramId": diagram_id,
                "input": {
                    "type": "START",
                    "position": {"x": 0, "y": 0},
                    "label": "Node 1"
                }
            }
        )
        node1_id = node1_result["createNode"]["node"]["id"]
        
        node2_result = await gql_client.execute(
            create_node_mutation,
            variable_values={
                "diagramId": diagram_id,
                "input": {
                    "type": "ENDPOINT",
                    "position": {"x": 200, "y": 0},
                    "label": "Node 2"
                }
            }
        )
        node2_id = node2_result["createNode"]["node"]["id"]
        
        # Create arrow
        create_arrow_mutation = gql("""
            mutation CreateArrow($diagramId: DiagramID!, $input: CreateArrowInput!) {
                createArrow(diagramId: $diagramId, input: $input) {
                    success
                    diagram {
                        arrows {
                            id
                            source
                            target
                        }
                    }
                    message
                }
            }
        """)
        
        result = await gql_client.execute(
            create_arrow_mutation,
            variable_values={
                "diagramId": diagram_id,
                "input": {
                    "source": node1_id,
                    "target": node2_id,
                    "label": "Connection"
                }
            }
        )
        
        assert "createArrow" in result
        assert result["createArrow"]["success"] is True
        arrows = result["createArrow"]["diagram"]["arrows"]
        assert len(arrows) > 0
        
        # Find the created arrow
        created_arrow = next(
            (a for a in arrows if a["source"] == node1_id and a["target"] == node2_id),
            None
        )
        assert created_arrow is not None


class TestDiagramQuicksave:
    """Test quicksave functionality."""
    
    async def test_quicksave_new_diagram(
        self,
        gql_client
    ):
        """Test quicksaving a new diagram."""
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
            "name": "Quicksaved Diagram",
            "nodes": [],
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
    
    async def test_quicksave_existing_diagram(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test quicksaving over an existing diagram."""
        # Create diagram first
        create_mutation = gql(graphql_mutations["create_diagram"])
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": sample_diagram_data()}
        )
        diagram_id = create_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Quicksave with updates
        quicksave_mutation = gql("""
            mutation QuicksaveDiagram($content: JSONScalar!, $existingDiagramId: DiagramID) {
                quicksaveDiagram(content: $content, existingDiagramId: $existingDiagramId) {
                    success
                    diagram {
                        metadata {
                            id
                            name
                            modified
                        }
                    }
                    message
                }
            }
        """)
        
        updated_content = {
            "name": "Updated via Quicksave",
            "nodes": [{"id": "new-node", "type": "START"}],
            "edges": []
        }
        
        result = await gql_client.execute(
            quicksave_mutation,
            variable_values={
                "content": updated_content,
                "existingDiagramId": diagram_id
            }
        )
        
        assert "quicksaveDiagram" in result
        assert result["quicksaveDiagram"]["success"] is True
        assert result["quicksaveDiagram"]["diagram"]["metadata"]["id"] == diagram_id
        assert result["quicksaveDiagram"]["diagram"]["metadata"]["modified"] is not None