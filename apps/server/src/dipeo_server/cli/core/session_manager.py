"""CLI session management for server communication."""

import asyncio
from typing import Any

import httpx

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.graphql.inputs import (
    RegisterCliSessionInput,
    UnregisterCliSessionInput,
)
from dipeo.diagram_generated.graphql.operations import (
    RegisterCliSessionOperation,
    UnregisterCliSessionOperation,
)

logger = get_module_logger(__name__)


class SessionManager:
    """Manages CLI session registration with the server."""

    @staticmethod
    async def is_server_available() -> bool:
        """Quick check if server is available."""
        try:
            async with httpx.AsyncClient(timeout=0.5) as client:
                await client.get("http://localhost:8000/health")
                return True
        except Exception:
            return False

    @staticmethod
    async def register_cli_session(
        execution_id: str,
        diagram_name: str,
        diagram_format: str,
        diagram_data: dict[str, Any] | None = None,
    ) -> None:
        """Register a CLI session via GraphQL mutation to the running server."""
        try:
            # Check if server is available first - skip registration if not
            if not await SessionManager.is_server_available():
                logger.debug("Server not available, skipping CLI session registration")
                return

            input_data = RegisterCliSessionInput(
                execution_id=execution_id,
                diagram_name=diagram_name,
                diagram_format=diagram_format.upper(),
                diagram_data=diagram_data,
            )

            variables = RegisterCliSessionOperation.get_variables_dict(input=input_data)
            query = RegisterCliSessionOperation.get_query()

            max_retries = 5
            retry_delay = 0.5

            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.post(
                            "http://localhost:8000/graphql",
                            json={"query": query, "variables": variables},
                        )
                        result = response.json()

                        if result.get("data", {}).get("registerCliSession", {}).get("success"):
                            logger.info(f"Registered CLI session for execution {execution_id}")
                            return
                        else:
                            error = (
                                result.get("data", {}).get("registerCliSession", {}).get("error")
                            )
                            logger.warning(f"Failed to register CLI session: {error}")
                            return

                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    if attempt < max_retries - 1:
                        logger.debug(
                            f"Server not ready (attempt {attempt + 1}/{max_retries}), retrying..."
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 1.5, 2.0)
                    else:
                        logger.debug(f"Could not connect to server after {max_retries} attempts")
                        return

        except Exception as e:
            logger.debug(f"Could not register CLI session: {e}")

    @staticmethod
    async def unregister_cli_session(execution_id: str) -> None:
        """Unregister a CLI session via GraphQL mutation to the running server."""
        try:
            if not await SessionManager.is_server_available():
                return

            input_data = UnregisterCliSessionInput(execution_id=execution_id)

            variables = UnregisterCliSessionOperation.get_variables_dict(input=input_data)
            query = UnregisterCliSessionOperation.get_query()

            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.post(
                    "http://localhost:8000/graphql",
                    json={"query": query, "variables": variables},
                )
                result = response.json()

                if result.get("data", {}).get("unregisterCliSession", {}).get("success"):
                    logger.debug(f"Unregistered CLI session for execution {execution_id}")
                else:
                    error = result.get("data", {}).get("unregisterCliSession", {}).get("error")
                    logger.debug(f"Could not unregister CLI session: {error}")

        except Exception as e:
            logger.debug(f"Could not unregister CLI session: {e}")
