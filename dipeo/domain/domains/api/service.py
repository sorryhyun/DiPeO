"""API integration domain service for high-level API operations."""

import asyncio
import logging
from typing import Any

from dipeo.core import ServiceError, SupportsFile

log = logging.getLogger(__name__)


class APIIntegrationDomainService:
    """High-level API operations with retry logic and error handling."""

    def __init__(self, file_service: SupportsFile):
        self._file = file_service

    async def execute_api_call_with_retry(
        self,
        url: str,
        method: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> dict[str, Any]:
        """Execute API call with retry logic and response validation.
        Returns response data as dictionary or raises ServiceError.
        """
        import aiohttp

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=method,
                        url=url,
                        json=data,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        if response.status >= 200 and response.status < 300:
                            return await response.json()

                        if response.status == 429:
                            retry_after = response.headers.get(
                                "Retry-After", retry_delay * (2**attempt)
                            )
                            log.warning(f"Rate limited, retrying after {retry_after}s")
                            await asyncio.sleep(float(retry_after))
                            continue

                        error_text = await response.text()
                        if attempt < max_retries - 1:
                            log.warning(
                                f"API call failed (attempt {attempt + 1}/{max_retries}): "
                                f"{response.status} - {error_text}"
                            )
                            await asyncio.sleep(retry_delay * (2**attempt))
                            continue

                        raise ServiceError(
                            f"API call failed after {max_retries} attempts: "
                            f"{response.status} - {error_text}"
                        )

            except TimeoutError:
                if attempt < max_retries - 1:
                    log.warning(
                        f"API call timed out (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(retry_delay * (2**attempt))
                    continue
                raise ServiceError(f"API call timed out after {max_retries} attempts")

            except Exception as e:
                if attempt < max_retries - 1:
                    log.warning(
                        f"API call error (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(retry_delay * (2**attempt))
                    continue
                raise ServiceError(f"API call failed: {e}")

        raise ServiceError(f"API call failed after {max_retries} attempts")

    async def execute_api_workflow(
        self,
        workflow: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a multi-step API workflow with error handling.
        Returns final workflow result.
        """
        results = {}
        current_context = context or {}

        for step in workflow.get("steps", []):
            step_name = step.get("name", "unknown")

            try:
                url = self._substitute_variables(step.get("url", ""), current_context)

                data = None
                if step.get("data"):
                    data = self._substitute_variables(step["data"], current_context)

                result = await self.execute_api_call_with_retry(
                    url=url,
                    method=step.get("method", "GET"),
                    data=data,
                    headers=step.get("headers"),
                    max_retries=step.get("max_retries", 3),
                )

                results[step_name] = result
                current_context[step_name] = result
                if success_condition := step.get("success_condition"):
                    if not self._evaluate_condition(success_condition, result):
                        raise ServiceError(
                            f"Step '{step_name}' failed success condition: {success_condition}"
                        )

            except Exception as e:
                if step.get("continue_on_error", False):
                    log.error(f"Step '{step_name}' failed but continuing: {e}")
                    results[step_name] = {"error": str(e)}
                else:
                    raise ServiceError(f"Workflow failed at step '{step_name}': {e}")

        return results

    def _substitute_variables(self, data: Any, context: dict[str, Any]) -> Any:
        """Recursively substitute variables in data using context."""
        if isinstance(data, str):
            import re

            pattern = r"\{(\w+)\}"

            def replacer(match):
                var_name = match.group(1)
                return str(context.get(var_name, match.group(0)))

            return re.sub(pattern, replacer, data)

        if isinstance(data, dict):
            return {k: self._substitute_variables(v, context) for k, v in data.items()}

        if isinstance(data, list):
            return [self._substitute_variables(item, context) for item in data]

        return data

    def _evaluate_condition(self, condition: str, data: dict[str, Any]) -> bool:
        """Evaluate a simple condition against data."""
        try:
            if "==" in condition:
                parts = condition.split("==")
                if len(parts) == 2:
                    field = parts[0].strip()
                    expected = parts[1].strip().strip("'\"")
                    actual = data.get(field)
                    return str(actual) == expected
            return True
        except Exception as e:
            log.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False

    async def save_api_response(
        self,
        response: dict[str, Any],
        file_path: str,
        format: str = "json",
    ) -> None:
        """Save API response to file with formatting.
        Supports json, yaml, and text formats.
        """
        import json

        if format == "json":
            content = json.dumps(response, indent=2)
        elif format == "yaml":
            try:
                import yaml

                content = yaml.dump(response, default_flow_style=False)
            except ImportError:
                log.warning("PyYAML not available, falling back to JSON")
                content = json.dumps(response, indent=2)
        else:
            content = str(response)

        await self._file.write(file_path, content)
