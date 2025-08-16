"""GraphQL types for API provider integration."""

from typing import List, Optional, Any
import strawberry
from strawberry.scalars import JSON as JSONScalar


@strawberry.type
class AuthConfigType:
    """Authentication configuration for a provider."""
    strategy: str
    header: Optional[str] = None
    query_param: Optional[str] = None
    format: Optional[str] = None
    scopes: Optional[List[str]] = None


@strawberry.type
class RateLimitConfigType:
    """Rate limit configuration."""
    algorithm: str
    capacity: int
    refill_per_sec: float
    window_size_sec: Optional[int] = None


@strawberry.type
class RetryPolicyType:
    """Retry policy configuration."""
    strategy: str
    max_retries: int
    base_delay_ms: int
    max_delay_ms: Optional[int] = None
    retry_on_status: List[int]


@strawberry.type
class OperationSchemaType:
    """Schema information for an operation."""
    operation: str
    method: str
    path: str
    description: Optional[str] = None
    request_body: Optional[JSONScalar] = None
    query_params: Optional[JSONScalar] = None
    response: Optional[JSONScalar] = None


@strawberry.type
class OperationType:
    """API operation definition."""
    name: str
    method: str
    path: str
    description: Optional[str] = None
    required_scopes: Optional[List[str]] = None
    has_pagination: bool = False
    timeout_override: Optional[float] = None


@strawberry.type
class ProviderMetadataType:
    """Provider metadata."""
    version: str
    type: str  # 'manifest' or 'programmatic'
    manifest_path: Optional[str] = None
    description: Optional[str] = None
    documentation_url: Optional[str] = None
    support_email: Optional[str] = None


@strawberry.type
class ProviderType:
    """API provider information."""
    name: str
    operations: List[OperationType]
    metadata: ProviderMetadataType
    base_url: Optional[str] = None
    auth_config: Optional[AuthConfigType] = None
    rate_limit: Optional[RateLimitConfigType] = None
    retry_policy: Optional[RetryPolicyType] = None
    default_timeout: float = 30.0


@strawberry.type
class ProviderStatisticsType:
    """Provider registry statistics."""
    total_providers: int
    total_operations: int
    provider_types: JSONScalar  # Dict[str, int]
    providers: List[JSONScalar]  # List of provider summary


@strawberry.type
class IntegrationTestResultType:
    """Result of an integration test."""
    success: bool
    provider: str
    operation: str
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    response_preview: Optional[JSONScalar] = None


@strawberry.input
class ExecuteIntegrationInput:
    """Input for executing an integration operation."""
    provider: str
    operation: str
    config: JSONScalar
    api_key_id: Optional[strawberry.ID] = None
    timeout: Optional[int] = None
    resource_id: Optional[str] = None


@strawberry.input
class TestIntegrationInput:
    """Input for testing an integration."""
    provider: str
    operation: str
    config_preview: JSONScalar
    api_key_id: Optional[strawberry.ID] = None
    dry_run: bool = True