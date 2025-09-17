"""GraphQL types for API provider integration."""

import strawberry
from strawberry.scalars import JSON


@strawberry.type
class AuthConfigType:
    """Authentication configuration for a provider."""

    strategy: str
    header: str | None = None
    query_param: str | None = None
    format: str | None = None
    scopes: list[str] | None = None


@strawberry.type
class RateLimitConfigType:
    """Rate limit configuration."""

    algorithm: str
    capacity: int
    refill_per_sec: float
    window_size_sec: int | None = None


@strawberry.type
class RetryPolicyType:
    """Retry policy configuration."""

    strategy: str
    max_retries: int
    base_delay_ms: int
    max_delay_ms: int | None = None
    retry_on_status: list[int]


@strawberry.type
class OperationSchemaType:
    """Schema information for an operation."""

    operation: str
    method: str
    path: str
    description: str | None = None
    request_body: JSON | None = None
    query_params: JSON | None = None
    response: JSON | None = None


@strawberry.type
class OperationType:
    """API operation definition."""

    name: str
    method: str
    path: str
    description: str | None = None
    required_scopes: list[str] | None = None
    has_pagination: bool = False
    timeout_override: float | None = None


@strawberry.type
class ProviderMetadataType:
    """Provider metadata."""

    version: str
    type: str  # 'manifest' or 'programmatic'
    manifest_path: str | None = None
    description: str | None = None
    documentation_url: str | None = None
    support_email: str | None = None


@strawberry.type
class ProviderType:
    """API provider information."""

    name: str
    operations: list[OperationType]
    metadata: ProviderMetadataType
    base_url: str | None = None
    auth_config: AuthConfigType | None = None
    rate_limit: RateLimitConfigType | None = None
    retry_policy: RetryPolicyType | None = None
    default_timeout: float = 30.0


@strawberry.type
class ProviderStatisticsType:
    """Provider registry statistics."""

    total_providers: int
    total_operations: int
    provider_types: JSON  # Dict[str, int]
    providers: list[JSON]  # List of provider summary


@strawberry.type
class IntegrationTestResultType:
    """Result of an integration test."""

    success: bool
    provider: str
    operation: str
    status_code: int | None = None
    response_time_ms: float | None = None
    error: str | None = None
    response_preview: JSON | None = None


@strawberry.input
class ExecuteIntegrationInput:
    """Input for executing an integration operation."""

    provider: str
    operation: str
    config: JSON
    api_key_id: strawberry.ID | None = None
    timeout: int | None = None
    resource_id: str | None = None


@strawberry.input
class TestIntegrationInput:
    """Input for testing an integration."""

    provider: str
    operation: str
    config_preview: JSON
    api_key_id: strawberry.ID | None = None
    dry_run: bool = True
