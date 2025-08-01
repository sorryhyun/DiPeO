"""API validation service with consolidated API key validation."""

import json
import re
import uuid
from typing import Any
from urllib.parse import urlparse

from dipeo.core.base.exceptions import ValidationError
from dipeo.core.constants import VALID_LLM_SERVICES, normalize_service_name
from dipeo.diagram_generated import APIServiceType
from dipeo.domain.validators.base_validator import BaseValidator, ValidationResult, ValidationWarning

VALID_SERVICES = VALID_LLM_SERVICES | {APIServiceType.NOTION.value}


class APIValidator(BaseValidator):
    """Validates API configurations, requests, and API keys using the unified framework."""
    
    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        """Perform API configuration validation."""
        if isinstance(target, dict):
            # Check if it's an API key validation
            if 'service' in target and 'key' in target:
                self._validate_api_key(target, result)
            else:
                self._validate_api_config(target, result)
        elif isinstance(target, str):
            # If it's just a URL string
            self._validate_url(target, result)
        else:
            result.add_error(ValidationError("Target must be an API config dict or URL string"))
    
    def _validate_api_config(self, config: dict[str, Any], result: ValidationResult) -> None:
        """Validate complete API configuration."""
        # Validate URL
        if 'url' in config:
            self._validate_url(config['url'], result)
        else:
            result.add_error(ValidationError("URL is required", details={"field": "url"}))
        
        # Validate method
        if 'method' in config:
            self._validate_method(config['method'], result)
        else:
            result.add_error(ValidationError("HTTP method is required", details={"field": "method"}))
        
        # Validate headers
        if 'headers' in config:
            self._validate_headers(config['headers'], result)
        
        # Validate body
        if 'body' in config:
            content_type = None
            if 'headers' in config and isinstance(config['headers'], dict):
                content_type = config['headers'].get('Content-Type') or config['headers'].get('content-type')
            self._validate_body(config['body'], content_type, config.get('method'), result)
        
        # Validate auth
        if 'auth' in config:
            self._validate_auth(config['auth'], result)
        
        # Validate timeout
        if 'timeout' in config:
            self._validate_timeout(config['timeout'], result)
        
        # Validate retry config
        if 'retry' in config:
            self._validate_retry(config['retry'], result)
    
    def _validate_url(self, url: str, result: ValidationResult) -> None:
        """Validate URL format."""
        if not url:
            result.add_error(ValidationError("URL is required"))
            return
        
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme:
                result.add_error(ValidationError("URL must include protocol (http:// or https://)"))
            elif parsed.scheme not in ['http', 'https']:
                result.add_error(ValidationError(f"Invalid protocol: {parsed.scheme}"))
            
            if not parsed.netloc:
                result.add_error(ValidationError("URL must include domain/host"))
            
            # Check for common URL issues
            if ' ' in url:
                result.add_error(ValidationError("URL contains spaces"))
            
            if not re.match(r'^[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'()*+,;=]+$', url):
                result.add_warning(ValidationWarning("URL contains potentially problematic characters"))
            
        except Exception as e:
            result.add_error(ValidationError(f"Invalid URL format: {e!s}"))
    
    def _validate_method(self, method: str, result: ValidationResult) -> None:
        """Validate HTTP method."""
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        
        if not method:
            result.add_error(ValidationError("HTTP method is required"))
        elif method.upper() not in valid_methods:
            result.add_error(ValidationError(f"Invalid HTTP method: {method}"))
    
    def _validate_headers(self, headers: dict[str, str], result: ValidationResult) -> None:
        """Validate HTTP headers."""
        if not isinstance(headers, dict):
            result.add_error(ValidationError("Headers must be a dictionary"))
            return
        
        # Validate header names and values
        for name, value in headers.items():
            if not isinstance(name, str):
                result.add_error(ValidationError(f"Header name must be string: {name}"))
            elif not re.match(r'^[a-zA-Z0-9\-_]+$', name):
                result.add_warning(ValidationWarning(f"Non-standard header name: {name}"))
            
            if not isinstance(value, str):
                result.add_error(ValidationError(f"Header value must be string: {name}"))
            elif '\n' in value or '\r' in value:
                result.add_error(ValidationError(f"Header value contains newlines: {name}"))
    
    def _validate_body(self, body: Any, content_type: str | None, method: str | None, result: ValidationResult) -> None:
        """Validate request body."""
        # GET requests shouldn't have body
        if method and method.upper() == 'GET' and body:
            result.add_warning(ValidationWarning("GET requests typically should not have a body"))
        
        if not body:
            return
        
        # Validate based on content type
        if content_type:
            if 'application/json' in content_type:
                if not isinstance(body, (dict, list)):
                    result.add_error(ValidationError("JSON body must be dict or list"))
                else:
                    # Try to serialize to check validity
                    try:
                        json.dumps(body)
                    except Exception as e:
                        result.add_error(ValidationError(f"Body is not JSON serializable: {e!s}"))
            
            elif 'application/x-www-form-urlencoded' in content_type:
                if not isinstance(body, dict):
                    result.add_error(ValidationError("Form body must be a dictionary"))
                else:
                    # Check all values are simple types
                    for key, value in body.items():
                        if not isinstance(value, (str, int, float, bool)):
                            result.add_error(ValidationError(f"Form value must be simple type: {key}"))
            
            elif 'text/' in content_type:
                if not isinstance(body, str):
                    result.add_error(ValidationError("Text body must be a string"))
    
    def _validate_auth(self, auth_config: dict[str, Any], result: ValidationResult) -> None:
        """Validate authentication configuration."""
        if not auth_config:
            return
        
        auth_type = auth_config.get('type')
        if not auth_type:
            result.add_error(ValidationError("Auth type is required"))
            return
        
        # Validate based on auth type
        if auth_type == 'bearer':
            if 'token' not in auth_config:
                result.add_error(ValidationError("Bearer auth requires 'token'"))
            elif not auth_config['token']:
                result.add_error(ValidationError("Bearer token cannot be empty"))
        
        elif auth_type == 'basic':
            if 'username' not in auth_config:
                result.add_error(ValidationError("Basic auth requires 'username'"))
            if 'password' not in auth_config:
                result.add_error(ValidationError("Basic auth requires 'password'"))
        
        elif auth_type == 'api_key':
            if 'key' not in auth_config:
                result.add_error(ValidationError("API key auth requires 'key'"))
            if 'location' not in auth_config:
                result.add_error(ValidationError("API key auth requires 'location' (header/query)"))
            elif auth_config['location'] not in ['header', 'query']:
                result.add_error(ValidationError("API key location must be 'header' or 'query'"))
            if auth_config['location'] == 'header' and 'header_name' not in auth_config:
                result.add_error(ValidationError("API key header auth requires 'header_name'"))
        
        elif auth_type == 'oauth2':
            required = ['client_id', 'client_secret', 'token_url']
            for field in required:
                if field not in auth_config:
                    result.add_error(ValidationError(f"OAuth2 requires '{field}'"))
        
        else:
            result.add_error(ValidationError(f"Unknown auth type: {auth_type}"))
    
    def _validate_timeout(self, timeout: Any, result: ValidationResult) -> None:
        """Validate timeout configuration."""
        if not isinstance(timeout, (int, float)):
            result.add_error(ValidationError("Timeout must be a number"))
        elif timeout <= 0:
            result.add_error(ValidationError("Timeout must be positive"))
        elif timeout > 300:
            result.add_warning(ValidationWarning("Timeout is very high (>300 seconds)"))
    
    def _validate_retry(self, retry: dict[str, Any], result: ValidationResult) -> None:
        """Validate retry configuration."""
        if not isinstance(retry, dict):
            result.add_error(ValidationError("Retry must be a dictionary"))
            return
        
        if 'max_attempts' in retry:
            if not isinstance(retry['max_attempts'], int):
                result.add_error(ValidationError("Retry max_attempts must be an integer"))
            elif retry['max_attempts'] < 0:
                result.add_error(ValidationError("Retry max_attempts must be non-negative"))
            elif retry['max_attempts'] > 10:
                result.add_warning(ValidationWarning("High retry count may cause long delays"))
        
        if 'backoff_factor' in retry:
            if not isinstance(retry['backoff_factor'], (int, float)):
                result.add_error(ValidationError("Retry backoff_factor must be a number"))
            elif retry['backoff_factor'] < 0:
                result.add_error(ValidationError("Retry backoff_factor must be non-negative"))
    
    # API Key validation methods (consolidated from apikey_validators)
    def _validate_api_key(self, key_info: dict[str, Any], result: ValidationResult) -> None:
        """Validate API key configuration."""
        service = key_info.get('service')
        key = key_info.get('key')
        
        if not service:
            result.add_error(ValidationError("Service name is required"))
            return
        
        if not key:
            result.add_error(ValidationError("API key is required"))
            return
        
        # Validate service name
        try:
            normalized_service = self.validate_service_name(service)
            key_info['service'] = normalized_service
        except ValidationError as e:
            result.add_error(e)
            return
        
        # Validate key format
        try:
            self.validate_api_key_format(key, normalized_service)
        except ValidationError as e:
            result.add_error(e)
    
    @staticmethod
    def validate_service_name(service: str) -> str:
        """Validate and normalize service name."""
        normalized = normalize_service_name(service)
        
        if normalized not in VALID_SERVICES:
            raise ValidationError(
                f"Invalid service '{service}'. Must be one of: {', '.join(VALID_SERVICES)}"
            )
        
        return normalized
    
    @staticmethod
    def validate_api_key_format(key: str, service: str) -> None:
        """Validate API key format based on service requirements."""
        if not key or not key.strip():
            raise ValidationError("API key cannot be empty")
        
        if service == APIServiceType.OPENAI.value and not key.startswith("sk-"):
            raise ValidationError("OpenAI API keys must start with 'sk-'")
        if service == APIServiceType.ANTHROPIC.value and not key.startswith("sk-ant-"):
            raise ValidationError("Anthropic API keys must start with 'sk-ant-'")
    
    @staticmethod
    def generate_api_key_id() -> str:
        """Generate a unique API key identifier."""
        return f"APIKEY_{uuid.uuid4().hex[:6].upper()}"
    
    @staticmethod
    def format_api_key_info(key_id: str, info: dict) -> dict:
        """Format API key information for storage."""
        if isinstance(info, dict):
            return {
                "id": key_id,
                "label": info.get("label", key_id),
                "service": info.get("service", "unknown"),
                "key": info.get("key", ""),
            }
        return info
    
    @staticmethod
    def extract_api_key_summary(key_id: str, info: dict) -> dict | None:
        """Extract summary information from API key data."""
        if isinstance(info, dict) and "service" in info:
            return {
                "id": key_id,
                "label": info.get("label", key_id),
                "service": info["service"],
            }
        return None