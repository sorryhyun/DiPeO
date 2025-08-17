"""API business logic - pure functions for API operations."""

import json
import logging
from typing import Any, Optional

from dipeo.domain.base.exceptions import ServiceError, ValidationError
from dipeo.domain.api.value_objects import RetryPolicy, RetryStrategy
from dipeo.domain.ports.template import TemplateProcessorPort
from dipeo.diagram_generated.enums import HttpMethod

log = logging.getLogger(__name__)


class APIBusinessLogic:
    
    def __init__(self, template_processor: Optional[TemplateProcessorPort] = None):
        self._template_processor = template_processor

    def validate_api_response(
        self,
        status_code: int,
        response_data: Any,
        expected_status_codes: list[int] | None = None
    ) -> None:
        if expected_status_codes is None:
            expected_status_codes = list(range(200, 300))
            
        if status_code not in expected_status_codes:
            raise ServiceError(
                f"Unexpected status code: {status_code}. "
                f"Expected one of: {expected_status_codes}"
            )

    def should_retry_with_policy(
        self,
        status_code: int,
        attempt: int,
        retry_policy: RetryPolicy,
        retryable_status_codes: list[int] | None = None
    ) -> bool:
        if retryable_status_codes is None:
            retryable_status_codes = [429, 500, 502, 503, 504]
        
        is_retryable_error = status_code in retryable_status_codes
        return retry_policy.should_retry(attempt, is_retryable_error)

    def calculate_retry_delay_with_policy(
        self,
        attempt: int,
        retry_policy: RetryPolicy,
        retry_after: float | None = None
    ) -> float:
        if retry_after is not None:
            # Use server-provided retry-after if available
            return min(retry_after * 1000, retry_policy.max_delay_ms) / 1000
        
        delay_ms = retry_policy.calculate_delay(attempt)
        return delay_ms / 1000  # Convert to seconds

    def should_retry(
        self,
        status_code: int,
        attempt: int,
        max_retries: int,
        retryable_status_codes: list[int] | None = None
    ) -> bool:
        """Legacy method for backward compatibility."""
        if attempt >= max_retries - 1:
            return False
            
        if retryable_status_codes is None:
            retryable_status_codes = [429, 500, 502, 503, 504]
            
        return status_code in retryable_status_codes

    def calculate_retry_delay(
        self,
        attempt: int,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        retry_after: float | None = None
    ) -> float:
        """Legacy method for backward compatibility."""
        if retry_after is not None:
            return min(retry_after, max_delay)
            
        delay = base_delay * (2 ** attempt)
        return min(delay, max_delay)

    def substitute_variables(self, data: Any, context: dict[str, Any]) -> Any:
        if isinstance(data, str):
            # Use TemplateProcessor for single brace variable substitution if available
            if self._template_processor:
                return self._template_processor.process_single_brace(data, context)
            return data  # Return unchanged if no processor available
            
        if isinstance(data, dict):
            return {k: self.substitute_variables(v, context) for k, v in data.items()}
            
        if isinstance(data, list):
            return [self.substitute_variables(item, context) for item in data]
            
        return data

    def evaluate_condition(self, condition: str, data: dict[str, Any]) -> bool:
        """Only supports '==' comparisons with dot notation for field access."""
        try:
            if "==" in condition:
                parts = condition.split("==", 1)
                if len(parts) == 2:
                    field = parts[0].strip()
                    expected = parts[1].strip().strip("'\"")
                    
                    actual = data
                    for key in field.split("."):
                        if isinstance(actual, dict):
                            actual = actual.get(key)
                        else:
                            return False
                            
                    return str(actual) == expected
                    
            return True
            
        except Exception as e:
            log.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False

    def validate_workflow_step(self, step: dict[str, Any]) -> None:
        required_fields = ["name", "url", "method"]
        for field in required_fields:
            if field not in step:
                raise ValidationError(f"Workflow step missing required field: {field}")

        try:
            HttpMethod(step["method"].upper())
        except ValueError:
            raise ValidationError(f"Invalid HTTP method: {step['method']}")

    def merge_workflow_results(
        self,
        results: dict[str, Any],
        step_name: str,
        step_result: Any,
        include_errors: bool = True
    ) -> dict[str, Any]:
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
        rate_limit_info = {}
        
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
        http_method = HttpMethod(method.upper())
        
        config = {
            "method": http_method.value,
            "url": str(url),
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

    def create_default_retry_policy(
        self,
        max_attempts: int = 3,
        initial_delay_ms: int = 1000,
        max_delay_ms: int = 60000
    ) -> RetryPolicy:
        return RetryPolicy(
            max_attempts=max_attempts,
            initial_delay_ms=initial_delay_ms,
            max_delay_ms=max_delay_ms,
            strategy=RetryStrategy.EXPONENTIAL,
            backoff_factor=2.0,
            jitter=True
        )