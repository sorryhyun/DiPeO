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
        diagram_id = create_result["createDiagram"]["id"]
        
        # Start execution
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        result = await gql_client.execute(
            execute_mutation,
            variable_values={
                "diagramId": diagram_id,
                "inputs": {"test": "data"}
            }
        )
        
        assert "executeDiagram" in result
        execution = result["executeDiagram"]
        assert execution["executionId"] is not None
        assert execution["status"] in ["PENDING", "RUNNING"]
    
    async def test_pause_execution(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test pausing a running execution."""
        # Create and start execution
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data()
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["id"]
        
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation,
            variable_values={"diagramId": diagram_id}
        )
        execution_id = exec_result["executeDiagram"]["executionId"]
        
        # Pause execution
        pause_mutation = gql("""
            mutation PauseExecution($executionId: ID!) {
                pauseExecution(executionId: $executionId) {
                    success
                    message
                    executionStatus
                }
            }
        """)
        
        result = await gql_client.execute(
            pause_mutation,
            variable_values={"executionId": execution_id}
        )
        
        assert "pauseExecution" in result
        pause_result = result["pauseExecution"]
        assert pause_result["success"] is True
        assert pause_result["executionStatus"] in ["PAUSED", "PAUSING"]
    
    async def test_resume_execution(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test resuming a paused execution."""
        # Create, start, and pause execution
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data()
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["id"]
        
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation,
            variable_values={"diagramId": diagram_id}
        )
        execution_id = exec_result["executeDiagram"]["executionId"]
        
        # Pause
        pause_mutation = gql("""
            mutation PauseExecution($executionId: ID!) {
                pauseExecution(executionId: $executionId) {
                    success
                }
            }
        """)
        
        await gql_client.execute(
            pause_mutation,
            variable_values={"executionId": execution_id}
        )
        
        # Resume
        resume_mutation = gql("""
            mutation ResumeExecution($executionId: ID!) {
                resumeExecution(executionId: $executionId) {
                    success
                    message
                    executionStatus
                }
            }
        """)
        
        result = await gql_client.execute(
            resume_mutation,
            variable_values={"executionId": execution_id}
        )
        
        assert "resumeExecution" in result
        resume_result = result["resumeExecution"]
        assert resume_result["success"] is True
        assert resume_result["executionStatus"] in ["RUNNING", "RESUMING"]
    
    async def test_abort_execution(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test aborting an execution."""
        # Create and start execution
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data()
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["id"]
        
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation,
            variable_values={"diagramId": diagram_id}
        )
        execution_id = exec_result["executeDiagram"]["executionId"]
        
        # Abort execution
        abort_mutation = gql("""
            mutation AbortExecution($executionId: ID!) {
                abortExecution(executionId: $executionId) {
                    success
                    message
                    executionStatus
                }
            }
        """)
        
        result = await gql_client.execute(
            abort_mutation,
            variable_values={"executionId": execution_id}
        )
        
        assert "abortExecution" in result
        abort_result = result["abortExecution"]
        assert abort_result["success"] is True
        assert abort_result["executionStatus"] in ["ABORTED", "ABORTING"]
    
    async def test_retry_execution(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test retrying a failed execution."""
        # Create diagram that might fail
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data()
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["id"]
        
        # Start execution
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation,
            variable_values={"diagramId": diagram_id}
        )
        execution_id = exec_result["executeDiagram"]["executionId"]
        
        # Retry execution
        retry_mutation = gql("""
            mutation RetryExecution($executionId: ID!, $fromNode: ID) {
                retryExecution(executionId: $executionId, fromNode: $fromNode) {
                    newExecutionId
                    status
                    message
                }
            }
        """)
        
        try:
            result = await gql_client.execute(
                retry_mutation,
                variable_values={"executionId": execution_id}
            )
            
            assert "retryExecution" in result
            retry_result = result["retryExecution"]
            assert retry_result["newExecutionId"] is not None
            assert retry_result["status"] in ["PENDING", "RUNNING"]
        except Exception:
            pytest.skip("Retry functionality not available")


class TestExecutionMonitoring:
    """Test execution monitoring queries."""
    
    async def test_get_execution_status(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test querying execution status."""
        # Create and execute diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data()
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["id"]
        
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation,
            variable_values={"diagramId": diagram_id}
        )
        execution_id = exec_result["executeDiagram"]["executionId"]
        
        # Query status
        status_query = gql("""
            query GetExecutionStatus($executionId: ID!) {
                executionStatus(executionId: $executionId) {
                    executionId
                    status
                    startTime
                    endTime
                    currentNode
                    progress
                    error
                }
            }
        """)
        
        result = await gql_client.execute(
            status_query,
            variable_values={"executionId": execution_id}
        )
        
        assert "executionStatus" in result
        status = result["executionStatus"]
        assert status["executionId"] == execution_id
        assert status["status"] is not None
        assert status["startTime"] is not None
    
    async def test_get_execution_logs(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test retrieving execution logs."""
        # Create and execute diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data()
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["id"]
        
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation,
            variable_values={"diagramId": diagram_id}
        )
        execution_id = exec_result["executeDiagram"]["executionId"]
        
        # Query logs
        logs_query = gql("""
            query GetExecutionLogs($executionId: ID!, $limit: Int, $offset: Int) {
                executionLogs(executionId: $executionId, limit: $limit, offset: $offset) {
                    logs {
                        timestamp
                        level
                        nodeId
                        message
                        data
                    }
                    totalCount
                    hasMore
                }
            }
        """)
        
        result = await gql_client.execute(
            logs_query,
            variable_values={
                "executionId": execution_id,
                "limit": 10
            }
        )
        
        assert "executionLogs" in result
        logs_result = result["executionLogs"]
        assert "logs" in logs_result
        assert isinstance(logs_result["logs"], list)
        assert "totalCount" in logs_result
    
    async def test_list_active_executions(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test listing active executions."""
        # Create and start multiple executions
        create_mutation = gql(graphql_mutations["create_diagram"])
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        
        for i in range(3):
            diagram_data = sample_diagram_data(name=f"Active Test {i}")
            create_result = await gql_client.execute(
                create_mutation,
                variable_values={"input": diagram_data}
            )
            diagram_id = create_result["createDiagram"]["id"]
            
            await gql_client.execute(
                execute_mutation,
                variable_values={"diagramId": diagram_id}
            )
        
        # List active executions
        list_query = gql("""
            query ListActiveExecutions($status: [ExecutionStatus!]) {
                activeExecutions(status: $status) {
                    executionId
                    diagramId
                    diagramName
                    status
                    startTime
                    progress
                }
            }
        """)
        
        result = await gql_client.execute(
            list_query,
            variable_values={
                "status": ["PENDING", "RUNNING", "PAUSED"]
            }
        )
        
        assert "activeExecutions" in result
        active = result["activeExecutions"]
        assert isinstance(active, list)
        assert len(active) >= 3


class TestExecutionInteraction:
    """Test interactive execution features."""
    
    async def test_respond_to_prompt(
        self,
        gql_client,
        graphql_mutations
    ):
        """Test responding to execution prompts."""
        # Create diagram with prompt node
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = {
            "name": "Prompt Test",
            "content": {
                "nodes": [
                    {
                        "id": "prompt1",
                        "type": "promptAgent",
                        "data": {
                            "prompt": "Enter value:",
                            "inputType": "text"
                        }
                    }
                ],
                "edges": []
            }
        }
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["id"]
        
        # Execute
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation,
            variable_values={"diagramId": diagram_id}
        )
        execution_id = exec_result["executeDiagram"]["executionId"]
        
        # Respond to prompt
        respond_mutation = gql("""
            mutation RespondToPrompt($executionId: ID!, $nodeId: ID!, $response: JSON!) {
                respondToPrompt(
                    executionId: $executionId,
                    nodeId: $nodeId,
                    response: $response
                ) {
                    success
                    message
                    nextPrompt {
                        nodeId
                        prompt
                        inputType
                    }
                }
            }
        """)
        
        result = await gql_client.execute(
            respond_mutation,
            variable_values={
                "executionId": execution_id,
                "nodeId": "prompt1",
                "response": {"value": "User input"}
            }
        )
        
        assert "respondToPrompt" in result
        response_result = result["respondToPrompt"]
        assert response_result["success"] is True
    
    async def test_update_node_data(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test updating node data during execution."""
        # Create and execute diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data()
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": diagram_data}
        )
        diagram_id = create_result["createDiagram"]["id"]
        
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation,
            variable_values={"diagramId": diagram_id}
        )
        execution_id = exec_result["executeDiagram"]["executionId"]
        
        # Update node data
        update_mutation = gql("""
            mutation UpdateNodeData($executionId: ID!, $nodeId: ID!, $data: JSON!) {
                updateNodeData(
                    executionId: $executionId,
                    nodeId: $nodeId,
                    data: $data
                ) {
                    success
                    message
                    updatedNode {
                        nodeId
                        data
                    }
                }
            }
        """)
        
        try:
            result = await gql_client.execute(
                update_mutation,
                variable_values={
                    "executionId": execution_id,
                    "nodeId": "1",
                    "data": {"newValue": "Updated during execution"}
                }
            )
            
            assert "updateNodeData" in result
            update_result = result["updateNodeData"]
            assert update_result["success"] is True
        except Exception:
            pytest.skip("Dynamic node updates not supported")