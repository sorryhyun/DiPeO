"""Provider manifest schema definitions."""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class AuthStrategy(str, Enum):
    """Supported authentication strategies."""
    API_KEY_HEADER = "api_key_header"
    API_KEY_QUERY = "api_key_query"
    OAUTH2_BEARER = "oauth2_bearer"
    BASIC = "basic"
    OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"
    CUSTOM = "custom"
    NONE = "none"


class RetryStrategy(str, Enum):
    """Retry strategies."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    NONE = "none"


class RateLimitAlgorithm(str, Enum):
    """Rate limiting algorithms."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"
    NONE = "none"


class PaginationType(str, Enum):
    """Pagination types."""
    NONE = "none"
    OFFSET_LIMIT = "offset_limit"
    PAGE_NUMBER = "page_number"
    CURSOR = "cursor"
    LINK_HEADER = "link_header"
    NEXT_TOKEN = "next_token"


class AuthConfig(BaseModel):
    """Authentication configuration."""
    strategy: AuthStrategy = Field(
        ...,
        description="Authentication strategy to use"
    )
    header: Optional[str] = Field(
        None,
        description="Header name for authentication (e.g., 'Authorization')"
    )
    query_param: Optional[str] = Field(
        None,
        description="Query parameter name for API key"
    )
    format: Optional[str] = Field(
        None,
        description="Format template for auth value (e.g., 'Bearer {{secret.token}}')"
    )
    token_endpoint: Optional[str] = Field(
        None,
        description="OAuth2 token endpoint for client credentials flow"
    )
    scopes: Optional[list[str]] = Field(
        default_factory=list,
        description="Required OAuth2 scopes"
    )
    custom_handler: Optional[str] = Field(
        None,
        description="Python module path for custom auth handler"
    )


class RetryPolicy(BaseModel):
    """Retry policy configuration."""
    strategy: RetryStrategy = Field(
        RetryStrategy.EXPONENTIAL_BACKOFF,
        description="Retry strategy"
    )
    max_retries: int = Field(
        3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts"
    )
    base_delay_ms: int = Field(
        300,
        ge=0,
        description="Base delay in milliseconds"
    )
    max_delay_ms: int = Field(
        30000,
        ge=0,
        description="Maximum delay in milliseconds"
    )
    retry_on_status: list[int] = Field(
        default_factory=lambda: [429, 500, 502, 503, 504],
        description="HTTP status codes to retry on"
    )


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    algorithm: RateLimitAlgorithm = Field(
        RateLimitAlgorithm.TOKEN_BUCKET,
        description="Rate limiting algorithm"
    )
    capacity: int = Field(
        50,
        ge=1,
        description="Token/request capacity"
    )
    refill_per_sec: float = Field(
        1.0,
        gt=0,
        description="Token refill rate per second"
    )
    window_size_sec: int = Field(
        60,
        ge=1,
        description="Window size in seconds (for window-based algorithms)"
    )


class RequestSchema(BaseModel):
    """Request configuration for an operation."""
    body_schema: Optional[str] = Field(
        None,
        description="JSON schema reference or inline schema for request body"
    )
    body_template: Optional[str] = Field(
        None,
        description="Jinja2 template for request body"
    )
    query_params_schema: Optional[str] = Field(
        None,
        description="JSON schema for query parameters"
    )
    query_params_template: Optional[dict[str, str]] = Field(
        None,
        description="Template for query parameters"
    )
    headers_template: Optional[dict[str, str]] = Field(
        None,
        description="Additional headers template"
    )
    path_params_template: Optional[dict[str, str]] = Field(
        None,
        description="Path parameters template"
    )


class ResponseSchema(BaseModel):
    """Response configuration for an operation."""
    success_codes: list[int] = Field(
        default_factory=lambda: [200, 201, 202, 204],
        description="HTTP status codes considered successful"
    )
    json_pointer: str = Field(
        "$",
        description="JSON pointer to extract data from response"
    )
    schema: Optional[str] = Field(
        None,
        description="JSON schema reference or inline schema for response"
    )
    error_json_pointer: Optional[str] = Field(
        None,
        description="JSON pointer for error message extraction"
    )
    transform: Optional[str] = Field(
        None,
        description="Jinja2 template to transform response"
    )


class PaginationConfig(BaseModel):
    """Pagination configuration."""
    type: PaginationType = Field(
        PaginationType.NONE,
        description="Pagination type"
    )
    limit_param: Optional[str] = Field(
        None,
        description="Parameter name for page size limit"
    )
    offset_param: Optional[str] = Field(
        None,
        description="Parameter name for offset"
    )
    page_param: Optional[str] = Field(
        None,
        description="Parameter name for page number"
    )
    cursor_param: Optional[str] = Field(
        None,
        description="Parameter name for cursor"
    )
    cursor_response_path: Optional[str] = Field(
        None,
        description="JSON path to extract next cursor from response"
    )
    has_more_path: Optional[str] = Field(
        None,
        description="JSON path to check if more pages exist"
    )
    default_limit: int = Field(
        100,
        ge=1,
        le=1000,
        description="Default page size"
    )


class OperationConfig(BaseModel):
    """Configuration for a single API operation."""
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"] = Field(
        ...,
        description="HTTP method"
    )
    path: str = Field(
        ...,
        description="URL path (can include {param} placeholders)"
    )
    description: Optional[str] = Field(
        None,
        description="Operation description"
    )
    request: Optional[RequestSchema] = Field(
        None,
        description="Request configuration"
    )
    response: Optional[ResponseSchema] = Field(
        None,
        description="Response configuration"
    )
    pagination: Optional[PaginationConfig] = Field(
        None,
        description="Pagination configuration"
    )
    rate_limit_override: Optional[RateLimitConfig] = Field(
        None,
        description="Operation-specific rate limit override"
    )
    timeout_override: Optional[float] = Field(
        None,
        ge=0.1,
        le=300,
        description="Operation-specific timeout override in seconds"
    )
    pre_request_hook: Optional[str] = Field(
        None,
        description="Python module path for pre-request processing"
    )
    post_response_hook: Optional[str] = Field(
        None,
        description="Python module path for post-response processing"
    )
    required_scopes: Optional[list[str]] = Field(
        default_factory=list,
        description="Required OAuth2 scopes for this operation"
    )


class WebhookEvent(BaseModel):
    """Webhook event configuration."""
    name: str = Field(
        ...,
        description="Event name"
    )
    description: Optional[str] = Field(
        None,
        description="Event description"
    )
    payload_schema: Optional[str] = Field(
        None,
        description="JSON schema for webhook payload"
    )
    example_payload: Optional[dict[str, Any]] = Field(
        None,
        description="Example webhook payload"
    )


class ProviderManifest(BaseModel):
    """Complete provider manifest schema."""
    name: str = Field(
        ...,
        description="Provider name (e.g., 'slack', 'notion')"
    )
    version: str = Field(
        "1.0.0",
        description="Provider version"
    )
    description: Optional[str] = Field(
        None,
        description="Provider description"
    )
    base_url: HttpUrl = Field(
        ...,
        description="Base URL for the API"
    )
    auth: AuthConfig = Field(
        ...,
        description="Authentication configuration"
    )
    retry_policy: Optional[RetryPolicy] = Field(
        None,
        description="Default retry policy"
    )
    rate_limit: Optional[RateLimitConfig] = Field(
        None,
        description="Default rate limiting configuration"
    )
    default_timeout: float = Field(
        30.0,
        ge=0.1,
        le=300,
        description="Default timeout in seconds"
    )
    default_headers: Optional[dict[str, str]] = Field(
        None,
        description="Default headers to include in all requests"
    )
    operations: dict[str, OperationConfig] = Field(
        ...,
        description="Map of operation name to configuration"
    )
    webhook_events: Optional[list[WebhookEvent]] = Field(
        None,
        description="Supported webhook events"
    )
    metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Additional provider metadata"
    )
    schemas_directory: Optional[str] = Field(
        None,
        description="Directory containing JSON schema files (relative to manifest)"
    )
    hooks_module: Optional[str] = Field(
        None,
        description="Python module containing hook implementations"
    )


def validate_manifest(manifest_dict: dict[str, Any]) -> ProviderManifest:
    """Validate and parse a provider manifest.
    
    Args:
        manifest_dict: Raw manifest dictionary
        
    Returns:
        Validated ProviderManifest
        
    Raises:
        ValidationError: If manifest is invalid
    """
    return ProviderManifest(**manifest_dict)


def create_example_manifest() -> dict[str, Any]:
    """Create an example manifest for reference."""
    return {
        "name": "example_api",
        "version": "1.0.0",
        "description": "Example API provider",
        "base_url": "https://api.example.com",
        "auth": {
            "strategy": "oauth2_bearer",
            "header": "Authorization",
            "format": "Bearer {{secret.token}}"
        },
        "retry_policy": {
            "strategy": "exponential_backoff",
            "max_retries": 3,
            "base_delay_ms": 300
        },
        "rate_limit": {
            "algorithm": "token_bucket",
            "capacity": 50,
            "refill_per_sec": 1.0
        },
        "operations": {
            "get_resource": {
                "method": "GET",
                "path": "/resources/{id}",
                "description": "Get a resource by ID",
                "request": {
                    "path_params_template": {
                        "id": "{{config.resource_id}}"
                    }
                },
                "response": {
                    "success_codes": [200],
                    "json_pointer": "$.data"
                }
            },
            "create_resource": {
                "method": "POST",
                "path": "/resources",
                "description": "Create a new resource",
                "request": {
                    "body_template": '{"name": "{{config.name}}", "type": "{{config.type}}"}'
                },
                "response": {
                    "success_codes": [201],
                    "json_pointer": "$"
                }
            }
        }
    }