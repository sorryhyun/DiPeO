"""Integration tests for interactive execution features."""

import asyncio
from typing import Any, Dict, List

from gql import gql

from ..conftest import *  # Import all fixtures


class TestInteractiveExecution:
    """Test interactive prompt handling during execution."""

    async def test_execution_pause_resume(
        self, gql_client, graphql_mutations, sample_diagram_data
    ):
        """Test pausing and resuming execution."""
        # Create diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Pause/Resume Test")

        result = await gql_client.execute(
            create_mutation, variable_values={"input": diagram_data}
        )
        diagram_id = result["createDiagram"]["id"]

        # Start execution
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        result = await gql_client.execute(
            execute_mutation, variable_values={"diagramId": diagram_id}
        )
        execution_id = result["executeDiagram"]["executionId"]

        # Define pause mutation
        pause_mutation = gql("""
            mutation PauseExecution($executionId: ID!) {
                pauseExecution(executionId: $executionId) {
                    success
                    message
                }
            }
        """)

        # Pause execution
        pause_result = await gql_client.execute(
            pause_mutation, variable_values={"executionId": execution_id}
        )
        assert pause_result["pauseExecution"]["success"] is True

        # Define resume mutation
        resume_mutation = gql("""
            mutation ResumeExecution($executionId: ID!) {
                resumeExecution(executionId: $executionId) {
                    success
                    message
                }
            }
        """)

        # Resume execution
        resume_result = await gql_client.execute(
            resume_mutation, variable_values={"executionId": execution_id}
        )
        assert resume_result["resumeExecution"]["success"] is True

    async def test_execution_abort(
        self, gql_client, graphql_mutations, sample_diagram_data
    ):
        """Test aborting an execution."""
        # Create diagram
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data(name="Abort Test")

        result = await gql_client.execute(
            create_mutation, variable_values={"input": diagram_data}
        )
        diagram_id = result["createDiagram"]["id"]

        # Start execution
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        result = await gql_client.execute(
            execute_mutation, variable_values={"diagramId": diagram_id}
        )
        execution_id = result["executeDiagram"]["executionId"]

        # Define abort mutation
        abort_mutation = gql("""
            mutation AbortExecution($executionId: ID!) {
                abortExecution(executionId: $executionId) {
                    success
                    message
                }
            }
        """)

        # Abort execution
        abort_result = await gql_client.execute(
            abort_mutation, variable_values={"executionId": execution_id}
        )
        assert abort_result["abortExecution"]["success"] is True

    async def test_interactive_prompt_handling(
        self,
        gql_client,
        gql_ws_client,
        graphql_mutations,
        graphql_subscriptions,
        wait_for_condition,
    ):
        """Test handling interactive prompts during execution."""
        # Create diagram with interactive node
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = {
            "name": "Interactive Prompt Test",
            "content": {
                "nodes": [
                    {
                        "id": "1",
                        "type": "promptAgent",
                        "data": {
                            "prompt": "Enter your name:",
                            "validation": {"required": True},
                        },
                    },
                    {
                        "id": "2",
                        "type": "llmAgent",
                        "data": {"model": "gpt-4.1-nano", "prompt": "Hello, {name}!"},
                    },
                ],
                "edges": [
                    {
                        "source": "1",
                        "target": "2",
                        "sourceHandle": "output",
                        "targetHandle": "name",
                    }
                ],
            },
        }

        result = await gql_client.execute(
            create_mutation, variable_values={"input": diagram_data}
        )
        diagram_id = result["createDiagram"]["id"]

        # Set up subscription to monitor for prompts
        subscription = gql(graphql_subscriptions["execution_updates"])
        updates: List[Dict[str, Any]] = []
        prompt_received = asyncio.Event()

        async def collect_updates():
            async for result in gql_ws_client.subscribe(
                subscription, variable_values={"executionId": execution_id}
            ):
                update = result["executionUpdates"]
                updates.append(update)

                # Check for prompt
                if update.get("status") == "WAITING_FOR_INPUT":
                    prompt_received.set()

                if update["status"] in ["COMPLETED", "FAILED"]:
                    break

        # Start execution
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        exec_result = await gql_client.execute(
            execute_mutation, variable_values={"diagramId": diagram_id}
        )
        execution_id = exec_result["executeDiagram"]["executionId"]

        # Start monitoring
        update_task = asyncio.create_task(collect_updates())

        # Wait for prompt
        await asyncio.wait_for(prompt_received.wait(), timeout=5)

        # Send response to prompt
        respond_mutation = gql("""
            mutation RespondToPrompt($executionId: ID!, $nodeId: ID!, $response: JSON!) {
                respondToPrompt(
                    executionId: $executionId,
                    nodeId: $nodeId,
                    response: $response
                ) {
                    success
                    message
                }
            }
        """)

        # Find the prompt node ID from updates
        prompt_update = next(
            u for u in updates if u.get("status") == "WAITING_FOR_INPUT"
        )

        response_result = await gql_client.execute(
            respond_mutation,
            variable_values={
                "executionId": execution_id,
                "nodeId": prompt_update["nodeId"],
                "response": {"value": "Test User"},
            },
        )
        assert response_result["respondToPrompt"]["success"] is True

        # Wait for completion
        await wait_for_condition(
            lambda: len(updates) > 0 and updates[-1]["status"] == "COMPLETED",
            timeout=10,
        )

        # Verify the prompt was handled
        assert any(u.get("status") == "WAITING_FOR_INPUT" for u in updates)
        assert updates[-1]["status"] == "COMPLETED"

    async def test_multiple_prompts_sequence(self, gql_client, graphql_mutations):
        """Test handling multiple sequential prompts."""
        # Create diagram with multiple prompt nodes
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = {
            "name": "Multi-Prompt Test",
            "content": {
                "nodes": [
                    {
                        "id": "p1",
                        "type": "promptAgent",
                        "data": {"prompt": "First name:"},
                    },
                    {
                        "id": "p2",
                        "type": "promptAgent",
                        "data": {"prompt": "Last name:"},
                    },
                    {"id": "p3", "type": "promptAgent", "data": {"prompt": "Email:"}},
                    {"id": "output", "type": "outputAgent", "data": {"format": "json"}},
                ],
                "edges": [
                    {"source": "p1", "target": "output", "targetHandle": "firstName"},
                    {"source": "p2", "target": "output", "targetHandle": "lastName"},
                    {"source": "p3", "target": "output", "targetHandle": "email"},
                ],
            },
        }

        result = await gql_client.execute(
            create_mutation, variable_values={"input": diagram_data}
        )
        diagram_id = result["createDiagram"]["id"]

        # Execute and verify we can handle multiple prompts
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        result = await gql_client.execute(
            execute_mutation, variable_values={"diagramId": diagram_id}
        )

        assert "executeDiagram" in result
        execution_id = result["executeDiagram"]["executionId"]
        assert execution_id is not None

    async def test_prompt_timeout_handling(self, gql_client, graphql_mutations):
        """Test handling prompt timeouts."""
        # Create diagram with prompt that has timeout
        create_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = {
            "name": "Prompt Timeout Test",
            "content": {
                "nodes": [
                    {
                        "id": "1",
                        "type": "promptAgent",
                        "data": {
                            "prompt": "Enter value:",
                            "timeout": 1,  # 1 second timeout
                        },
                    }
                ],
                "edges": [],
            },
        }

        result = await gql_client.execute(
            create_mutation, variable_values={"input": diagram_data}
        )
        diagram_id = result["createDiagram"]["id"]

        # Execute and let it timeout
        execute_mutation = gql(graphql_mutations["execute_diagram"])
        result = await gql_client.execute(
            execute_mutation, variable_values={"diagramId": diagram_id}
        )

        execution_id = result["executeDiagram"]["executionId"]

        # Wait longer than timeout
        await asyncio.sleep(2)

        # Check execution status - should handle timeout gracefully
        status_query = gql("""
            query GetExecutionStatus($executionId: ID!) {
                executionStatus(executionId: $executionId) {
                    status
                    error
                }
            }
        """)

        status_result = await gql_client.execute(
            status_query, variable_values={"executionId": execution_id}
        )

        # Should be in a terminal state after timeout
        status = status_result["executionStatus"]["status"]
        assert status in ["FAILED", "TIMED_OUT", "COMPLETED"]
