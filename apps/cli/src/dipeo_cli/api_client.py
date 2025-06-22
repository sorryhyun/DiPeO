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
        # Store multiple subscription clients to avoid concurrent connection issues
        self._subscription_clients: Dict[str, Optional[Client]] = {
            "execution": None,
            "nodes": None,
            "prompts": None
        }

    async def __aenter__(self):
        # HTTP client for queries/mutations
        transport = AIOHTTPTransport(url=self.http_url)
        self._client = Client(transport=transport, fetch_schema_from_transport=False)

        # No need to create WebSocket clients here - they'll be created on demand
        return self

    async def __aexit__(self, *args):
        try:
            if self._client:
                await self._client.transport.close()
        except Exception:
            pass  # Ignore errors during cleanup
        
        # Close all subscription clients
        for client in self._subscription_clients.values():
            if client:
                try:
                    await client.transport.close()
                except Exception:
                    pass  # Ignore errors during cleanup

    def _get_subscription_client(self, subscription_type: str) -> Client:
        """Get or create a subscription client for the given type."""
        if not self._subscription_clients.get(subscription_type):
            ws_transport = WebsocketsTransport(url=self.ws_url)
            self._subscription_clients[subscription_type] = Client(
                transport=ws_transport,
                fetch_schema_from_transport=False,
                execute_timeout=None  # Disable timeout for subscriptions
            )
        return self._subscription_clients[subscription_type]

    async def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute a GraphQL query and return the result."""
        parsed_query = gql(query)
        result = await self._client.execute_async(parsed_query, variable_values=variables or {})
        return result

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

        # Check if this is a temporary diagram (created by save_diagram)
        input_data = {
            "debugMode": debug_mode,
            "timeoutSeconds": timeout,
            "maxIterations": 1000,
        }
        
        if diagram_id.startswith("temp_") and hasattr(self, '_temp_diagram_data'):
            # Use diagram data directly
            input_data["diagramData"] = self._temp_diagram_data
            if variables:
                input_data["variables"] = variables
        else:
            # Use existing diagram ID
            input_data["diagramId"] = diagram_id
            
        result = await self._client.execute_async(
            mutation,
            variable_values={"input": input_data},
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
            subscription ExecutionUpdates($executionId: ExecutionID!) {
                executionUpdates(executionId: $executionId) {
                    id
                    status
                    diagramId
                    startedAt
                    endedAt
                    nodeStates
                    nodeOutputs
                    variables
                    tokenUsage {
                        input
                        output
                        total
                    }
                    error
                    isActive
                    durationSeconds
                }
            }
        """)

        client = self._get_subscription_client("execution")
        async for result in client.subscribe_async(
            subscription, variable_values={"executionId": execution_id}
        ):
            yield result["executionUpdates"]

    async def subscribe_to_node_updates(
        self, execution_id: str, node_types: Optional[List[str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to node execution updates."""
        subscription = gql("""
            subscription NodeUpdates($executionId: ExecutionID!, $nodeTypes: [NodeType!]) {
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

        client = self._get_subscription_client("nodes")
        async for result in client.subscribe_async(
            subscription, variable_values=variables
        ):
            yield result["nodeUpdates"]

    async def subscribe_to_interactive_prompts(
        self, execution_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to interactive prompt notifications."""
        subscription = gql("""
            subscription InteractivePrompts($executionId: ExecutionID!) {
                interactivePrompts(executionId: $executionId) {
                    executionId
                    nodeId
                    prompt
                    timeoutSeconds
                    timestamp
                }
            }
        """)

        client = self._get_subscription_client("prompts")
        async for result in client.subscribe_async(
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
        """Save a diagram and return its ID.
        
        Note: Since there's no direct mutation to save a diagram with content,
        we'll create an empty diagram and then execute directly with diagram_data.
        For now, we'll return a temporary ID since execution can work with diagram_data directly.
        """
        from datetime import datetime
        
        # For CLI usage, we can execute diagrams directly without saving
        # Return a temporary ID that indicates this is an unsaved diagram
        diagram_name = diagram_data.get("metadata", {}).get("name", "cli_diagram")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_id = f"temp_{diagram_name}_{timestamp}"
        
        # Store the diagram data temporarily (in practice, the execute_diagram
        # mutation will receive the diagram_data directly)
        self._temp_diagram_data = diagram_data
        
        return temp_id
