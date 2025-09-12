"""Generic HTTP provider that works with manifest definitions."""

import asyncio
import contextlib
import importlib.util
import json
import logging
from pathlib import Path
from typing import Any

import jsonpointer
from jinja2 import Environment, Template, meta

from dipeo.domain.base.exceptions import ServiceError
from dipeo.domain.integrations.ports import APIKeyPort
from dipeo.infrastructure.integrations.adapters.api_service import APIService
from dipeo.infrastructure.integrations.drivers.integrated_api.auth_strategies import (
    AuthStrategyFactory,
)
from dipeo.infrastructure.integrations.drivers.integrated_api.manifest_schema import (
    PaginationType,
    ProviderManifest,
    RetryStrategy,
    validate_manifest,
)
from dipeo.infrastructure.integrations.drivers.integrated_api.providers.base_provider import (
    BaseApiProvider,
)
from dipeo.infrastructure.integrations.drivers.integrated_api.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class GenericHTTPProvider(BaseApiProvider):
    """A zero-code API provider driven by manifest configuration.

    This provider can work with any REST API by reading a manifest file
    that describes the API's endpoints, authentication, and behavior.
    """

    def __init__(
        self,
        manifest: dict[str, Any] | ProviderManifest,
        manifest_dir: Path | None = None,
        api_service: APIService | None = None,
        api_key_port: APIKeyPort | None = None,
    ):
        """Initialize generic provider from manifest.

        Args:
            manifest: Provider manifest (dict or validated ProviderManifest)
            manifest_dir: Directory containing the manifest (for relative paths)
            api_service: APIService for making HTTP requests
            api_key_port: Port for resolving API keys
        """
        # Validate manifest if it's a dict
        if isinstance(manifest, dict):
            self._manifest = validate_manifest(manifest)
        else:
            self._manifest = manifest

        # Initialize base provider
        super().__init__(
            provider_name=self._manifest.name,
            supported_operations=list(self._manifest.operations.keys()),
        )

        self.manifest_dir = manifest_dir or Path.cwd()
        self.api_service = api_service
        self.api_key_port = api_key_port

        # Initialize components
        self.auth_strategy = None
        self.rate_limiter = None
        self.jinja_env = Environment()

        # Cache for loaded schemas and hooks
        self._schema_cache: dict[str, dict] = {}
        self._hook_cache: dict[str, Any] = {}

    @property
    def manifest(self) -> dict:
        """Provider manifest with schemas and capabilities."""
        return self._manifest.__dict__ if hasattr(self._manifest, "__dict__") else self._manifest

    async def initialize(self) -> None:
        """Initialize the provider."""
        await super().initialize()

        # Initialize auth strategy
        self.auth_strategy = AuthStrategyFactory.create(self._manifest.auth, self.api_key_port)

        # Initialize rate limiter if configured
        if self._manifest.rate_limit:
            self.rate_limiter = RateLimiter(self._manifest.rate_limit)

        # Load hooks module if specified
        if self._manifest.hooks_module:
            await self._load_hooks_module()

    async def _execute_operation(
        self,
        operation: str,
        config: dict[str, Any],
        resource_id: str | None,
        api_key: str,
        timeout: float,
    ) -> dict[str, Any]:
        """Execute a specific operation defined in the manifest.

        Args:
            operation: Operation name
            config: Operation configuration from diagram
            resource_id: Optional resource ID
            api_key: API key for authentication
            timeout: Request timeout

        Returns:
            Operation result
        """
        op_config = self._manifest.operations[operation]

        # Apply rate limiting if configured
        if self.rate_limiter:
            rate_limit_config = op_config.rate_limit_override or self._manifest.rate_limit
            if rate_limit_config:
                await self.rate_limiter.acquire(operation)

        # Prepare context for template rendering
        context = {
            "config": config,
            "resource_id": resource_id,
            "api_key": api_key,
            "secret": {},  # Will be populated by auth strategy
        }

        # Execute pre-request hook if defined
        if op_config.pre_request_hook:
            context = await self._execute_hook(op_config.pre_request_hook, "pre_request", context)

        # Build request
        url = self._build_url(op_config.path, context)
        headers = await self._build_headers(op_config, context, api_key)
        body = self._build_body(op_config, context)
        query_params = self._build_query_params(op_config, context)

        # Use operation-specific timeout if provided
        request_timeout = op_config.timeout_override or timeout

        # Execute request with retry logic
        response = await self._execute_with_retry(
            method=op_config.method,
            url=url,
            headers=headers,
            body=body,
            query_params=query_params,
            timeout=request_timeout,
            retry_policy=self._manifest.retry_policy,
        )

        # Process response
        result = self._process_response(response, op_config)

        # Execute post-response hook if defined
        if op_config.post_response_hook:
            result = await self._execute_hook(
                op_config.post_response_hook,
                "post_response",
                {"result": result, "context": context},
            )

        # Handle pagination if configured
        if op_config.pagination and op_config.pagination.type != PaginationType.NONE:
            result = await self._handle_pagination(
                result, op_config, context, headers, request_timeout
            )

        return self._build_success_response(result, operation)

    def _build_url(self, path_template: str, context: dict[str, Any]) -> str:
        """Build the full URL from base URL and path template.

        Args:
            path_template: Path template with placeholders
            context: Template context

        Returns:
            Full URL
        """
        # Render path template
        template = Template(path_template)
        path = template.render(**context)

        # Combine with base URL
        base_url = str(self._manifest.base_url).rstrip("/")
        path = path.lstrip("/")

        return f"{base_url}/{path}"

    async def _build_headers(
        self, op_config, context: dict[str, Any], api_key: str
    ) -> dict[str, str]:
        """Build request headers.

        Args:
            op_config: Operation configuration
            context: Template context
            api_key: API key

        Returns:
            Headers dictionary
        """
        headers = {}

        # Add default headers
        if self._manifest.default_headers:
            headers.update(self._manifest.default_headers)

        # Add operation-specific headers
        if op_config.request and op_config.request.headers_template:
            for key, value_template in op_config.request.headers_template.items():
                template = Template(value_template)
                headers[key] = template.render(**context)

        # Add authentication headers
        if self.auth_strategy:
            auth_headers = await self.auth_strategy.get_auth_headers(api_key, context)
            headers.update(auth_headers)

        # Ensure Content-Type for methods with body
        if op_config.method in ["POST", "PUT", "PATCH"] and "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        return headers

    def _build_body(self, op_config, context: dict[str, Any]) -> dict[str, Any] | None:
        """Build request body.

        Args:
            op_config: Operation configuration
            context: Template context

        Returns:
            Request body or None
        """
        if not op_config.request or not op_config.request.body_template:
            return None

        # Render body template
        template = Template(op_config.request.body_template)
        body_str = template.render(**context)

        # Parse as JSON
        try:
            return json.loads(body_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse body template result as JSON: {e}")
            logger.debug(f"Body template result: {body_str}")
            raise ServiceError(f"Invalid body template result: {e}")

    def _build_query_params(self, op_config, context: dict[str, Any]) -> dict[str, str] | None:
        """Build query parameters.

        Args:
            op_config: Operation configuration
            context: Template context

        Returns:
            Query parameters or None
        """
        if not op_config.request or not op_config.request.query_params_template:
            return None

        params = {}
        for key, value_template in op_config.request.query_params_template.items():
            template = Template(value_template)
            value = template.render(**context)
            if value:  # Only include non-empty values
                params[key] = value

        return params if params else None

    async def _execute_with_retry(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
        query_params: dict[str, str] | None,
        timeout: float,
        retry_policy,
    ) -> dict[str, Any]:
        """Execute HTTP request with retry logic.

        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body
            query_params: Query parameters
            timeout: Request timeout
            retry_policy: Retry policy configuration

        Returns:
            Response data
        """
        if not self.api_service:
            raise ServiceError("APIService not configured")

        # Default retry policy if not specified
        if not retry_policy:
            max_retries = 3
            retry_on_status = [429, 500, 502, 503, 504]
            base_delay = 0.3
            strategy = RetryStrategy.EXPONENTIAL_BACKOFF
        else:
            max_retries = retry_policy.max_retries
            retry_on_status = retry_policy.retry_on_status
            base_delay = retry_policy.base_delay_ms / 1000.0
            strategy = retry_policy.strategy

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # Make the request
                (
                    status_code,
                    response_data,
                    response_headers,
                ) = await self.api_service.execute_request(
                    method=method, url=url, data=body, headers=headers, timeout=timeout
                )

                # Check if we should retry based on status code
                if status_code in retry_on_status and attempt < max_retries:
                    # Calculate delay based on strategy
                    if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                        delay = base_delay * (2**attempt)
                    elif strategy == RetryStrategy.LINEAR_BACKOFF:
                        delay = base_delay * (attempt + 1)
                    else:  # FIXED_DELAY or NONE
                        delay = base_delay

                    # Check for Retry-After header
                    if "Retry-After" in response_headers:
                        with contextlib.suppress(ValueError):
                            delay = float(response_headers["Retry-After"])

                    logger.warning(
                        f"Request failed with status {status_code} "
                        f"(attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)
                    continue

                # Return response
                return {
                    "status_code": status_code,
                    "data": response_data,
                    "headers": response_headers,
                }

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    # Calculate delay
                    if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                        delay = base_delay * (2**attempt)
                    elif strategy == RetryStrategy.LINEAR_BACKOFF:
                        delay = base_delay * (attempt + 1)
                    else:
                        delay = base_delay

                    logger.warning(
                        f"Request failed with error: {e} "
                        f"(attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)
                    continue

        # All retries exhausted
        raise ServiceError(
            f"Request to {url} failed after {max_retries + 1} attempts: {last_error}"
        )

    def _process_response(self, response: dict[str, Any], op_config) -> Any:
        """Process response according to operation configuration.

        Args:
            response: Raw response from API
            op_config: Operation configuration

        Returns:
            Processed response data
        """
        status_code = response["status_code"]
        data = response["data"]

        # Check if response is successful
        success_codes = [200, 201, 202, 204]
        if op_config.response:
            success_codes = op_config.response.success_codes

        if status_code not in success_codes:
            # Extract error message if configured
            error_msg = f"Request failed with status {status_code}"
            error_detail = None
            if op_config.response and op_config.response.error_json_pointer and data:
                try:
                    error_detail = jsonpointer.resolve_pointer(
                        data, op_config.response.error_json_pointer
                    )
                    error_msg = f"{error_msg}: {error_detail}"
                except Exception:
                    pass

            # Include full response for debugging if no specific error found
            if not error_detail and data:
                error_msg = f"{error_msg}. Response: {data}"

            raise ServiceError(error_msg)

        # Extract data using JSON pointer if configured
        if op_config.response and op_config.response.json_pointer:
            try:
                data = jsonpointer.resolve_pointer(data, op_config.response.json_pointer)
            except Exception as e:
                logger.error(f"Failed to extract data using JSON pointer: {e}")
                logger.debug(f"Response data: {data}")

        # Apply transformation if configured
        if op_config.response and op_config.response.transform:
            template = Template(op_config.response.transform)
            data_str = template.render(response=data)
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                # If not JSON, return as string
                data = data_str

        return data

    async def _handle_pagination(
        self,
        initial_result: Any,
        op_config,
        context: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> Any:
        """Handle pagination if configured.

        Args:
            initial_result: Initial response data
            op_config: Operation configuration
            context: Template context
            headers: Request headers
            timeout: Request timeout

        Returns:
            Aggregated results
        """
        # This is a simplified implementation
        # Full implementation would handle different pagination types
        logger.info(f"Pagination handling not fully implemented for {op_config.pagination.type}")
        return initial_result

    async def _load_hooks_module(self) -> None:
        """Load Python module containing hook implementations."""
        if not self._manifest.hooks_module:
            return

        module_path = self.manifest_dir / self._manifest.hooks_module
        if not module_path.exists():
            logger.warning(f"Hooks module not found: {module_path}")
            return

        spec = importlib.util.spec_from_file_location("hooks", module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._hook_cache["module"] = module

    async def _execute_hook(self, hook_name: str, hook_type: str, data: Any) -> Any:
        """Execute a hook function.

        Args:
            hook_name: Hook function name
            hook_type: Type of hook (pre_request, post_response)
            data: Data to pass to hook

        Returns:
            Modified data from hook
        """
        if "module" not in self._hook_cache:
            logger.warning(f"Hooks module not loaded, skipping {hook_name}")
            return data

        module = self._hook_cache["module"]
        if not hasattr(module, hook_name):
            logger.warning(f"Hook function {hook_name} not found in module")
            return data

        hook_func = getattr(module, hook_name)

        try:
            if asyncio.iscoroutinefunction(hook_func):
                result = await hook_func(data)
            else:
                result = hook_func(data)
            return result
        except Exception as e:
            logger.error(f"Hook {hook_name} failed: {e}")
            raise ServiceError(f"Hook execution failed: {e}")

    async def validate_config(self, operation: str, config: dict[str, Any] | None = None) -> bool:
        """Validate operation configuration.

        Args:
            operation: Operation name
            config: Configuration to validate

        Returns:
            True if valid, False otherwise
        """
        if not await super().validate_config(operation, config):
            return False

        if not config:
            return True

        op_config = self._manifest.operations.get(operation)
        if not op_config:
            return False

        # Check if required template variables are present
        if op_config.request:
            # Check body template variables
            if op_config.request.body_template:
                env = Environment()
                ast = env.parse(op_config.request.body_template)
                undeclared = meta.find_undeclared_variables(ast)

                for var in undeclared:
                    if var.startswith("config."):
                        config_key = var[7:]  # Remove "config." prefix
                        if config_key not in config:
                            logger.warning(f"Missing required config key: {config_key}")
                            return False

        return True

    def get_operation_schema(self, operation: str) -> dict[str, Any] | None:
        """Get the schema for an operation.

        Args:
            operation: Operation name

        Returns:
            Operation schema or None
        """
        op_config = self._manifest.operations.get(operation)
        if not op_config:
            return None

        schema = {
            "operation": operation,
            "method": op_config.method,
            "path": op_config.path,
            "description": op_config.description,
        }

        # Add request schema if available
        if op_config.request:
            if op_config.request.body_schema:
                schema["request_body"] = self._load_schema(op_config.request.body_schema)
            if op_config.request.query_params_schema:
                schema["query_params"] = self._load_schema(op_config.request.query_params_schema)

        # Add response schema if available
        if op_config.response and op_config.response.schema:
            schema["response"] = self._load_schema(op_config.response.schema)

        return schema

    def _load_schema(self, schema_ref: str) -> dict[str, Any]:
        """Load a JSON schema from reference.

        Args:
            schema_ref: Schema reference (inline or file path)

        Returns:
            Schema dictionary
        """
        # Check cache
        if schema_ref in self._schema_cache:
            return self._schema_cache[schema_ref]

        # Check if it's an inline schema (starts with {)
        if schema_ref.startswith("{"):
            try:
                schema = json.loads(schema_ref)
                self._schema_cache[schema_ref] = schema
                return schema
            except json.JSONDecodeError:
                logger.error(f"Invalid inline schema: {schema_ref}")
                return {}

        # Load from file
        if schema_ref.startswith("schema://"):
            # Remove schema:// prefix
            schema_path = schema_ref[9:]

            # Look in schemas directory if configured
            if self._manifest.schemas_directory:
                full_path = self.manifest_dir / self._manifest.schemas_directory / schema_path
            else:
                full_path = self.manifest_dir / schema_path

            try:
                with open(full_path) as f:
                    schema = json.load(f)
                    self._schema_cache[schema_ref] = schema
                    return schema
            except Exception as e:
                logger.error(f"Failed to load schema from {full_path}: {e}")
                return {}

        # Return empty schema if we can't load it
        return {}
