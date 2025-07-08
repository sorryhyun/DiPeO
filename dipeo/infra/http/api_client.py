# Infrastructure implementation for HTTP/API operations.

import asyncio
import logging
from typing import Any

import aiohttp
from dipeo.core import ServiceError
from dipeo.domain.services.api.api_domain_service import APIDomainService

log = logging.getLogger(__name__)


class APIClient:
    """Infrastructure service for HTTP/API operations.
    
    This service handles all HTTP interactions.
    Business logic is delegated to APIDomainService.
    """

    def __init__(self, domain_service: APIDomainService):
        self.domain_service = domain_service
        self._session: aiohttp.ClientSession | None = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure HTTP session exists."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def execute_request(
        self,
        method: str,
        url: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        auth: aiohttp.BasicAuth | None = None
    ) -> tuple[int, dict[str, Any], dict[str, str]]:
        """Execute single HTTP request.
        
        Returns: (status_code, response_data, response_headers)
        Pure I/O operation - no business logic.
        """
        session = await self._ensure_session()
        
        try:
            async with session.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
                auth=auth
            ) as response:
                response_data = await response.json()
                response_headers = dict(response.headers)
                return response.status, response_data, response_headers
                
        except asyncio.TimeoutError:
            raise ServiceError(f"Request timed out after {timeout}s")
        except aiohttp.ClientError as e:
            raise ServiceError(f"HTTP client error: {e}")
        except Exception as e:
            raise ServiceError(f"Unexpected error during request: {e}")


class APIService:
    """Higher-level API service that combines client and domain logic."""

    def __init__(self, client: APIClient, domain_service: APIDomainService):
        self.client = client
        self.domain_service = domain_service

    async def execute_with_retry(
        self,
        url: str,
        method: str = "GET",
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
        auth: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Execute API call with retry logic."""
        # Build request config using domain service
        config = self.domain_service.build_request_config(
            method=method,
            url=url,
            data=data,
            headers=headers,
            timeout=timeout,
            auth=auth
        )
        
        # Extract auth if present
        auth_obj = None
        if "auth" in config:
            auth_obj = aiohttp.BasicAuth(config["auth"][0], config["auth"][1])
        
        for attempt in range(max_retries):
            try:
                # Execute request
                status, response_data, response_headers = await self.client.execute_request(
                    method=config["method"],
                    url=config["url"],
                    data=data,
                    headers=config.get("headers"),
                    timeout=config["timeout"],
                    auth=auth_obj
                )
                
                # Check if successful
                if 200 <= status < 300:
                    return response_data
                    
                # Check if should retry
                if self.domain_service.should_retry(status, attempt, max_retries):
                    # Calculate delay
                    rate_limit_info = self.domain_service.extract_rate_limit_info(response_headers)
                    delay = self.domain_service.calculate_retry_delay(
                        attempt=attempt,
                        base_delay=retry_delay,
                        retry_after=rate_limit_info.get("retry_after")
                    )
                    
                    log.warning(
                        f"Request failed with status {status}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(delay)
                    continue
                    
                # No retry - raise error
                raise ServiceError(
                    f"Request failed with status {status}: {response_data}"
                )
                
            except ServiceError:
                # Re-raise service errors
                raise
            except Exception as e:
                # Handle other errors
                if attempt < max_retries - 1:
                    delay = self.domain_service.calculate_retry_delay(attempt, retry_delay)
                    log.warning(
                        f"Request error: {e}, retrying in {delay}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(delay)
                    continue
                raise ServiceError(f"Request failed after {max_retries} attempts: {e}")
                
        raise ServiceError(f"Request failed after {max_retries} attempts")

    async def execute_workflow(
        self,
        workflow: dict[str, Any],
        initial_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute multi-step API workflow."""
        results = {}
        context = initial_context or {}
        
        for step in workflow.get("steps", []):
            # Validate step
            self.domain_service.validate_workflow_step(step)
            
            step_name = step["name"]
            
            try:
                # Substitute variables in step config
                url = self.domain_service.substitute_variables(step["url"], context)
                step_data = None
                if step.get("data"):
                    step_data = self.domain_service.substitute_variables(step["data"], context)
                    
                # Execute request
                result = await self.execute_with_retry(
                    url=url,
                    method=step.get("method", "GET"),
                    data=step_data,
                    headers=step.get("headers"),
                    max_retries=step.get("max_retries", 3),
                    timeout=step.get("timeout", 30.0),
                    auth=step.get("auth")
                )
                
                # Check success condition if provided
                if success_condition := step.get("success_condition"):
                    if not self.domain_service.evaluate_condition(success_condition, result):
                        raise ServiceError(
                            f"Step '{step_name}' failed success condition: {success_condition}"
                        )
                        
                # Update results and context
                results = self.domain_service.merge_workflow_results(
                    results, step_name, result
                )
                context[step_name] = result
                
            except Exception as e:
                if step.get("continue_on_error", False):
                    log.error(f"Step '{step_name}' failed but continuing: {e}")
                    results = self.domain_service.merge_workflow_results(
                        results, step_name, e, include_errors=True
                    )
                else:
                    raise ServiceError(f"Workflow failed at step '{step_name}': {e}")
                    
        return results

    async def save_response(
        self,
        response_data: dict[str, Any],
        file_path: str,
        format: str = "json",
        file_service = None  # Would be injected
    ) -> None:
        """Save API response to file."""
        if not file_service:
            raise ServiceError("File service required for saving responses")
            
        # Format response using domain service
        formatted_content = self.domain_service.format_api_response(
            response_data=response_data,
            format=format,
            include_metadata=True,
            metadata={
                "saved_at": asyncio.get_event_loop().time(),
                "format": format
            }
        )
        
        # Save using file service
        await file_service.write(file_path, formatted_content)