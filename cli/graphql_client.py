import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.websockets import WebsocketsTransport
from gql.transport.exceptions import TransportQueryError

class DiPeoGraphQLClient:
    def __init__(self, host: str = "localhost:8100"):
        self.http_url = f"http://{host}/graphql"
        self.ws_url = f"ws://{host}/graphql"
        self._client: Optional[Client] = None
        self._subscription_client: Optional[Client] = None
    
    async def __aenter__(self):
        # HTTP client for queries/mutations
        transport = AIOHTTPTransport(url=self.http_url)
        self._client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # WebSocket client for subscriptions
        ws_transport = WebsocketsTransport(url=self.ws_url)
        self._subscription_client = Client(transport=ws_transport, fetch_schema_from_transport=True)
        
        await self._client.transport.connect()
        await self._subscription_client.transport.connect()
        return self
    
    async def __aexit__(self, *args):
        if self._client:
            await self._client.transport.close()
        if self._subscription_client:
            await self._subscription_client.transport.close()
    
    async def execute_diagram(self, diagram_id: str, variables: Optional[Dict[str, Any]] = None, 
                            debug_mode: bool = False, timeout: int = 300) -> str:
        """Start diagram execution and return execution ID."""
        mutation = gql("""
            mutation ExecuteDiagram($input: ExecuteDiagramInput!) {
                executeDiagram(input: $input) {
                    success
                    executionId
                    message
                    error
                }
            }
        """)
        
        result = await self._client.execute_async(
            mutation,
            variable_values={
                "input": {
                    "diagram_id": diagram_id,
                    "variables": variables or {},
                    "debug_mode": debug_mode,
                    "timeout_seconds": timeout
                }
            }
        )
        
        response = result["executeDiagram"]
        if response["success"]:
            return response["executionId"]
        else:
            raise Exception(response.get("error") or response.get("message", "Unknown error"))
    
    async def subscribe_to_execution(self, execution_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to execution updates."""
        subscription = gql("""
            subscription ExecutionUpdates($executionId: ExecutionID!) {
                executionUpdates(executionId: $executionId) {
                    id
                    status
                    runningNodes
                    completedNodes
                    failedNodes
                    nodeOutputs
                    tokenUsage {
                        total
                    }
                    error
                }
            }
        """)
        
        async for result in self._subscription_client.subscribe_async(
            subscription,
            variable_values={"executionId": execution_id}
        ):
            yield result["executionUpdates"]
    
    async def subscribe_to_node_updates(self, execution_id: str, node_types: Optional[List[str]] = None) -> AsyncGenerator[Dict[str, Any], None]:
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
            
        async for result in self._subscription_client.subscribe_async(
            subscription,
            variable_values=variables
        ):
            yield result["nodeUpdates"]
    
    async def subscribe_to_interactive_prompts(self, execution_id: str) -> AsyncGenerator[Dict[str, Any], None]:
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
        
        async for result in self._subscription_client.subscribe_async(
            subscription,
            variable_values={"executionId": execution_id}
        ):
            yield result["interactivePrompts"]
    
    async def control_execution(self, execution_id: str, action: str, node_id: Optional[str] = None) -> bool:
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
        
        input_data = {
            "execution_id": execution_id,
            "action": action
        }
        if node_id and action == "skip_node":
            input_data["node_id"] = node_id
            
        result = await self._client.execute_async(
            mutation,
            variable_values={"input": input_data}
        )
        
        response = result["controlExecution"]
        if not response["success"]:
            raise Exception(response.get("error") or response.get("message", "Control action failed"))
        return response["success"]
    
    async def submit_interactive_response(self, execution_id: str, node_id: str, response: str) -> bool:
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
                    "execution_id": execution_id,
                    "node_id": node_id,
                    "response": response
                }
            }
        )
        
        response = result["submitInteractiveResponse"]
        if not response["success"]:
            raise Exception(response.get("error") or response.get("message", "Interactive response failed"))
        return response["success"]