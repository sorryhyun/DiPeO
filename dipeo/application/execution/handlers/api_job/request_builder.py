import contextlib
import json
from typing import Any

from dipeo.diagram_generated.enums import HttpMethod


def parse_json_inputs(headers: Any, params: Any, body: Any, auth_config: Any) -> dict[str, Any]:
    """Parse and validate JSON inputs for API request.

    Args:
        headers: Headers dict or JSON string
        params: Params dict or JSON string
        body: Body data (any type)
        auth_config: Auth config dict or JSON string

    Returns:
        Dictionary with parsed headers, params, body, and auth_config
        Returns dict with 'error' key if parsing fails
    """
    result = {
        "headers": headers or {},
        "params": params or {},
        "body": body,
        "auth_config": auth_config or {},
    }

    if isinstance(headers, str):
        try:
            result["headers"] = json.loads(headers)
        except json.JSONDecodeError:
            return {"error": "Invalid headers JSON format"}

    if isinstance(params, str):
        try:
            result["params"] = json.loads(params)
        except json.JSONDecodeError:
            return {"error": "Invalid params JSON format"}

    if isinstance(body, str) and body.strip():
        with contextlib.suppress(json.JSONDecodeError):
            result["body"] = json.loads(body)

    if isinstance(auth_config, str) and auth_config.strip():
        try:
            result["auth_config"] = json.loads(auth_config)
        except json.JSONDecodeError:
            return {"error": "Invalid auth_config JSON format"}

    return result


def prepare_auth(auth_type: str, auth_config: dict) -> dict[str, str] | None:
    """Prepare authentication credentials for HTTP request.

    Args:
        auth_type: Type of authentication (none, basic, bearer, api_key)
        auth_config: Authentication configuration

    Returns:
        Auth dict for basic auth, or None for other auth types
    """
    if auth_type == "none":
        return None

    if auth_type == "basic":
        username = auth_config.get("username", "")
        password = auth_config.get("password", "")
        if username and password:
            return {"username": username, "password": password}

    return None


def apply_auth_headers(headers: dict, auth_type: str, auth_config: dict) -> dict:
    """Apply authentication headers to request headers.

    Args:
        headers: Existing headers dictionary
        auth_type: Type of authentication
        auth_config: Authentication configuration

    Returns:
        Updated headers dictionary with auth headers added
    """
    headers = headers.copy()

    if auth_type == "bearer":
        token = auth_config.get("token", "")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    elif auth_type == "api_key":
        key_name = auth_config.get("key_name", "X-API-Key")
        key_value = auth_config.get("key_value", "")
        if key_value:
            headers[key_name] = key_value

    return headers


def prepare_request_data(method: HttpMethod, params: dict, body: Any) -> dict[str, Any] | None:
    """Prepare request data based on HTTP method.

    Args:
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        params: Query parameters
        body: Request body

    Returns:
        Request data to send, or None for GET requests
    """
    if method == HttpMethod.GET:
        return None

    if body is not None:
        return body

    if method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH] and params:
        return params

    return None
