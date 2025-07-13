"""Infrastructure service for API operations."""

import asyncio
import logging
from typing import Any

import aiohttp
from dipeo.core import ServiceError
from dipeo.core.ports import FileServicePort
from dipeo.domain.api.services import APIBusinessLogic

log = logging.getLogger(__name__)


class APIService:

    def __init__(
        self, 
        business_logic: APIBusinessLogic,
        file_service: FileServicePort | None = None
    ):
        self.business_logic = business_logic
        self.file_service = file_service
        self._session: aiohttp.ClientSession | None = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close HTTP session and cleanup resources."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def execute_request(
        self,
        method: str,
        url: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        auth: dict[str, str] | None = None
    ) -> tuple[int, dict[str, Any], dict[str, str]]:
        """Execute single HTTP request.
        
        This is the core I/O operation that performs the actual HTTP call.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            data: Request body data
            headers: Request headers
            timeout: Request timeout in seconds
            auth: Authentication credentials
            
        Returns:
            Tuple of (status_code, response_data, response_headers)
            
        Raises:
            ServiceError: On request failures
        """
        session = await self._ensure_session()
        
        # Build request configuration using domain service
        config = self.business_logic.build_request_config(
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
        
        try:
            async with session.request(
                method=config["method"],
                url=config["url"],
                json=config.get("json"),
                headers=config.get("headers"),
                timeout=aiohttp.ClientTimeout(total=config["timeout"]),
                auth=auth_obj
            ) as response:
                # Read response
                try:
                    response_data = await response.json()
                except Exception:
                    # If JSON parsing fails, return text
                    response_data = {"text": await response.text()}
                    
                response_headers = dict(response.headers)
                return response.status, response_data, response_headers
                
        except asyncio.TimeoutError:
            raise ServiceError(f"Request timed out after {timeout}s")
        except aiohttp.ClientError as e:
            raise ServiceError(f"HTTP client error: {e}")
        except Exception as e:
            raise ServiceError(f"Unexpected error during request: {e}")

    async def execute_with_retry(
        self,
        url: str,
        method: str = "GET",
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
        auth: dict[str, str] | None = None,
        expected_status_codes: list[int] | None = None
    ) -> dict[str, Any]:
        """Execute API call with retry logic.
        
        Uses domain service to determine retry strategy and delays.
        
        Args:
            url: Target URL
            method: HTTP method
            data: Request body
            headers: Request headers
            max_retries: Maximum retry attempts
            retry_delay: Base delay between retries
            timeout: Request timeout
            auth: Authentication credentials
            expected_status_codes: List of acceptable status codes
            
        Returns:
            Response data dictionary
            
        Raises:
            ServiceError: After all retries exhausted
        """
        for attempt in range(max_retries):
            try:
                # Execute request
                status, response_data, response_headers = await self.execute_request(
                    method=method,
                    url=url,
                    data=data,
                    headers=headers,
                    timeout=timeout,
                    auth=auth
                )
                
                # Validate response using domain service
                try:
                    self.business_logic.validate_api_response(
                        status_code=status,
                        response_data=response_data,
                        expected_status_codes=expected_status_codes
                    )
                    return response_data
                except ServiceError:
                    # Response validation failed, check if should retry
                    if not self.business_logic.should_retry(status, attempt, max_retries):
                        raise
                    
                # Calculate retry delay
                rate_limit_info = self.business_logic.extract_rate_limit_info(response_headers)
                delay = self.business_logic.calculate_retry_delay(
                    attempt=attempt,
                    base_delay=retry_delay,
                    retry_after=rate_limit_info.get("retry_after")
                )
                
                log.warning(
                    f"Request failed with status {status}, "
                    f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)
                
            except ServiceError:
                # Re-raise service errors
                raise
            except Exception as e:
                # Handle other errors
                if attempt < max_retries - 1:
                    delay = self.business_logic.calculate_retry_delay(attempt, retry_delay)
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
        """Execute multi-step API workflow.
        
        Executes a series of API calls with variable substitution and
        conditional logic between steps.
        
        Args:
            workflow: Workflow definition with steps
            initial_context: Initial variable context
            
        Returns:
            Dictionary of step results
            
        Raises:
            ServiceError: On workflow failures
        """
        results = {}
        context = initial_context or {}
        
        for step in workflow.get("steps", []):
            # Validate step using domain service
            self.business_logic.validate_workflow_step(step)
            
            step_name = step["name"]
            
            try:
                # Substitute variables in step config
                url = self.business_logic.substitute_variables(step["url"], context)
                step_data = None
                if step.get("data"):
                    step_data = self.business_logic.substitute_variables(step["data"], context)
                    
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
                    if not self.business_logic.evaluate_condition(success_condition, result):
                        raise ServiceError(
                            f"Step '{step_name}' failed success condition: {success_condition}"
                        )
                        
                # Update results and context
                results = self.business_logic.merge_workflow_results(
                    results, step_name, result
                )
                context[step_name] = result
                
            except Exception as e:
                if step.get("continue_on_error", False):
                    log.error(f"Step '{step_name}' failed but continuing: {e}")
                    results = self.business_logic.merge_workflow_results(
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
        include_metadata: bool = True
    ) -> None:
        """Save API response to file.
        
        Uses the injected file service to persist responses.
        
        Args:
            response_data: Response data to save
            file_path: Target file path
            format: Output format (json, yaml, etc.)
            include_metadata: Whether to include metadata
            
        Raises:
            ServiceError: If file service not available
        """
        if not self.file_service:
            raise ServiceError("File service required for saving responses")
            
        # Format response using domain service
        formatted_content = self.business_logic.format_api_response(
            response_data=response_data,
            format=format,
            include_metadata=include_metadata,
            metadata={
                "saved_at": asyncio.get_event_loop().time(),
                "format": format
            } if include_metadata else None
        )
        
        # Save using file service
        await self.file_service.write(file_path, formatted_content)

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()