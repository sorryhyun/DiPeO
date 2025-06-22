"""Shared test fixtures and utilities for server tests."""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add the server directory to path
server_dir = Path(__file__).parent.parent
sys.path.insert(0, str(server_dir))

from main import app


# Basic fixtures
@pytest.fixture
def test_app():
    """FastAPI test app instance."""
    return app


@pytest.fixture
def test_client(test_app):
    """Synchronous test client for basic HTTP testing."""
    return TestClient(test_app)


@pytest_asyncio.fixture
async def async_client(test_app):
    """Asynchronous test client for async HTTP testing."""
    from httpx import ASGITransport

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# GraphQL fixtures
@pytest.fixture
def graphql_url():
    """GraphQL endpoint URL."""
    return "http://localhost:8000/graphql"


@pytest.fixture
def graphql_ws_url():
    """GraphQL WebSocket endpoint URL."""
    return "ws://localhost:8000/graphql"


@pytest_asyncio.fixture
async def gql_client(async_client):
    """GraphQL client that uses the async test client for requests."""

    class TestGraphQLClient:
        def __init__(self, async_client):
            self.async_client = async_client

        async def execute(self, query, variable_values=None):
            """Execute a GraphQL query using the test client."""
            # Extract the query string from the DocumentNode
            if hasattr(query, "loc") and hasattr(query.loc, "source"):
                query_str = query.loc.source.body
            else:
                query_str = str(query)

            response = await self.async_client.post(
                "/graphql",
                json={"query": query_str, "variables": variable_values or {}},
            )

            if response.status_code != 200:
                raise Exception(
                    f"GraphQL request failed with status {response.status_code}"
                )

            result = response.json()

            # Check for errors in the GraphQL response
            if "errors" in result:
                from gql.transport.exceptions import TransportQueryError

                raise TransportQueryError(str(result["errors"][0]))

            return result.get("data", {})

    yield TestGraphQLClient(async_client)


@pytest_asyncio.fixture
async def gql_ws_client(test_app):
    """GraphQL client with WebSocket transport for subscriptions."""
    # For now, skip WebSocket tests as they require a running server
    pytest.skip("WebSocket tests require a running server")
    yield None


# Test data builders
@pytest.fixture
def sample_diagram_data():
    """Factory for creating sample diagram data for createDiagram mutation."""

    def build(**overrides) -> Dict[str, Any]:
        base = {
            "name": "Test Diagram",
            "description": "A test diagram",
            "author": "Test User",
            "tags": ["test", "sample"],
        }
        return {**base, **overrides}

    return build


@pytest.fixture
def sample_person_data():
    """Factory for creating sample person data."""

    def build(**overrides) -> Dict[str, Any]:
        base = {
            "label": "Test Assistant",
            "service": "OPENAI",
            "model": "gpt-4.1-nano",
            "apiKeyId": "test-api-key-id",
            "systemPrompt": "You are a helpful assistant.",
            "forgettingMode": "NO_FORGET",
            "temperature": 0.7,
            "maxTokens": 1000,
            "topP": 1.0,
        }
        return {**base, **overrides}

    return build


@pytest.fixture
def sample_api_key_data():
    """Factory for creating sample API key data."""

    def build(**overrides) -> Dict[str, Any]:
        base = {"provider": "OPENAI", "key": "test-api-key", "model": "gpt-4.1-nano"}
        return {**base, **overrides}

    return build


# File fixtures
@pytest.fixture
def temp_diagram_file(tmp_path, sample_diagram_data):
    """Create a temporary diagram file for testing."""

    def create(filename="test_diagram.json", **diagram_overrides):
        file_path = tmp_path / filename
        import json

        data = sample_diagram_data(**diagram_overrides)
        file_path.write_text(json.dumps(data))
        return str(file_path)

    return create


@pytest.fixture
def temp_yaml_diagram_file(tmp_path):
    """Create a temporary YAML diagram file for testing."""

    def create(filename="test_diagram.yaml"):
        file_path = tmp_path / filename
        content = """
name: Test YAML Diagram
nodes:
  - id: input1
    type: inputAgent
    data:
      type: text
      value: Hello from YAML
edges:
  - source: input1
    target: output1
"""
        file_path.write_text(content)
        return str(file_path)

    return create


# GraphQL query/mutation helpers
@pytest.fixture
def graphql_queries():
    """Common GraphQL queries for testing."""
    return {
        "health": """
            query Health {
                health
            }
        """,
        "list_diagrams": """
            query ListDiagrams($limit: Int!, $offset: Int!) {
                diagrams(limit: $limit, offset: $offset) {
                    metadata {
                        id
                        name
                        created
                        modified
                    }
                    nodeCount
                    arrowCount
                }
            }
        """,
        "get_diagram": """
            query GetDiagram($id: DiagramID!) {
                diagram(id: $id) {
                    metadata {
                        id
                        name
                        description
                    }
                    nodes {
                        id
                        type
                    }
                    arrows {
                        id
                        source
                        target
                    }
                }
            }
        """,
        "list_people": """
            query ListPeople($limit: Int!) {
                persons(limit: $limit) {
                    id
                    label
                    service
                    model
                }
            }
        """,
    }


@pytest.fixture
def graphql_mutations():
    """Common GraphQL mutations for testing."""
    return {
        "create_diagram": """
            mutation CreateDiagram($input: CreateDiagramInput!) {
                createDiagram(input: $input) {
                    success
                    diagram {
                        metadata {
                            id
                            name
                            created
                        }
                    }
                    message
                    error
                }
            }
        """,
        "execute_diagram": """
            mutation ExecuteDiagram($input: ExecuteDiagramInput!) {
                executeDiagram(input: $input) {
                    success
                    execution {
                        id
                        status
                    }
                    message
                    error
                }
            }
        """,
        "create_person": """
            mutation CreatePerson($diagramId: DiagramID!, $input: CreatePersonInput!) {
                createPerson(diagramId: $diagramId, input: $input) {
                    success
                    person {
                        id
                        label
                        service
                    }
                    message
                    error
                }
            }
        """,
        "upload_file": """
            mutation UploadFile($input: FileUploadInput!) {
                uploadFile(input: $input) {
                    success
                    diagramId
                    message
                    errors
                }
            }
        """,
        "create_node": """
            mutation CreateNode($diagramId: DiagramID!, $input: CreateNodeInput!) {
                createNode(diagramId: $diagramId, input: $input) {
                    success
                    node {
                        id
                        type
                        position {
                            x
                            y
                        }
                    }
                    message
                    error
                }
            }
        """,
        "update_person": """
            mutation UpdatePerson($input: UpdatePersonInput!) {
                updatePerson(input: $input) {
                    success
                    person {
                        id
                        label
                        model
                    }
                    message
                    error
                }
            }
        """,
        "delete_person": """
            mutation DeletePerson($id: PersonID!) {
                deletePerson(id: $id) {
                    success
                    message
                }
            }
        """,
        "upload_diagram": """
            mutation UploadDiagram($file: Upload!, $format: String, $validateOnly: Boolean!) {
                uploadDiagram(file: $file, format: $format, validateOnly: $validateOnly) {
                    success
                    message
                    diagramId
                    diagramName
                    nodeCount
                    formatDetected
                }
            }
        """,
    }


@pytest.fixture
def graphql_subscriptions():
    """Common GraphQL subscriptions for testing."""
    return {
        "execution_updates": """
            subscription ExecutionUpdates($executionId: ID!) {
                executionUpdates(executionId: $executionId) {
                    nodeId
                    status
                    output
                    error
                    timestamp
                }
            }
        """
    }


# Utility functions
@pytest.fixture
def wait_for_condition():
    """Utility to wait for a condition with timeout."""

    async def wait(condition_func, timeout=5, interval=0.1):
        start = asyncio.get_event_loop().time()
        while True:
            if await condition_func():
                return True
            if asyncio.get_event_loop().time() - start > timeout:
                raise TimeoutError(f"Condition not met within {timeout} seconds")
            await asyncio.sleep(interval)

    return wait


@pytest.fixture
def mock_llm_response():
    """Mock LLM responses for testing."""

    def mock(content="Test response", model="gpt-4.1-nano"):
        return {
            "content": content,
            "model": model,
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

    return mock


# Environment setup
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("DIPEO_ENV", "test")
    monkeypatch.setenv("DIPEO_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
