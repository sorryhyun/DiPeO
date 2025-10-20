import contextlib
import json
from typing import Any

from dipeo.diagram_generated.enums import HttpMethod


def parse_json_inputs(headers: Any, params: Any, body: Any, auth_config: Any) -> dict[str, Any]:
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
    if auth_type == "none":
        return None

    if auth_type == "basic":
        username = auth_config.get("username", "")
        password = auth_config.get("password", "")
        if username and password:
            return {"username": username, "password": password}

    return None


def apply_auth_headers(headers: dict, auth_type: str, auth_config: dict) -> dict:
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
    if method == HttpMethod.GET:
        return None

    if body is not None:
        return body

    if method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH] and params:
        return params

    return None
