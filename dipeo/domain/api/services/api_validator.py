"""API validation service using unified validation framework."""

import re
import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from dipeo.core.base.exceptions import ValidationError
from dipeo.domain.shared.services import ValidationResult, ValidationWarning, BaseValidator


class APIValidator(BaseValidator):
    """Validates API configurations and requests using the unified framework."""
    
    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        """Perform API configuration validation."""
        if isinstance(target, dict):
            self._validate_api_config(target, result)
        elif isinstance(target, str):
            # If it's just a URL string
            self._validate_url(target, result)
        else:
            result.add_error(ValidationError("Target must be an API config dict or URL string"))
    
    def _validate_api_config(self, config: Dict[str, Any], result: ValidationResult) -> None:
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
            result.add_error(ValidationError(f"Invalid URL format: {str(e)}"))
    
    def _validate_method(self, method: str, result: ValidationResult) -> None:
        """Validate HTTP method."""
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        
        if not method:
            result.add_error(ValidationError("HTTP method is required"))
        elif method.upper() not in valid_methods:
            result.add_error(ValidationError(f"Invalid HTTP method: {method}"))
    
    def _validate_headers(self, headers: Dict[str, str], result: ValidationResult) -> None:
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
    
    def _validate_body(self, body: Any, content_type: Optional[str], method: Optional[str], result: ValidationResult) -> None:
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
                        result.add_error(ValidationError(f"Body is not JSON serializable: {str(e)}"))
            
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
    
    def _validate_auth(self, auth_config: Dict[str, Any], result: ValidationResult) -> None:
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
    
    def _validate_retry(self, retry: Dict[str, Any], result: ValidationResult) -> None:
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