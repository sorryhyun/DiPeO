"""Integration tests for diagram execution flow."""

import asyncio

from gql import gql

from ..conftest import *  # Import all fixtures


class TestDiagramExecutionFlow:
    """Test complete diagram execution workflows."""

    async def test_simple_execution_flow(
        self, gql_client, graphql_mutations, sample_diagram_data
    ):
        """Test basic diagram creation and execution flow."""
        # Create diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Simple Execution Test")

        result = await gql_client.execute(
            create_mutation, variable_values={"input": diagram_data}
        )

        assert "createDiagram" in result
        diagram_id = result["createDiagram"]["id"]
        assert diagram_id is not None

        # Execute diagram
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        result = await gql_client.execute(
            execute_mutation,
            variable_values={
                "diagramId": diagram_id,
                "inputs": {"initial_data": "test"},
            },
        )

        assert "executeDiagram" in result
        execution = result["executeDiagram"]
        assert execution["executionId"] is not None
        assert execution["status"] == "PENDING"

    async def test_execution_with_monitoring(
        self,
        gql_client,
        gql_ws_client,
        graphql_mutations,
        graphql_subscriptions,
        sample_diagram_data,
        wait_for_condition,
    ):
        """Test execution with real-time monitoring via subscriptions."""
        # Create diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(
            name="Monitored Execution Test",
            content={
                "nodes": [
                    {
                        "id": "1",
                        "type": "inputAgent",
                        "data": {"type": "text", "value": "Test input"},
                    },
                    {
                        "id": "2",
                        "type": "llmAgent",
                        "data": {"model": "gpt-4.1-nano", "prompt": "Process: {input}"},
                    },
                ],
                "edges": [
                    {
                        "source": "1",
                        "target": "2",
                        "sourceHandle": "output",
                        "targetHandle": "input",
                    }
                ],
            },
        )

        result = await gql_client.execute(
            create_mutation, variable_values={"input": diagram_data}
        )
        diagram_id = result["createDiagram"]["id"]

        # Set up subscription
        subscription = gql(graphql_subscriptions["execution_updates"])
        updates = []

        async def collect_updates():
            async for result in gql_ws_client.subscribe(
                subscription, variable_values={"executionId": execution_id}
            ):
                update = result["executionUpdates"]
                updates.append(update)
                if update["status"] in ["COMPLETED", "FAILED"]:
                    break

        # Execute diagram
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation, variable_values={"diagramId": diagram_id}
        )
        execution_id = exec_result["executeDiagram"]["executionId"]

        # Collect updates
        update_task = asyncio.create_task(collect_updates())

        # Wait for completion
        await wait_for_condition(
            lambda: len(updates) > 0 and updates[-1]["status"] == "COMPLETED",
            timeout=10,
        )

        # Verify updates
        assert len(updates) >= 2  # At least start and complete
        assert any(u["nodeId"] == "1" for u in updates)
        assert any(u["nodeId"] == "2" for u in updates)
        assert updates[-1]["status"] == "COMPLETED"

    async def test_execution_error_handling(
        self, gql_client, graphql_mutations, sample_diagram_data
    ):
        """Test execution error handling."""
        # Create diagram with invalid configuration
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(
            name="Error Test Diagram",
            content={
                "nodes": [
                    {
                        "id": "1",
                        "type": "llmAgent",
                        "data": {
                            "model": "invalid-model",
                            "prompt": "This should fail",
                        },
                    }
                ],
                "edges": [],
            },
        )

        result = await gql_client.execute(
            create_mutation, variable_values={"input": diagram_data}
        )
        diagram_id = result["createDiagram"]["id"]

        # Execute should handle error gracefully
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        result = await gql_client.execute(
            execute_mutation, variable_values={"diagramId": diagram_id}
        )

        assert "executeDiagram" in result
        execution = result["executeDiagram"]
        assert execution["executionId"] is not None
        # Status should indicate failure or error state
        assert execution["status"] in ["PENDING", "RUNNING", "FAILED"]

    async def test_parallel_executions(
        self, gql_client, graphql_mutations, sample_diagram_data
    ):
        """Test running multiple executions in parallel."""
        # Create diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Parallel Execution Test")

        result = await gql_client.execute(
            create_mutation, variable_values={"input": diagram_data}
        )
        diagram_id = result["createDiagram"]["id"]

        # Execute multiple times in parallel
        execute_mutation = gql(graphql_mutations["execute_diagram"])

        async def execute_diagram(index: int):
            result = await gql_client.execute(
                execute_mutation,
                variable_values={
                    "diagramId": diagram_id,
                    "inputs": {"run_index": index},
                },
            )
            return result["executeDiagram"]["executionId"]

        # Run 5 parallel executions
        tasks = [execute_diagram(i) for i in range(5)]
        execution_ids = await asyncio.gather(*tasks)

        # All should have unique execution IDs
        assert len(execution_ids) == 5
        assert len(set(execution_ids)) == 5  # All unique

        # All executions should be valid
        for exec_id in execution_ids:
            assert exec_id is not None
            assert isinstance(exec_id, str)

    async def test_execution_with_custom_inputs(
        self, gql_client, graphql_mutations, sample_diagram_data
    ):
        """Test execution with various input types."""
        # Create diagram that accepts inputs
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(
            name="Custom Input Test",
            content={
                "nodes": [
                    {"id": "1", "type": "inputAgent", "data": {"type": "dynamic"}}
                ],
                "edges": [],
            },
        )

        result = await gql_client.execute(
            create_mutation, variable_values={"input": diagram_data}
        )
        diagram_id = result["createDiagram"]["id"]

        # Test various input types
        test_inputs = [
            {"text": "Simple string input"},
            {"number": 42},
            {"array": [1, 2, 3]},
            {"nested": {"key": "value", "list": ["a", "b"]}},
            {"mixed": {"text": "hello", "number": 123, "bool": True}},
        ]

        execute_mutation = gql(graphql_mutations["execute_diagram"])

        for inputs in test_inputs:
            result = await gql_client.execute(
                execute_mutation,
                variable_values={"diagramId": diagram_id, "inputs": inputs},
            )

            assert "executeDiagram" in result
            execution = result["executeDiagram"]
            assert execution["executionId"] is not None
            assert execution["status"] == "PENDING"
