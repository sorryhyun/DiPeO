from typing import Any, AsyncGenerator, Dict, List, Optional

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.websockets import (
    WebsocketsTransport,
)  # For GraphQL subscriptions only


class DiPeoAPIClient:
    def __init__(self, host: str = "localhost:8000"):
        self.http_url = f"http://{host}/graphql"
        self.ws_url = f"ws://{host}/graphql"
        self._client: Optional[Client] = None
        self._subscription_client: Optional[Client] = None

    async def __aenter__(self):
        # HTTP client for queries/mutations
        transport = AIOHTTPTransport(url=self.http_url)
        self._client = Client(transport=transport, fetch_schema_from_transport=False)

        # WebSocket client for subscriptions
        ws_transport = WebsocketsTransport(url=self.ws_url)
        self._subscription_client = Client(
            transport=ws_transport, fetch_schema_from_transport=False
        )

        # No manual connection needed - gql handles this automatically
        return self

    async def __aexit__(self, *args):
        try:
            if self._client:
                await self._client.transport.close()
        except Exception:
            pass  # Ignore errors during cleanup
        
        try:
            if self._subscription_client:
                await self._subscription_client.transport.close()
        except Exception:
            pass  # Ignore errors during cleanup

    async def execute_diagram(
        self,
        diagram_id: str,
        variables: Optional[Dict[str, Any]] = None,
        debug_mode: bool = False,
        timeout: int = 300,
    ) -> str:
        """Start diagram execution and return execution ID."""
        mutation = gql("""
            mutation ExecuteDiagram($input: ExecuteDiagramInput!) {
                executeDiagram(input: $input) {
                    success
                    execution {
                        id
                        status
                        diagramId
                        startedAt
                    }
                    message
                    error
                }
            }
        """)

        result = await self._client.execute_async(
            mutation,
            variable_values={
                "input": {
                    "diagramId": diagram_id,
                    "debugMode": debug_mode,
                    "timeoutSeconds": timeout,
                    "maxIterations": 1000,
                }
            },
        )

        response = result["executeDiagram"]
        if response["success"]:
            return response["execution"]["id"]
        raise Exception(
            response.get("error") or response.get("message", "Unknown error")
        )

    async def subscribe_to_execution(
        self, execution_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to execution updates."""
        subscription = gql("""
            subscription ExecutionUpdates($executionId: String!) {
                executionUpdates(executionId: $executionId) {
                    id
                    status
                    diagramId
                    startedAt
                    endedAt
                    currentNode
                    nodeOutputs
                    variables
                    totalTokens
                    error
                    progress
                }
            }
        """)

        async for result in self._subscription_client.subscribe_async(
            subscription, variable_values={"executionId": execution_id}
        ):
            yield result["executionUpdates"]

    async def subscribe_to_node_updates(
        self, execution_id: str, node_types: Optional[List[str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to node execution updates."""
        subscription = gql("""
            subscription NodeUpdates($executionId: String!, $nodeTypes: [String!]) {
                nodeUpdates(executionId: $executionId, nodeTypes: $nodeTypes) {
                    executionId
                    nodeId
                    nodeType
                    status
                    progress
                    output
                    error
                    tokensUsed
                    timestamp
                }
            }
        """)

        variables = {"executionId": execution_id}
        if node_types:
            variables["nodeTypes"] = node_types

        async for result in self._subscription_client.subscribe_async(
            subscription, variable_values=variables
        ):
            yield result["nodeUpdates"]

    async def subscribe_to_interactive_prompts(
        self, execution_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to interactive prompt notifications."""
        subscription = gql("""
            subscription InteractivePrompts($executionId: String!) {
                interactivePrompts(executionId: $executionId) {
                    executionId
                    nodeId
                    prompt
                    timeoutSeconds
                    timestamp
                }
            }
        """)

        async for result in self._subscription_client.subscribe_async(
            subscription, variable_values={"executionId": execution_id}
        ):
            yield result["interactivePrompts"]

    async def control_execution(
        self, execution_id: str, action: str, node_id: Optional[str] = None
    ) -> bool:
        """Control a running execution (pause, resume, abort, skip_node)."""
        mutation = gql("""
            mutation ControlExecution($input: ExecutionControlInput!) {
                controlExecution(input: $input) {
                    success
                    execution {
                        id
                        status
                    }
                    message
                    error
                }
            }
        """)

        input_data = {"executionId": execution_id, "action": action}
        if node_id and action == "skip_node":
            input_data["nodeId"] = node_id

        result = await self._client.execute_async(
            mutation, variable_values={"input": input_data}
        )

        response = result["controlExecution"]
        if not response["success"]:
            raise Exception(
                response.get("error")
                or response.get("message", "Control action failed")
            )
        return response["success"]

    async def submit_interactive_response(
        self, execution_id: str, node_id: str, response: str
    ) -> bool:
        """Submit response to an interactive prompt."""
        mutation = gql("""
            mutation SubmitInteractiveResponse($input: InteractiveResponseInput!) {
                submitInteractiveResponse(input: $input) {
                    success
                    execution {
                        id
                        status
                        runningNodes
                    }
                    message
                    error
                }
            }
        """)

        result = await self._client.execute_async(
            mutation,
            variable_values={
                "input": {
                    "executionId": execution_id,
                    "nodeId": node_id,
                    "response": response,
                }
            },
        )

        response = result["submitInteractiveResponse"]
        if not response["success"]:
            raise Exception(
                response.get("error")
                or response.get("message", "Interactive response failed")
            )
        return response["success"]

    async def save_diagram(
        self, diagram_data: Dict[str, Any], filename: Optional[str] = None
    ) -> str:
        """Save a diagram and return its ID."""
        from datetime import datetime

        import yaml

        # Determine format based on content
        yaml_content = yaml.dump(diagram_data, default_flow_style=False)

        mutation = gql("""
            mutation ImportYamlDiagram($input: ImportYamlInput!) {
                importYamlDiagram(input: $input) {
                    success
                    diagram {
                        id
                        metadata {
                            name
                        }
                    }
                    message
                    error
                }
            }
        """)

        # Generate filename if not provided
        if not filename:
            diagram_name = diagram_data.get("metadata", {}).get("name", "cli_diagram")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{diagram_name}_{timestamp}.yaml"

        result = await self._client.execute_async(
            mutation,
            variable_values={"input": {"content": yaml_content, "filename": filename}},
        )

        response = result["importYamlDiagram"]
        if response["success"]:
            return response["diagram"]["id"]
        raise Exception(
            response.get("error")
            or response.get("message", "Failed to save diagram")
        )
