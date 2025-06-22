"""Test execution-related GraphQL mutations."""

import asyncio
from typing import Dict, Any

import pytest
from gql import gql

from ..conftest import *  # Import all fixtures


class TestExecutionControl:
    """Test execution control mutations."""
    
    async def test_start_execution(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test starting a diagram execution."""
        # Create diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Execution Test")
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Start execution
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        result = await gql_client.execute(
            execute_mutation,
            variable_values={
                "input": {
                    "diagramId": diagram_id,
                    "variables": {"test": "data"},
                    "debugMode": False
                }
            }
        )
        
        assert "executeDiagram" in result
        assert result["executeDiagram"]["success"] is True
        execution = result["executeDiagram"]["execution"]
        assert execution["id"] is not None
        assert execution["status"] in ["STARTED", "RUNNING"]
    
    async def test_control_execution(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test controlling execution (pause/resume/abort)."""
        # Create and start execution
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data()
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation,
            variable_values={
                "input": {
                    "diagramId": diagram_id,
                    "debugMode": True
                }
            }
        )
        execution_id = exec_result["executeDiagram"]["execution"]["id"]
        
        # Control execution
        control_mutation = gql("""
            mutation ControlExecution($input: ExecutionControlInput!) {
                controlExecution(input: $input) {
                    success
                    execution {
                        id
                        status
                    }
                    message
                }
            }
        """)
        
        # Test pause
        result = await gql_client.execute(
            control_mutation,
            variable_values={
                "input": {
                    "executionId": execution_id,
                    "action": "pause"
                }
            }
        )
        
        assert "controlExecution" in result
        assert result["controlExecution"]["success"] is True
        
        # Test resume
        result = await gql_client.execute(
            control_mutation,
            variable_values={
                "input": {
                    "executionId": execution_id,
                    "action": "resume"
                }
            }
        )
        
        assert result["controlExecution"]["success"] is True
        
        # Test abort
        result = await gql_client.execute(
            control_mutation,
            variable_values={
                "input": {
                    "executionId": execution_id,
                    "action": "abort"
                }
            }
        )
        
        assert result["controlExecution"]["success"] is True
        assert result["controlExecution"]["execution"]["status"] in ["ABORTED", "FAILED"]
    
    async def test_execution_with_timeout(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test execution with timeout settings."""
        # Create diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data()
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Execute with timeout
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        result = await gql_client.execute(
            execute_mutation,
            variable_values={
                "input": {
                    "diagramId": diagram_id,
                    "timeoutSeconds": 30,
                    "maxIterations": 100
                }
            }
        )
        
        assert "executeDiagram" in result
        assert result["executeDiagram"]["success"] is True
        execution = result["executeDiagram"]["execution"]
        assert execution["id"] is not None


class TestExecutionMonitoring:
    """Test execution monitoring queries."""
    
    async def test_get_execution_state(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test querying execution state."""
        # Create and execute diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data()
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation,
            variable_values={
                "input": {"diagramId": diagram_id}
            }
        )
        execution_id = exec_result["executeDiagram"]["execution"]["id"]
        
        # Query execution state
        execution_query = gql("""
            query GetExecution($id: ExecutionID!) {
                execution(id: $id) {
                    id
                    status
                    diagramId
                    startedAt
                    endedAt
                    isActive
                    runningNodes
                    completedNodes
                    failedNodes
                    error
                }
            }
        """)
        
        result = await gql_client.execute(
            execution_query,
            variable_values={"id": execution_id}
        )
        
        assert "execution" in result
        execution = result["execution"]
        assert execution["id"] == execution_id
        assert execution["status"] is not None
        assert execution["startedAt"] is not None
        assert execution["isActive"] in [True, False]
    
    async def test_get_execution_events(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test retrieving execution events."""
        # Create and execute diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data()
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation,
            variable_values={
                "input": {"diagramId": diagram_id}
            }
        )
        execution_id = exec_result["executeDiagram"]["execution"]["id"]
        
        # Wait a bit for events to be generated
        await asyncio.sleep(0.5)
        
        # Query events
        events_query = gql("""
            query GetExecutionEvents($executionId: ExecutionID!, $sinceSequence: Int, $limit: Int!) {
                executionEvents(executionId: $executionId, sinceSequence: $sinceSequence, limit: $limit) {
                    executionId
                    sequence
                    eventType
                    nodeId
                    timestamp
                    formattedMessage
                    data
                }
            }
        """)
        
        result = await gql_client.execute(
            events_query,
            variable_values={
                "executionId": execution_id,
                "limit": 100
            }
        )
        
        assert "executionEvents" in result
        events = result["executionEvents"]
        assert isinstance(events, list)
        
        # Should have at least a start event
        assert len(events) > 0
        assert any(e["eventType"] == "EXECUTION_STARTED" for e in events)
    
    async def test_list_executions(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test listing executions with filters."""
        # Create and start multiple executions
        create_mutation = gql(graphql_mutations["create_diagram"])
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        
        diagram_ids = []
        for i in range(3):
            diagram_data = sample_diagram_data(name=f"List Test {i}")
            create_result = await gql_client.execute(
                create_mutation,
                variable_values={"input": diagram_data}
            )
            diagram_id = create_result["createDiagram"]["diagram"]["metadata"]["id"]
            diagram_ids.append(diagram_id)
            
            await gql_client.execute(
                execute_mutation,
                variable_values={
                    "input": {"diagramId": diagram_id}
                }
            )
        
        # List all executions
        list_query = gql("""
            query ListExecutions($filter: ExecutionFilterInput, $limit: Int!, $offset: Int!) {
                executions(filter: $filter, limit: $limit, offset: $offset) {
                    id
                    status
                    diagramId
                    startedAt
                    isActive
                }
            }
        """)
        
        result = await gql_client.execute(
            list_query,
            variable_values={
                "filter": {"activeOnly": True},
                "limit": 10,
                "offset": 0
            }
        )
        
        assert "executions" in result
        executions = result["executions"]
        assert isinstance(executions, list)
        assert len(executions) >= 3
        
        # Test filtering by diagram
        result = await gql_client.execute(
            list_query,
            variable_values={
                "filter": {"diagramId": diagram_ids[0]},
                "limit": 10,
                "offset": 0
            }
        )
        
        filtered_executions = result["executions"]
        assert all(e["diagramId"] == diagram_ids[0] for e in filtered_executions)


class TestExecutionInteraction:
    """Test interactive execution features."""
    
    async def test_submit_interactive_response(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test submitting responses to interactive prompts."""
        # Create diagram with user response node
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Interactive Test")
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Add a USER_RESPONSE node
        create_node_mutation = gql(graphql_mutations["create_node"])
        node_result = await gql_client.execute(
            create_node_mutation,
            variable_values={
                "diagramId": diagram_id,
                "input": {
                    "type": "USER_RESPONSE",
                    "position": {"x": 100, "y": 100},
                    "label": "User Input",
                    "properties": {
                        "prompt": "Enter your response:"
                    }
                }
            }
        )
        node_id = node_result["createNode"]["node"]["id"]
        
        # Execute diagram
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation,
            variable_values={
                "input": {"diagramId": diagram_id}
            }
        )
        execution_id = exec_result["executeDiagram"]["execution"]["id"]
        
        # Submit interactive response
        response_mutation = gql("""
            mutation SubmitInteractiveResponse($input: InteractiveResponseInput!) {
                submitInteractiveResponse(input: $input) {
                    success
                    execution {
                        id
                        status
                    }
                    message
                }
            }
        """)
        
        result = await gql_client.execute(
            response_mutation,
            variable_values={
                "input": {
                    "executionId": execution_id,
                    "nodeId": node_id,
                    "response": "User provided input"
                }
            }
        )
        
        assert "submitInteractiveResponse" in result
        assert result["submitInteractiveResponse"]["success"] is True
    
    async def test_execution_with_direct_data(
        self,
        gql_client,
        graphql_mutations
    ):
        """Test executing with diagram data directly (no saved diagram)."""
        # Execute with inline diagram data
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        
        diagram_data = {
            "name": "Direct Execution",
            "nodes": [
                {
                    "id": "start",
                    "type": "START",
                    "position": {"x": 0, "y": 0},
                    "data": {}
                },
                {
                    "id": "end",
                    "type": "ENDPOINT",
                    "position": {"x": 200, "y": 0},
                    "data": {}
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "source": "start",
                    "target": "end"
                }
            ]
        }
        
        result = await gql_client.execute(
            execute_mutation,
            variable_values={
                "input": {
                    "diagramData": diagram_data,
                    "debugMode": True
                }
            }
        )
        
        assert "executeDiagram" in result
        assert result["executeDiagram"]["success"] is True
        execution = result["executeDiagram"]["execution"]
        assert execution["id"] is not None
        assert execution["diagramId"] is None  # No saved diagram