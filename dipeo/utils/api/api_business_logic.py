"""API business logic utilities - pure functions for API operations.

This module contains only business logic with no I/O operations.
All API responses and data are passed in as parameters.
"""

import logging
import re
from typing import Any

from dipeo.core import ServiceError, ValidationError

log = logging.getLogger(__name__)


class APIBusinessLogic:
    """Pure business logic for API operations.
    
    This utility class contains only pure functions - no HTTP calls or I/O operations.
    All API responses and data are passed in as parameters.
    """

    def validate_api_response(
        self,
        status_code: int,
        response_data: Any,
        expected_status_codes: list[int] | None = None
    ) -> None:
        """Validate API response status and structure.
        
        Raises:
            ServiceError: If response is invalid
        """
        if expected_status_codes is None:
            expected_status_codes = list(range(200, 300))  # 2xx success codes
            
        if status_code not in expected_status_codes:
            raise ServiceError(
                f"Unexpected status code: {status_code}. "
                f"Expected one of: {expected_status_codes}"
            )

    def should_retry(
        self,
        status_code: int,
        attempt: int,
        max_retries: int,
        retryable_status_codes: list[int] | None = None
    ) -> bool:
        """Determine if request should be retried based on status and attempt count.
        
        Pure business logic for retry decision.
        """
        if attempt >= max_retries - 1:
            return False
            
        if retryable_status_codes is None:
            # Default retryable status codes
            retryable_status_codes = [
                429,  # Too Many Requests
                500,  # Internal Server Error  
                502,  # Bad Gateway
                503,  # Service Unavailable
                504,  # Gateway Timeout
            ]
            
        return status_code in retryable_status_codes

    def calculate_retry_delay(
        self,
        attempt: int,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        retry_after: float | None = None
    ) -> float:
        """Calculate exponential backoff delay for retries.
        
        Pure calculation - no I/O.
        """
        if retry_after is not None:
            return min(retry_after, max_delay)
            
        # Exponential backoff: base_delay * 2^attempt
        delay = base_delay * (2 ** attempt)
        return min(delay, max_delay)

    def substitute_variables(self, data: Any, context: dict[str, Any]) -> Any:
        """Recursively substitute variables in data using context.
        
        Pure transformation - no I/O.
        """
        if isinstance(data, str):
            pattern = r"\{(\w+)\}"
            
            def replacer(match):
                var_name = match.group(1)
                return str(context.get(var_name, match.group(0)))
                
            return re.sub(pattern, replacer, data)
            
        if isinstance(data, dict):
            return {k: self.substitute_variables(v, context) for k, v in data.items()}
            
        if isinstance(data, list):
            return [self.substitute_variables(item, context) for item in data]
            
        return data

    def evaluate_condition(self, condition: str, data: dict[str, Any]) -> bool:
        """Evaluate a simple condition against data.
        
        Pure logic - no I/O.
        """
        try:
            # Simple equality check
            if "==" in condition:
                parts = condition.split("==", 1)
                if len(parts) == 2:
                    field = parts[0].strip()
                    expected = parts[1].strip().strip("'\"")
                    
                    # Handle nested field access (e.g., "response.status")
                    actual = data
                    for key in field.split("."):
                        if isinstance(actual, dict):
                            actual = actual.get(key)
                        else:
                            return False
                            
                    return str(actual) == expected
                    
            # Could add more condition types here (!=, <, >, in, etc.)
            return True
            
        except Exception as e:
            log.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False

    def validate_workflow_step(self, step: dict[str, Any]) -> None:
        """Validate workflow step configuration.
        
        Raises:
            ValidationError: If step is invalid
        """
        required_fields = ["name", "url", "method"]
        for field in required_fields:
            if field not in step:
                raise ValidationError(f"Workflow step missing required field: {field}")
                
        # Validate HTTP method
        valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
        if step["method"].upper() not in valid_methods:
            raise ValidationError(f"Invalid HTTP method: {step['method']}")

    def merge_workflow_results(
        self,
        results: dict[str, Any],
        step_name: str,
        step_result: Any,
        include_errors: bool = True
    ) -> dict[str, Any]:
        """Merge step result into workflow results.
        
        Pure data transformation.
        """
        if isinstance(step_result, Exception) and include_errors:
            results[step_name] = {"error": str(step_result), "status": "failed"}
        else:
            results[step_name] = step_result
            
        return results

    def format_api_response(
        self,
        response_data: Any,
        format: str = "json",
        include_metadata: bool = False,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """Format API response for storage.
        
        Pure transformation - returns formatted string.
        """
        import json
        
        if include_metadata and metadata:
            response_data = {
                "data": response_data,
                "metadata": metadata
            }
        
        if format == "json":
            return json.dumps(response_data, indent=2, ensure_ascii=False)
        elif format == "yaml":
            try:
                import yaml
                return yaml.dump(response_data, default_flow_style=False, allow_unicode=True)
            except ImportError:
                log.warning("PyYAML not available, falling back to JSON")
                return json.dumps(response_data, indent=2, ensure_ascii=False)
        else:
            return str(response_data)

    def extract_rate_limit_info(self, headers: dict[str, str]) -> dict[str, Any]:
        """Extract rate limit information from response headers.
        
        Pure data extraction.
        """
        rate_limit_info = {}
        
        # Common rate limit headers
        rate_limit_headers = {
            "X-RateLimit-Limit": "limit",
            "X-RateLimit-Remaining": "remaining", 
            "X-RateLimit-Reset": "reset",
            "Retry-After": "retry_after",
        }
        
        for header, key in rate_limit_headers.items():
            if header in headers:
                try:
                    value = headers[header]
                    # Try to convert to number
                    rate_limit_info[key] = float(value) if "." in value else int(value)
                except ValueError:
                    rate_limit_info[key] = value
                    
        return rate_limit_info

    def build_request_config(
        self,
        method: str,
        url: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        auth: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Build request configuration dictionary.
        
        Pure data construction.
        """
        config = {
            "method": method.upper(),
            "url": url,
            "timeout": timeout,
        }
        
        if headers:
            config["headers"] = headers
            
        if data:
            config["json"] = data
            
        if auth:
            if "bearer" in auth:
                config.setdefault("headers", {})["Authorization"] = f"Bearer {auth['bearer']}"
            elif "basic" in auth:
                config["auth"] = (auth.get("username", ""), auth.get("password", ""))
                
        return config