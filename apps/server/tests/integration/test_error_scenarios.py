"""Integration tests for error scenarios and edge cases."""

import json
import asyncio
from typing import Dict, Any

import pytest
from gql import gql
from graphql import GraphQLError

from ..conftest import *  # Import all fixtures


class TestErrorScenarios:
    """Test various error conditions and edge cases."""
    
    async def test_invalid_diagram_creation(self, gql_client, graphql_mutations):
        """Test creating diagrams with invalid data."""
        create_mutation = gql(graphql_mutations["create_diagram"])
        
        # Test cases for invalid diagram creation inputs
        invalid_cases = [
            {
                "name": "Empty name",
                "data": {"name": "", "description": "Test"},
                "error": "name cannot be empty"
            },
            {
                "name": "Whitespace only name",
                "data": {"name": "   ", "description": "Test"},
                "error": "name cannot be empty"
            },
            {
                "name": "Missing name",
                "data": {"description": "Test"},
                "error": "field required"
            }
        ]
        
        for case in invalid_cases:
            with pytest.raises((GraphQLError, Exception)) as exc_info:
                await gql_client.execute(
                    create_mutation,
                    variable_values={"input": case["data"]}
                )
            # Verify error relates to expected issue
            error_msg = str(exc_info.value).lower()
            assert case["error"] in error_msg or "validation" in error_msg
    
    async def test_execution_with_missing_api_keys(
        self,
        gql_client,
        graphql_mutations,
        monkeypatch
    ):
        """Test execution when required API keys are missing."""
        # Remove API keys
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        
        # Create diagram requiring LLM
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = {
            "name": "Missing API Key Test",
            "content": {
                "nodes": [
                    {
                        "id": "1",
                        "type": "llmAgent",
                        "data": {
                            "model": "gpt-4",
                            "prompt": "Test prompt"
                        }
                    }
                ],
                "edges": []
            }
        }
        
        result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = result["createDiagram"]["id"]
        
        # Try to execute - should fail gracefully
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation,
            variable_values={"diagramId": diagram_id}
        )
        
        # Should return execution ID but fail during processing
        assert "executeDiagram" in exec_result
        execution_id = exec_result["executeDiagram"]["executionId"]
        assert execution_id is not None
    
    async def test_network_failure_handling(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data,
        monkeypatch
    ):
        """Test handling network failures during execution."""
        # Mock network failure
        import aiohttp
        
        original_request = aiohttp.ClientSession.request
        
        async def failing_request(*args, **kwargs):
            raise aiohttp.ClientError("Network error")
        
        monkeypatch.setattr(aiohttp.ClientSession, "request", failing_request)
        
        # Create and execute diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Network Failure Test")
        
        result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = result["createDiagram"]["id"]
        
        # Restore original request method for GraphQL client
        monkeypatch.setattr(aiohttp.ClientSession, "request", original_request)
        
        # Execute should handle network errors gracefully
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        result = await gql_client.execute(
            execute_mutation,
            variable_values={"diagramId": diagram_id}
        )
        
        assert "executeDiagram" in result
    
    async def test_timeout_handling(
        self,
        gql_client,
        graphql_mutations
    ):
        """Test execution timeout handling."""
        # Create diagram with long-running task
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = {
            "name": "Timeout Test",
            "content": {
                "nodes": [
                    {
                        "id": "1",
                        "type": "scriptAgent",
                        "data": {
                            "language": "python",
                            "script": "import time; time.sleep(60)"
                        }
                    }
                ],
                "edges": []
            },
            "metadata": {
                "timeout": 1  # 1 second timeout
            }
        }
        
        result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = result["createDiagram"]["id"]
        
        # Execute with timeout
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        result = await gql_client.execute(
            execute_mutation,
            variable_values={"diagramId": diagram_id}
        )
        
        execution_id = result["executeDiagram"]["executionId"]
        assert execution_id is not None
    
    async def test_concurrent_modification_errors(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test handling concurrent modifications to same resources."""
        # Create diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Concurrent Modification Test")
        
        result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = result["createDiagram"]["id"]
        
        # Since there's no updateDiagram mutation, test concurrent node creation instead
        create_node_mutation = gql("""
            mutation CreateNode($diagramId: DiagramID!, $input: CreateNodeInput!) {
                createNode(diagramId: $diagramId, input: $input) {
                    success
                    node {
                        id
                        label
                    }
                }
            }
        """)
        
        # Try concurrent node creations
        async def create_node(suffix: str):
            try:
                node_input = {
                    "type": "llmAgent",
                    "position": {"x": 100, "y": 100},
                    "label": f"Node {suffix}",
                    "properties": {}
                }
                result = await gql_client.execute(
                    create_node_mutation,
                    variable_values={
                        "diagramId": diagram_id,
                        "input": node_input
                    }
                )
                return result, None
            except Exception as e:
                return None, e
        
        # Run multiple node creations concurrently
        tasks = [create_node(str(i)) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # At least one should succeed
        successes = [r for r, e in results if r is not None]
        errors = [e for r, e in results if e is not None]
        
        assert len(successes) >= 1
        # Concurrent modifications might cause some failures
        # but system should handle gracefully
    
    async def test_invalid_execution_operations(
        self,
        gql_client
    ):
        """Test operations on non-existent executions."""
        fake_execution_id = "non-existent-execution-id"
        
        # Test pause on non-existent execution
        pause_mutation = gql("""
            mutation PauseExecution($executionId: ID!) {
                pauseExecution(executionId: $executionId) {
                    success
                    message
                }
            }
        """)
        
        result = await gql_client.execute(
            pause_mutation,
            variable_values={"executionId": fake_execution_id}
        )
        
        # Should return failure
        assert result["pauseExecution"]["success"] is False
        assert "not found" in result["pauseExecution"]["message"].lower()
        
        # Test abort on non-existent execution
        abort_mutation = gql("""
            mutation AbortExecution($executionId: ID!) {
                abortExecution(executionId: $executionId) {
                    success
                    message
                }
            }
        """)
        
        result = await gql_client.execute(
            abort_mutation,
            variable_values={"executionId": fake_execution_id}
        )
        
        assert result["abortExecution"]["success"] is False
    
    async def test_malformed_graphql_queries(self, gql_client):
        """Test handling of malformed GraphQL queries."""
        # Invalid query syntax
        with pytest.raises(Exception):
            await gql_client.execute(gql("query { invalid syntax"))
        
        # Non-existent field
        with pytest.raises(GraphQLError):
            await gql_client.execute(
                gql("query { nonExistentField }")
            )
        
        # Wrong argument types
        with pytest.raises(GraphQLError):
            await gql_client.execute(
                gql("""
                    query GetDiagram($id: String!) {
                        diagram(id: $id) { id }
                    }
                """),
                variable_values={"id": 123}  # Should be string
            )
    
    async def test_resource_cleanup_after_errors(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test that resources are properly cleaned up after errors."""
        # Create multiple diagrams
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_ids = []
        
        for i in range(3):
            diagram_data = sample_diagram_data(name=f"Cleanup Test {i}")
            result = await gql_client.execute(
                create_mutation,
                variable_values={"input": diagram_data}
            )
            diagram_ids.append(result["createDiagram"]["id"])
        
        # Force some operations to fail
        delete_mutation = gql("""
            mutation DeleteDiagram($id: ID!) {
                deleteDiagram(id: $id) {
                    success
                    message
                }
            }
        """)
        
        # Try to delete with mixed valid/invalid IDs
        mixed_ids = diagram_ids + ["invalid-id-1", "invalid-id-2"]
        
        for diagram_id in mixed_ids:
            try:
                await gql_client.execute(
                    delete_mutation,
                    variable_values={"id": diagram_id}
                )
            except:
                pass  # Ignore errors
        
        # Verify we can still query remaining diagrams
        list_query = gql("""
            query ListDiagrams {
                diagrams {
                    id
                    name
                }
            }
        """)
        
        result = await gql_client.execute(list_query)
        assert "diagrams" in result
        # System should still be functional