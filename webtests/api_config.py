import json
import math
from pathlib import Path
from urllib.parse import urlparse

from webtests.config import resolve_text


def load_api_config(path):
    config_path = Path(path)
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read API configuration '{config_path}': {exc}") from exc

    if not isinstance(config, dict):
        raise ValueError("API configuration must be a JSON object.")
    base_url = config.get("base_url")
    parsed_url = urlparse(base_url) if isinstance(base_url, str) else None
    if parsed_url is None or parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("API base_url must be a valid http(s) URL.")

    requests_config = config.get("requests")
    if not isinstance(requests_config, dict):
        raise ValueError("API configuration requires a requests object.")
    for field in ("timeout_seconds", "max_response_seconds"):
        value = requests_config.get(field)
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or value <= 0
        ):
            raise ValueError(f"requests.{field} must be a positive number.")
    list_limit = requests_config.get("user_list_limit")
    if not isinstance(list_limit, int) or isinstance(list_limit, bool) or list_limit <= 0:
        raise ValueError("requests.user_list_limit must be a positive integer.")

    endpoints = config.get("endpoints")
    if not isinstance(endpoints, dict):
        raise ValueError("API configuration requires an endpoints object.")
    required_endpoints = {"users", "user_by_id", "missing_user", "login", "current_user"}
    if not required_endpoints <= endpoints.keys():
        missing = ", ".join(sorted(required_endpoints - endpoints.keys()))
        raise ValueError(f"API configuration is missing endpoints: {missing}.")
    for name in required_endpoints:
        endpoint = endpoints[name]
        if not isinstance(endpoint, str) or not endpoint.startswith("/"):
            raise ValueError(f"endpoints.{name} must be a path beginning with '/'.")

    credentials = config.get("credentials")
    if not isinstance(credentials, dict):
        raise ValueError("API configuration requires credentials.")
    for field in ("username", "password"):
        value = credentials.get(field)
        if not isinstance(value, str) or not value:
            raise ValueError(f"credentials.{field} must be a non-empty string.")
    credentials["username"] = resolve_text(credentials["username"])
    credentials["password"] = resolve_text(credentials["password"])

    expected = config.get("expected")
    if not isinstance(expected, dict):
        raise ValueError("API configuration requires an expected object.")
    for field in ("success_status", "not_found_status", "user_id"):
        value = expected.get(field)
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"expected.{field} must be an integer.")
    for field in ("unauthorized_statuses", "invalid_login_statuses"):
        statuses = expected.get(field)
        if (
            not isinstance(statuses, list)
            or not statuses
            or any(not isinstance(status, int) or isinstance(status, bool) for status in statuses)
        ):
            raise ValueError(f"expected.{field} must be a non-empty list of status codes.")
    if not isinstance(expected.get("username"), str) or not expected["username"]:
        raise ValueError("expected.username must be a non-empty string.")
    for field in ("invalid_password", "invalid_token"):
        if not isinstance(config.get(field), str) or not config[field]:
            raise ValueError(f"{field} must be a non-empty string.")

    config["base_url"] = base_url.rstrip("/")
    return config


def api_url(config, endpoint_name):
    return f"{config['base_url']}{config['endpoints'][endpoint_name]}"
