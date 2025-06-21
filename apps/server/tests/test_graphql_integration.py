"""
Integration tests for GraphQL API covering the happy path.
Tests query → mutation → subscription flow.
"""
import pytest
import asyncio
import json
from typing import Dict, Any, AsyncGenerator
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from httpx import AsyncClient
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.websockets import WebsocketsTransport

# Test configuration
GRAPHQL_URL = "http://localhost:8000/graphql"
GRAPHQL_WS_URL = "ws://localhost:8000/graphql"

@pytest.fixture
async def gql_client():
    """Create GraphQL client for testing."""
    transport = AIOHTTPTransport(url=GRAPHQL_URL)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    return client

@pytest.fixture
async def gql_ws_client():
    """Create GraphQL WebSocket client for subscriptions."""
    transport = WebsocketsTransport(url=GRAPHQL_WS_URL)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    return client

@pytest.fixture
def sample_diagram() -> Dict[str, Any]:
    """Sample diagram for testing."""
    return {
        "nodes": {
            "start_1": {
                "id": "start_1",
                "type": "start",
                "label": "Test Start",
                "props": {
                    "staticData": {"message": "Hello from test"}
                }
            },
            "person_1": {
                "id": "person_1", 
                "type": "person_job",
                "label": "Test Person",
                "props": {
                    "personId": "test_person",
                    "task": "Echo the message: {{message}}"
                }
            },
            "end_1": {
                "id": "end_1",
                "type": "endpoint",
                "label": "Test End",
                "props": {
                    "outputType": "result"
                }
            }
        },
        "arrows": {
            "arrow_1": {
                "id": "arrow_1",
                "source": "start_1:output",
                "target": "person_1:input"
            },
            "arrow_2": {
                "id": "arrow_2",
                "source": "person_1:output",
                "target": "end_1:input"
            }
        },
        "handles": {
            "start_1:output": {"nodeId": "start_1", "name": "output", "type": "source"},
            "person_1:input": {"nodeId": "person_1", "name": "input", "type": "target"},
            "person_1:output": {"nodeId": "person_1", "name": "output", "type": "source"},
            "end_1:input": {"nodeId": "end_1", "name": "input", "type": "target"}
        },
        "persons": {
            "test_person": {
                "id": "test_person",
                "label": "Test Person",
                "model": "gpt-4.1-nano",
                "apiKeyId": "test_key"
            }
        },
        "apiKeys": {
            "test_key": {
                "id": "test_key",
                "label": "Test Key",
                "service": "openai",
                "key": "test-api-key"
            }
        },
        "metadata": {
            "name": "Test Diagram",
            "version": "2.0.0"
        }
    }

@pytest.mark.asyncio
async def test_graphql_happy_path(gql_client, gql_ws_client, sample_diagram):
    """Test the complete GraphQL flow: create diagram → execute → monitor."""
    
    # Step 1: Import diagram via mutation
    import_mutation = gql("""
        mutation ImportDiagram($input: ImportYamlInput!) {
            importYamlDiagram(input: $input) {
                success
                diagram {
                    id
                    name
                    nodeCount
                }
                message
            }
        }
    """)
    
    import yaml
    yaml_content = yaml.dump(sample_diagram, default_flow_style=False)
    
    result = await gql_client.execute_async(
        import_mutation,
        variable_values={
            "input": {
                "yamlContent": yaml_content,
                "filename": "test_diagram.yaml"
            }
        }
    )
    
    assert result["importYamlDiagram"]["success"] == True
    diagram_id = result["importYamlDiagram"]["diagram"]["id"]
    assert diagram_id is not None
    assert result["importYamlDiagram"]["diagram"]["nodeCount"] == 3
    
    # Step 2: Query the diagram to verify it was saved
    query_diagram = gql("""
        query GetDiagram($id: String!) {
            diagram(id: $id) {
                id
                name
                nodes {
                    id
                    type
                    label
                }
            }
        }
    """)
    
    result = await gql_client.execute_async(
        query_diagram,
        variable_values={"id": diagram_id}
    )
    
    assert result["diagram"]["id"] == diagram_id
    assert result["diagram"]["name"] == "Test Diagram"
    assert len(result["diagram"]["nodes"]) == 3
    
    # Step 3: Execute the diagram
    execute_mutation = gql("""
        mutation ExecuteDiagram($diagramId: String!, $mode: ExecutionMode) {
            executeDiagram(diagramId: $diagramId, mode: $mode) {
                executionId
                status
            }
        }
    """)
    
    result = await gql_client.execute_async(
        execute_mutation,
        variable_values={
            "diagramId": diagram_id,
            "mode": "STANDARD"
        }
    )
    
    execution_id = result["executeDiagram"]["executionId"]
    assert execution_id is not None
    assert result["executeDiagram"]["status"] == "STARTED"
    
    # Step 4: Subscribe to execution updates
    subscription = gql("""
        subscription ExecutionUpdates($executionId: String!) {
            executionUpdates(executionId: $executionId) {
                status
                nodeId
                result
                error
            }
        }
    """)
    
    # Collect events for verification
    events = []
    max_events = 10
    timeout = 30  # seconds
    
    async with gql_ws_client as session:
        sub = session.subscribe(
            subscription,
            variable_values={"executionId": execution_id}
        )
        
        try:
            async for result in sub:
                events.append(result["executionUpdates"])
                
                # Check if execution is complete
                if result["executionUpdates"]["status"] in ["COMPLETED", "FAILED"]:
                    break
                    
                if len(events) >= max_events:
                    break
                    
        except asyncio.TimeoutError:
            pytest.fail(f"Subscription timeout after {timeout} seconds")
    
    # Verify we received events
    assert len(events) > 0
    
    # Check that we have both node updates and completion
    node_events = [e for e in events if e["nodeId"] is not None]
    completion_events = [e for e in events if e["status"] == "COMPLETED"]
    
    assert len(node_events) > 0, "Should have received node update events"
    assert len(completion_events) > 0, "Should have received completion event"
    
    # Step 5: Query final execution state
    query_execution = gql("""
        query GetExecution($id: String!) {
            execution(id: $id) {
                id
                status
                startedAt
                completedAt
                outputs
            }
        }
    """)
    
    result = await gql_client.execute_async(
        query_execution,
        variable_values={"id": execution_id}
    )
    
    assert result["execution"]["id"] == execution_id
    assert result["execution"]["status"] == "COMPLETED"
    assert result["execution"]["outputs"] is not None

@pytest.mark.asyncio
async def test_graphql_control_mutations(gql_client, sample_diagram):
    """Test execution control mutations: pause, resume, abort."""
    
    # First, create and start a diagram with a delay
    import yaml
    
    # Modify diagram to add delay
    slow_diagram = sample_diagram.copy()
    slow_diagram["nodes"]["delay_1"] = {
        "id": "delay_1",
        "type": "job",
        "label": "Delay Node",
        "props": {
            "language": "python",
            "code": "import time; time.sleep(5); return {'delayed': True}"
        }
    }
    
    # Re-route arrows through delay
    slow_diagram["arrows"]["arrow_1"]["target"] = "delay_1:input"
    slow_diagram["arrows"]["arrow_1_5"] = {
        "id": "arrow_1_5",
        "source": "delay_1:output",
        "target": "person_1:input"
    }
    slow_diagram["handles"]["delay_1:input"] = {"nodeId": "delay_1", "name": "input", "type": "target"}
    slow_diagram["handles"]["delay_1:output"] = {"nodeId": "delay_1", "name": "output", "type": "source"}
    
    # Import the slow diagram
    import_mutation = gql("""
        mutation ImportDiagram($input: ImportYamlInput!) {
            importYamlDiagram(input: $input) {
                success
                diagram { id }
            }
        }
    """)
    
    yaml_content = yaml.dump(slow_diagram, default_flow_style=False)
    result = await gql_client.execute_async(
        import_mutation,
        variable_values={
            "input": {
                "yamlContent": yaml_content,
                "filename": "slow_test.yaml"
            }
        }
    )
    
    diagram_id = result["importYamlDiagram"]["diagram"]["id"]
    
    # Start execution
    execute_mutation = gql("""
        mutation ExecuteDiagram($diagramId: String!) {
            executeDiagram(diagramId: $diagramId) {
                executionId
                status
            }
        }
    """)
    
    result = await gql_client.execute_async(
        execute_mutation,
        variable_values={"diagramId": diagram_id}
    )
    
    execution_id = result["executeDiagram"]["executionId"]
    
    # Wait a bit then pause
    await asyncio.sleep(1)
    
    control_mutation = gql("""
        mutation ControlExecution($executionId: String!, $action: ExecutionAction!) {
            controlExecution(executionId: $executionId, action: $action) {
                success
                message
            }
        }
    """)
    
    # Test pause
    result = await gql_client.execute_async(
        control_mutation,
        variable_values={
            "executionId": execution_id,
            "action": "PAUSE"
        }
    )
    assert result["controlExecution"]["success"] == True
    
    # Test resume  
    result = await gql_client.execute_async(
        control_mutation,
        variable_values={
            "executionId": execution_id,
            "action": "RESUME"
        }
    )
    assert result["controlExecution"]["success"] == True
    
    # Test abort
    result = await gql_client.execute_async(
        control_mutation,
        variable_values={
            "executionId": execution_id,
            "action": "ABORT"
        }
    )
    assert result["controlExecution"]["success"] == True

@pytest.mark.asyncio 
async def test_graphql_interactive_prompts(gql_client, gql_ws_client):
    """Test interactive prompt handling via GraphQL."""
    
    # Create diagram with user_response node
    interactive_diagram = {
        "nodes": {
            "start_1": {
                "id": "start_1",
                "type": "start",
                "label": "Start",
                "props": {"staticData": {}}
            },
            "prompt_1": {
                "id": "prompt_1",
                "type": "user_response",
                "label": "User Input",
                "props": {
                    "prompt": "Please enter your name:",
                    "timeout": 30
                }
            },
            "end_1": {
                "id": "end_1",
                "type": "endpoint",
                "label": "End",
                "props": {"outputType": "result"}
            }
        },
        "arrows": {
            "a1": {
                "id": "a1",
                "source": "start_1:output",
                "target": "prompt_1:input"
            },
            "a2": {
                "id": "a2",
                "source": "prompt_1:output",
                "target": "end_1:input"
            }
        },
        "handles": {
            "start_1:output": {"nodeId": "start_1", "name": "output", "type": "source"},
            "prompt_1:input": {"nodeId": "prompt_1", "name": "input", "type": "target"},
            "prompt_1:output": {"nodeId": "prompt_1", "name": "output", "type": "source"},
            "end_1:input": {"nodeId": "end_1", "name": "input", "type": "target"}
        },
        "metadata": {"name": "Interactive Test", "version": "2.0.0"}
    }
    
    # Import diagram
    import yaml
    yaml_content = yaml.dump(interactive_diagram, default_flow_style=False)
    
    import_result = await gql_client.execute_async(
        gql("""
            mutation ImportDiagram($input: ImportYamlInput!) {
                importYamlDiagram(input: $input) {
                    success
                    diagram { id }
                }
            }
        """),
        variable_values={
            "input": {
                "yamlContent": yaml_content,
                "filename": "interactive.yaml"
            }
        }
    )
    
    diagram_id = import_result["importYamlDiagram"]["diagram"]["id"]
    
    # Execute diagram
    exec_result = await gql_client.execute_async(
        gql("""
            mutation ExecuteDiagram($diagramId: String!) {
                executeDiagram(diagramId: $diagramId) {
                    executionId
                }
            }
        """),
        variable_values={"diagramId": diagram_id}
    )
    
    execution_id = exec_result["executeDiagram"]["executionId"]
    
    # Subscribe to prompts
    prompt_sub = gql("""
        subscription InteractivePrompts($executionId: String!) {
            interactivePrompts(executionId: $executionId) {
                nodeId
                prompt
                timeout
            }
        }
    """)
    
    # Listen for prompt in background
    prompt_received = False
    prompt_node_id = None
    
    async def listen_for_prompts():
        nonlocal prompt_received, prompt_node_id
        async with gql_ws_client as session:
            sub = session.subscribe(
                prompt_sub,
                variable_values={"executionId": execution_id}
            )
            async for result in sub:
                prompt_data = result["interactivePrompts"]
                if prompt_data["prompt"] == "Please enter your name:":
                    prompt_received = True
                    prompt_node_id = prompt_data["nodeId"]
                    break
    
    # Start listening
    listen_task = asyncio.create_task(listen_for_prompts())
    
    # Wait for prompt
    await asyncio.sleep(2)
    
    # Verify prompt was received
    assert prompt_received == True
    assert prompt_node_id == "prompt_1"
    
    # Submit response
    response_mutation = gql("""
        mutation SubmitResponse($executionId: String!, $nodeId: String!, $response: String!) {
            submitInteractiveResponse(
                executionId: $executionId,
                nodeId: $nodeId, 
                response: $response
            ) {
                success
                message
            }
        }
    """)
    
    result = await gql_client.execute_async(
        response_mutation,
        variable_values={
            "executionId": execution_id,
            "nodeId": prompt_node_id,
            "response": "Test User"
        }
    )
    
    assert result["submitInteractiveResponse"]["success"] == True
    
    # Clean up
    listen_task.cancel()

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])