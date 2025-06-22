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
        created = result["createDiagram"]
        assert created["id"] is not None
        assert created["name"] == "Test Create Diagram"
        assert created["createdAt"] is not None
    
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
        diagram_id = create_result["createDiagram"]["id"]
        
        # Now retrieve it
        get_query = gql(graphql_queries["get_diagram"])
        result = await gql_client.execute(
            get_query,
            variable_values={"id": diagram_id}
        )
        
        assert "diagram" in result
        diagram = result["diagram"]
        assert diagram["id"] == diagram_id
        assert diagram["name"] == "Test Get Diagram"
        assert diagram["content"] is not None
        assert diagram["metadata"] is not None
    
    async def test_update_diagram(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test updating an existing diagram."""
        # Create diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Original Name")
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["id"]
        
        # Update diagram
        update_mutation = gql("""
            mutation UpdateDiagram($id: ID!, $input: DiagramInput!) {
                updateDiagram(id: $id, input: $input) {
                    id
                    name
                    updatedAt
                }
            }
        """)
        
        updated_data = sample_diagram_data(
            name="Updated Name",
            metadata={"version": "2.0", "updated": True}
        )
        
        result = await gql_client.execute(
            update_mutation,
            variable_values={
                "id": diagram_id,
                "input": updated_data
            }
        )
        
        assert "updateDiagram" in result
        updated = result["updateDiagram"]
        assert updated["id"] == diagram_id
        assert updated["name"] == "Updated Name"
        assert updated["updatedAt"] is not None
    
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
        diagram_id = create_result["createDiagram"]["id"]
        
        # Delete diagram
        delete_mutation = gql("""
            mutation DeleteDiagram($id: ID!) {
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
        
        # Verify it's deleted
        get_query = gql(graphql_queries["get_diagram"])
        with pytest.raises(Exception):
            await gql_client.execute(
                get_query,
                variable_values={"id": diagram_id}
            )
    
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
        
        # Test default listing
        result = await gql_client.execute(list_query)
        assert "diagrams" in result
        assert len(result["diagrams"]) >= 5
        
        # Test with limit
        result = await gql_client.execute(
            list_query,
            variable_values={"limit": 3}
        )
        assert len(result["diagrams"]) == 3
        
        # Test with offset
        result = await gql_client.execute(
            list_query,
            variable_values={"limit": 2, "offset": 2}
        )
        assert len(result["diagrams"]) == 2


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
            mutation ImportYamlDiagram($yaml: String!) {
                importYamlDiagram(yaml: $yaml) {
                    id
                    name
                    nodeCount
                    edgeCount
                }
            }
        """)
        
        result = await gql_client.execute(
            import_mutation,
            variable_values={"yaml": yaml_content}
        )
        
        assert "importYamlDiagram" in result
        imported = result["importYamlDiagram"]
        assert imported["id"] is not None
        assert imported["name"] == "Test YAML Diagram"
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
        diagram_id = create_result["createDiagram"]["id"]
        
        # Export as JSON
        export_json_mutation = gql("""
            mutation ExportDiagramJson($id: ID!) {
                exportDiagram(id: $id, format: JSON) {
                    content
                    format
                    filename
                }
            }
        """)
        
        result = await gql_client.execute(
            export_json_mutation,
            variable_values={"id": diagram_id}
        )
        
        assert "exportDiagram" in result
        export = result["exportDiagram"]
        assert export["format"] == "JSON"
        assert export["filename"].endswith(".json")
        
        # Verify content is valid JSON
        exported_data = json.loads(export["content"])
        assert exported_data["name"] == "Export Test"
        
        # Export as YAML
        export_yaml_mutation = gql("""
            mutation ExportDiagramYaml($id: ID!) {
                exportDiagram(id: $id, format: YAML) {
                    content
                    format
                    filename
                }
            }
        """)
        
        result = await gql_client.execute(
            export_yaml_mutation,
            variable_values={"id": diagram_id}
        )
        
        assert result["exportDiagram"]["format"] == "YAML"
        assert result["exportDiagram"]["filename"].endswith(".yaml")
    
    async def test_clone_diagram(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test cloning an existing diagram."""
        # Create original
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Original Diagram")
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        original_id = create_result["createDiagram"]["id"]
        
        # Clone diagram
        clone_mutation = gql("""
            mutation CloneDiagram($id: ID!, $newName: String) {
                cloneDiagram(id: $id, newName: $newName) {
                    id
                    name
                    content
                }
            }
        """)
        
        result = await gql_client.execute(
            clone_mutation,
            variable_values={
                "id": original_id,
                "newName": "Cloned Diagram"
            }
        )
        
        assert "cloneDiagram" in result
        cloned = result["cloneDiagram"]
        assert cloned["id"] != original_id
        assert cloned["name"] == "Cloned Diagram"
        assert cloned["content"] == diagram_data["content"]


class TestDiagramValidation:
    """Test diagram validation and error handling."""
    
    async def test_create_invalid_diagram(
        self,
        gql_client,
        graphql_mutations
    ):
        """Test creating diagram with invalid data."""
        create_mutation = gql(graphql_mutations["create_diagram"])
        
        # Missing required fields
        with pytest.raises(GraphQLError):
            await gql_client.execute(
                create_mutation,
                variable_values={"input": {}}
            )
        
        # Invalid node structure
        invalid_data = {
            "name": "Invalid Diagram",
            "content": {
                "nodes": [{"invalid": "structure"}],
                "edges": []
            }
        }
        
        with pytest.raises(Exception):
            await gql_client.execute(
                create_mutation,
                variable_values={"input": invalid_data}
            )
    
    async def test_duplicate_node_ids(
        self,
        gql_client,
        graphql_mutations
    ):
        """Test creating diagram with duplicate node IDs."""
        create_mutation = gql(graphql_mutations["create_diagram"])
        
        duplicate_data = {
            "name": "Duplicate Nodes",
            "content": {
                "nodes": [
                    {"id": "node1", "type": "inputAgent"},
                    {"id": "node1", "type": "outputAgent"}  # Duplicate ID
                ],
                "edges": []
            }
        }
        
        with pytest.raises(Exception) as exc_info:
            await gql_client.execute(
                create_mutation,
                variable_values={"input": duplicate_data}
            )
        
        error_msg = str(exc_info.value).lower()
        assert "duplicate" in error_msg or "unique" in error_msg
    
    async def test_invalid_edge_references(
        self,
        gql_client,
        graphql_mutations
    ):
        """Test creating diagram with edges referencing non-existent nodes."""
        create_mutation = gql(graphql_mutations["create_diagram"])
        
        invalid_edges = {
            "name": "Invalid Edges",
            "content": {
                "nodes": [
                    {"id": "node1", "type": "inputAgent"}
                ],
                "edges": [
                    {
                        "id": "edge1",
                        "source": "node1",
                        "target": "non_existent"  # Invalid reference
                    }
                ]
            }
        }
        
        with pytest.raises(Exception) as exc_info:
            await gql_client.execute(
                create_mutation,
                variable_values={"input": invalid_edges}
            )
        
        error_msg = str(exc_info.value).lower()
        assert "exist" in error_msg or "invalid" in error_msg


class TestDiagramBatchOperations:
    """Test batch diagram operations."""
    
    async def test_batch_create_diagrams(
        self,
        gql_client,
        sample_diagram_data
    ):
        """Test creating multiple diagrams in batch."""
        batch_create_mutation = gql("""
            mutation BatchCreateDiagrams($inputs: [DiagramInput!]!) {
                batchCreateDiagrams(inputs: $inputs) {
                    id
                    name
                    createdAt
                }
            }
        """)
        
        # Create batch input
        batch_inputs = [
            sample_diagram_data(name=f"Batch Diagram {i}")
            for i in range(3)
        ]
        
        try:
            result = await gql_client.execute(
                batch_create_mutation,
                variable_values={"inputs": batch_inputs}
            )
            
            assert "batchCreateDiagrams" in result
            created = result["batchCreateDiagrams"]
            assert len(created) == 3
            
            for i, diagram in enumerate(created):
                assert diagram["name"] == f"Batch Diagram {i}"
        except GraphQLError:
            pytest.skip("Batch operations not supported")
    
    async def test_batch_delete_diagrams(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test deleting multiple diagrams in batch."""
        # Create diagrams to delete
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_ids = []
        
        for i in range(3):
            diagram_data = sample_diagram_data(name=f"To Delete {i}")
            result = await gql_client.execute(
                create_mutation,
                variable_values={"input": diagram_data}
            )
            diagram_ids.append(result["createDiagram"]["id"])
        
        # Batch delete
        batch_delete_mutation = gql("""
            mutation BatchDeleteDiagrams($ids: [ID!]!) {
                batchDeleteDiagrams(ids: $ids) {
                    success
                    deletedCount
                    failedIds
                }
            }
        """)
        
        try:
            result = await gql_client.execute(
                batch_delete_mutation,
                variable_values={"ids": diagram_ids}
            )
            
            assert "batchDeleteDiagrams" in result
            batch_result = result["batchDeleteDiagrams"]
            assert batch_result["success"] is True
            assert batch_result["deletedCount"] == 3
            assert len(batch_result["failedIds"]) == 0
        except GraphQLError:
            pytest.skip("Batch delete not supported")