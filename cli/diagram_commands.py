"""
Diagram management commands using GraphQL
"""
from typing import Dict, Any, List, Optional
from gql import gql
from cli.graphql_client import DiPeoGraphQLClient


async def list_diagrams() -> List[Dict[str, Any]]:
    """List all saved diagrams."""
    query = gql("""
        query ListDiagrams {
            diagrams {
                id
                name
                description
                created_at
                updated_at
            }
        }
    """)
    
    async with DiPeoGraphQLClient() as client:
        result = await client._client.execute_async(query)
        return result["diagrams"]


async def save_diagram(diagram: Dict[str, Any], name: str, description: str = "") -> Dict[str, Any]:
    """Save a diagram."""
    mutation = gql("""
        mutation SaveDiagram($input: SaveDiagramInput!) {
            saveDiagram(input: $input) {
                ... on Diagram {
                    id
                    name
                    created_at
                }
                ... on OperationError {
                    error
                    details
                }
            }
        }
    """)
    
    async with DiPeoGraphQLClient() as client:
        result = await client._client.execute_async(
            mutation,
            variable_values={
                "input": {
                    "name": name,
                    "description": description,
                    "diagram": diagram
                }
            }
        )
        return result["saveDiagram"]


async def load_diagram(diagram_id: str) -> Dict[str, Any]:
    """Load a diagram by ID."""
    query = gql("""
        query LoadDiagram($id: String!) {
            diagram(id: $id) {
                id
                name
                description
                content
                created_at
                updated_at
            }
        }
    """)
    
    async with DiPeoGraphQLClient() as client:
        result = await client._client.execute_async(
            query,
            variable_values={"id": diagram_id}
        )
        return result["diagram"]


async def delete_diagram(diagram_id: str) -> bool:
    """Delete a diagram by ID."""
    mutation = gql("""
        mutation DeleteDiagram($id: String!) {
            deleteDiagram(id: $id) {
                success
                message
            }
        }
    """)
    
    async with DiPeoGraphQLClient() as client:
        result = await client._client.execute_async(
            mutation,
            variable_values={"id": diagram_id}
        )
        return result["deleteDiagram"]["success"]


async def list_executions(diagram_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List executions, optionally filtered by diagram ID."""
    query = gql("""
        query ListExecutions($diagramId: String) {
            executions(diagramId: $diagramId) {
                id
                diagramId
                status
                startedAt
                completedAt
                error
                tokenCount
            }
        }
    """)
    
    async with DiPeoGraphQLClient() as client:
        result = await client._client.execute_async(
            query,
            variable_values={"diagramId": diagram_id}
        )
        return result["executions"]


async def get_execution_details(execution_id: str) -> Dict[str, Any]:
    """Get detailed information about an execution."""
    query = gql("""
        query GetExecutionDetails($id: String!) {
            execution(id: $id) {
                id
                diagramId
                status
                startedAt
                completedAt
                error
                tokenCount
                result
                nodeStatuses {
                    nodeId
                    status
                    startedAt
                    completedAt
                    error
                }
            }
        }
    """)
    
    async with DiPeoGraphQLClient() as client:
        result = await client._client.execute_async(
            query,
            variable_values={"id": execution_id}
        )
        return result["execution"]