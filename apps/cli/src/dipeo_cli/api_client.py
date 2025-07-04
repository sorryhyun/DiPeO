import asyncio
from collections.abc import AsyncGenerator, Callable
from typing import Any, TypeVar

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportQueryError, TransportServerError
from gql.transport.websockets import (
    WebsocketsTransport,
)  # For GraphQL subscriptions only

from dipeo_cli.__generated__.graphql_operations import (
    CONTROL_EXECUTION_MUTATION,
    CONVERT_DIAGRAM_MUTATION,
    EXECUTE_DIAGRAM_MUTATION,
    EXECUTION_UPDATES_SUBSCRIPTION,
    INTERACTIVE_PROMPTS_SUBSCRIPTION,
    NODE_UPDATES_SUBSCRIPTION,
    SUBMIT_INTERACTIVE_RESPONSE_MUTATION,
)

T = TypeVar("T")


class DiPeoAPIClient:
    """GraphQL API client for DiPeO server communication."""

    def __init__(
        self,
        host: str = "localhost:8000",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.host = host
        self.http_url = f"http://{host}/graphql"
        self.ws_url = f"ws://{host}/graphql"
        self._client: Client | None = None
        self._subscription_clients: dict[str, Client | None] = {
            "execution": None,
            "nodes": None,
            "prompts": None,
        }
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def __aenter__(self):
        transport = AIOHTTPTransport(url=self.http_url)
        self._client = Client(transport=transport, fetch_schema_from_transport=False)
        return self

    async def __aexit__(self, *args):
        try:
            if self._client:
                await self._client.transport.close()
        except Exception:
            pass
        for client in self._subscription_clients.values():
            if client:
                try:
                    await client.transport.close()
                except Exception:
                    pass

    def _get_subscription_client(self, subscription_type: str) -> Client:
        """Get or create a subscription client for the given type."""
        if not self._subscription_clients.get(subscription_type):
            ws_transport = WebsocketsTransport(url=self.ws_url)
            self._subscription_clients[subscription_type] = Client(
                transport=ws_transport,
                fetch_schema_from_transport=False,
                execute_timeout=None,
            )
        return self._subscription_clients[subscription_type]

    async def _retry_with_backoff(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry logic and exponential backoff."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except (
                TransportQueryError,
                TransportServerError,
                ConnectionError,
                OSError,
            ) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    print(
                        f"⚠️  Connection failed (attempt {attempt + 1}/{self.max_retries}): {e!s}"
                    )
                    print(f"   Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    print(f"❌ Connection failed after {self.max_retries} attempts")
        raise ConnectionError(
            f"Failed to connect to server at {self.host} after {self.max_retries} attempts: {last_error}"
        )

    async def _execute_query(self, query: str, variables: dict | None = None) -> dict:
        """Execute a GraphQL query and return the result."""

        async def _do_execute():
            parsed_query = gql(query)
            return await self._client.execute_async(
                parsed_query, variable_values=variables or {}
            )

        return await self._retry_with_backoff(_do_execute)

    async def execute_diagram(
        self,
        diagram_id: str | None = None,
        diagram_data: dict[str, Any] | None = None,
        variables: dict[str, Any] | None = None,
        debug_mode: bool = False,
        timeout: int = 300,
    ) -> str:
        """Start diagram execution and return execution ID."""
        mutation = gql(EXECUTE_DIAGRAM_MUTATION)

        input_data = {
            "debug_mode": debug_mode,
            "timeout_seconds": timeout,
            "max_iterations": 1000,
        }

        if diagram_data:
            input_data["diagram_data"] = diagram_data
            if variables:
                input_data["variables"] = variables
        elif diagram_id:
            input_data["diagram_id"] = diagram_id
        else:
            raise ValueError("Either diagram_id or diagram_data must be provided")

        result = await self._retry_with_backoff(
            self._client.execute_async,
            mutation,
            variable_values={"data": input_data},
        )

        response = result["execute_diagram"]
        if response["success"]:
            return response["execution"]["id"]
        raise Exception(
            response.get("error") or response.get("message", "Unknown error")
        )

    async def convert_diagram(
        self,
        diagram_data: dict[str, Any],
        format: str = "native",
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """Convert diagram to specified format using backend API."""
        mutation = gql(CONVERT_DIAGRAM_MUTATION)

        result = await self._retry_with_backoff(
            self._client.execute_async,
            mutation,
            variable_values={
                "content": diagram_data,
                "format": format.upper(),
                "includeMetadata": include_metadata,
            },
        )

        response = result.get("convertDiagram")
        if not response:
            raise Exception(
                f"No response from convertDiagram mutation. Result: {result}"
            )
        if response["success"]:
            return response
        raise Exception(response.get("error") or "Conversion failed")

    async def subscribe_to_execution(
        self, execution_id: str
    ) -> AsyncGenerator[dict[str, Any]]:
        """Subscribe to execution updates."""
        subscription = gql(EXECUTION_UPDATES_SUBSCRIPTION)

        client = self._get_subscription_client("execution")
        async for result in client.subscribe_async(
            subscription, variable_values={"execution_id": execution_id}
        ):
            yield result["execution_updates"]

    async def subscribe_to_node_updates(
        self, execution_id: str, node_types: list[str] | None = None
    ) -> AsyncGenerator[dict[str, Any]]:
        """Subscribe to node execution updates."""
        subscription = gql(NODE_UPDATES_SUBSCRIPTION)

        variables = {"execution_id": execution_id}
        if node_types:
            variables["node_types"] = node_types

        client = self._get_subscription_client("nodes")
        async for result in client.subscribe_async(
            subscription, variable_values=variables
        ):
            yield result["node_updates"]

    async def subscribe_to_interactive_prompts(
        self, execution_id: str
    ) -> AsyncGenerator[dict[str, Any]]:
        """Subscribe to interactive prompt notifications."""
        subscription = gql(INTERACTIVE_PROMPTS_SUBSCRIPTION)

        client = self._get_subscription_client("prompts")
        async for result in client.subscribe_async(
            subscription, variable_values={"execution_id": execution_id}
        ):
            yield result["interactive_prompts"]

    async def control_execution(
        self, execution_id: str, action: str, node_id: str | None = None
    ) -> bool:
        """Control a running execution (pause, resume, abort, skip_node)."""
        mutation = gql(CONTROL_EXECUTION_MUTATION)

        input_data = {"execution_id": execution_id, "action": action}
        if node_id and action == "skip_node":
            input_data["node_id"] = node_id

        result = await self._retry_with_backoff(
            self._client.execute_async, mutation, variable_values={"data": input_data}
        )

        response = result["control_execution"]
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
        mutation = gql(SUBMIT_INTERACTIVE_RESPONSE_MUTATION)

        result = await self._retry_with_backoff(
            self._client.execute_async,
            mutation,
            variable_values={
                "data": {
                    "execution_id": execution_id,
                    "node_id": node_id,
                    "response": response,
                }
            },
        )

        response = result["submit_interactive_response"]
        if not response["success"]:
            raise Exception(
                response.get("error")
                or response.get("message", "Interactive response failed")
            )
        return response["success"]
