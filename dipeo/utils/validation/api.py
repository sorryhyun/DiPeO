# API validation utilities for integrations

from typing import Dict, Any, List, Optional
import re
import json
from urllib.parse import urlparse


class APIValidator:
    # Validates API configurations and requests
    
    @staticmethod
    def validate_url(url: str) -> List[str]:
        # Validate URL format
        errors = []
        
        if not url:
            errors.append("URL is required")
            return errors
        
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme:
                errors.append("URL must include protocol (http:// or https://)")
            elif parsed.scheme not in ['http', 'https']:
                errors.append(f"Invalid protocol: {parsed.scheme}")
            
            if not parsed.netloc:
                errors.append("URL must include domain/host")
            
            # Check for common URL issues
            if ' ' in url:
                errors.append("URL contains spaces")
            
            if not re.match(r'^[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'()*+,;=]+$', url):
                errors.append("URL contains invalid characters")
            
        except Exception as e:
            errors.append(f"Invalid URL format: {str(e)}")
        
        return errors
    
    @staticmethod
    def validate_method(method: str) -> List[str]:
        # Validate HTTP method
        errors = []
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        
        if not method:
            errors.append("HTTP method is required")
        elif method.upper() not in valid_methods:
            errors.append(f"Invalid HTTP method: {method}")
        
        return errors
    
    @staticmethod
    def validate_headers(headers: Dict[str, str]) -> List[str]:
        # Validate HTTP headers
        errors = []
        
        if not isinstance(headers, dict):
            errors.append("Headers must be a dictionary")
            return errors
        
        # Check for required headers in certain cases
        content_headers = ['Content-Type', 'content-type']
        has_content_type = any(h in headers for h in content_headers)
        
        # Validate header names and values
        for name, value in headers.items():
            if not isinstance(name, str):
                errors.append(f"Header name must be string: {name}")
            elif not re.match(r'^[a-zA-Z0-9\-_]+$', name):
                errors.append(f"Invalid header name: {name}")
            
            if not isinstance(value, str):
                errors.append(f"Header value must be string: {name}")
            elif '\n' in value or '\r' in value:
                errors.append(f"Header value contains newlines: {name}")
        
        return errors
    
    @staticmethod
    def validate_body(
        body: Any,
        content_type: Optional[str] = None,
        method: Optional[str] = None
    ) -> List[str]:
        # Validate request body
        errors = []
        
        # GET requests shouldn't have body
        if method and method.upper() == 'GET' and body:
            errors.append("GET requests should not have a body")
        
        if not body:
            return errors
        
        # Validate based on content type
        if content_type:
            if 'application/json' in content_type:
                if not isinstance(body, (dict, list)):
                    errors.append("JSON body must be dict or list")
                else:
                    # Try to serialize to check validity
                    try:
                        json.dumps(body)
                    except Exception as e:
                        errors.append(f"Body is not JSON serializable: {str(e)}")
            
            elif 'application/x-www-form-urlencoded' in content_type:
                if not isinstance(body, dict):
                    errors.append("Form body must be a dictionary")
                else:
                    # Check all values are simple types
                    for key, value in body.items():
                        if not isinstance(value, (str, int, float, bool)):
                            errors.append(f"Form value must be simple type: {key}")
            
            elif 'text/' in content_type:
                if not isinstance(body, str):
                    errors.append("Text body must be a string")
        
        return errors
    
    @staticmethod
    def validate_auth(auth_config: Dict[str, Any]) -> List[str]:
        # Validate authentication configuration
        errors = []
        
        if not auth_config:
            return errors
        
        auth_type = auth_config.get('type')
        if not auth_type:
            errors.append("Auth type is required")
            return errors
        
        # Validate based on auth type
        if auth_type == 'bearer':
            if 'token' not in auth_config:
                errors.append("Bearer auth requires 'token'")
            elif not auth_config['token']:
                errors.append("Bearer token cannot be empty")
        
        elif auth_type == 'basic':
            if 'username' not in auth_config:
                errors.append("Basic auth requires 'username'")
            if 'password' not in auth_config:
                errors.append("Basic auth requires 'password'")
        
        elif auth_type == 'api_key':
            if 'key' not in auth_config:
                errors.append("API key auth requires 'key'")
            if 'location' not in auth_config:
                errors.append("API key auth requires 'location' (header/query)")
            elif auth_config['location'] not in ['header', 'query']:
                errors.append("API key location must be 'header' or 'query'")
            if auth_config['location'] == 'header' and 'header_name' not in auth_config:
                errors.append("API key header auth requires 'header_name'")
        
        elif auth_type == 'oauth2':
            required = ['client_id', 'client_secret', 'token_url']
            for field in required:
                if field not in auth_config:
                    errors.append(f"OAuth2 requires '{field}'")
        
        else:
            errors.append(f"Unknown auth type: {auth_type}")
        
        return errors
    
    @staticmethod
    def validate_api_config(config: Dict[str, Any]) -> List[str]:
        # Validate complete API configuration
        errors = []
        
        # Validate URL
        if 'url' in config:
            errors.extend(APIValidator.validate_url(config['url']))
        else:
            errors.append("URL is required")
        
        # Validate method
        if 'method' in config:
            errors.extend(APIValidator.validate_method(config['method']))
        else:
            errors.append("HTTP method is required")
        
        # Validate headers
        if 'headers' in config:
            errors.extend(APIValidator.validate_headers(config['headers']))
        
        # Validate body
        if 'body' in config:
            content_type = None
            if 'headers' in config and isinstance(config['headers'], dict):
                content_type = config['headers'].get('Content-Type') or config['headers'].get('content-type')
            errors.extend(APIValidator.validate_body(
                config['body'],
                content_type,
                config.get('method')
            ))
        
        # Validate auth
        if 'auth' in config:
            errors.extend(APIValidator.validate_auth(config['auth']))
        
        # Validate timeout
        if 'timeout' in config:
            timeout = config['timeout']
            if not isinstance(timeout, (int, float)):
                errors.append("Timeout must be a number")
            elif timeout <= 0:
                errors.append("Timeout must be positive")
            elif timeout > 300:
                errors.append("Timeout too large (max 300 seconds)")
        
        # Validate retry config
        if 'retry' in config:
            retry = config['retry']
            if not isinstance(retry, dict):
                errors.append("Retry must be a dictionary")
            else:
                if 'max_attempts' in retry:
                    if not isinstance(retry['max_attempts'], int):
                        errors.append("Retry max_attempts must be an integer")
                    elif retry['max_attempts'] < 0:
                        errors.append("Retry max_attempts must be non-negative")
                
                if 'backoff_factor' in retry:
                    if not isinstance(retry['backoff_factor'], (int, float)):
                        errors.append("Retry backoff_factor must be a number")
                    elif retry['backoff_factor'] < 0:
                        errors.append("Retry backoff_factor must be non-negative")
        
        return errors
    
    @staticmethod
    def sanitize_url(url: str, params: Optional[Dict[str, Any]] = None) -> str:
        # Sanitize and build URL with parameters
        # Remove trailing slashes
        url = url.rstrip('/')
        
        # Add query parameters if provided
        if params:
            from urllib.parse import urlencode
            query_string = urlencode(params)
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}{query_string}"
        
        return url