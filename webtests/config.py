import json
import math
import os
import re
from pathlib import Path


LOCATORS = {
    "id",
    "name",
    "class_name",
    "css_selector",
    "xpath",
    "tag_name",
    "link_text",
    "partial_link_text",
}
LOCATOR_ACTIONS = {
    "click",
    "type",
    "clear",
    "wait_visible",
    "assert_visible",
    "assert_not_visible",
    "assert_text_contains",
    "assert_count",
}
SUPPORTED_ACTIONS = LOCATOR_ACTIONS | {
    "assert_url_contains",
    "assert_title_contains",
    "accept_alert",
}
ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def load_config(path, base_url_override=None):
    """Load and validate a JSON web-test configuration."""
    config_path = Path(path)
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read test configuration '{config_path}': {exc}") from exc

    if not isinstance(config, dict):
        raise ValueError("Configuration must be a JSON object.")
    base_url = base_url_override or config.get("base_url")
    if not isinstance(base_url, str) or not base_url.startswith(("http://", "https://", "file://")):
        raise ValueError("base_url must be an http(s) or file URL.")

    browser = config.get("browser", {})
    if not isinstance(browser, dict):
        raise ValueError("browser must be a JSON object.")
    timeout = browser.get("timeout_seconds", 5)
    if (
        not isinstance(timeout, (int, float))
        or isinstance(timeout, bool)
        or not math.isfinite(timeout)
        or timeout <= 0
    ):
        raise ValueError("browser.timeout_seconds must be a positive number.")
    if "headless" in browser and not isinstance(browser["headless"], bool):
        raise ValueError("browser.headless must be true or false.")

    test_cases = config.get("tests")
    if not isinstance(test_cases, list) or not test_cases:
        raise ValueError("tests must be a non-empty JSON array.")
    names = set()
    for index, case in enumerate(test_cases):
        prefix = f"tests[{index}]"
        if not isinstance(case, dict) or not isinstance(case.get("name"), str) or not case["name"].strip():
            raise ValueError(f"{prefix}.name must be a non-empty string.")
        if case["name"] in names:
            raise ValueError(f"Test names must be unique: '{case['name']}'.")
        names.add(case["name"])
        steps = case.get("steps")
        if not isinstance(steps, list) or not steps:
            raise ValueError(f"{prefix}.steps must be a non-empty array.")
        for step_index, step in enumerate(steps):
            _validate_step(step, f"{prefix}.steps[{step_index}]")

    config["base_url"] = base_url
    config["browser"] = {**browser, "timeout_seconds": float(timeout)}
    return config


def _validate_step(step, location):
    if not isinstance(step, dict):
        raise ValueError(f"{location} must be a JSON object.")
    action = step.get("action")
    if not isinstance(action, str) or action not in SUPPORTED_ACTIONS:
        raise ValueError(
            f"{location}.action must be one of: {', '.join(sorted(SUPPORTED_ACTIONS))}."
        )
    if action in LOCATOR_ACTIONS:
        by = step.get("by")
        value = step.get("value")
        if not isinstance(by, str) or by not in LOCATORS:
            raise ValueError(f"{location}.by must be one of: {', '.join(sorted(LOCATORS))}.")
        if not isinstance(value, str) or not value:
            raise ValueError(f"{location}.value must be a non-empty locator string.")
    if action == "type" and not isinstance(step.get("text"), str):
        raise ValueError(f"{location}.text must be a string.")
    if action == "assert_text_contains" and not isinstance(step.get("text"), str):
        raise ValueError(f"{location}.text must be a string.")
    if action in {"assert_url_contains", "assert_title_contains"}:
        if not isinstance(step.get("value"), str) or not step["value"]:
            raise ValueError(f"{location}.value must be a non-empty string.")
    if action == "assert_count":
        count = step.get("count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError(f"{location}.count must be a non-negative integer.")


def resolve_text(text):
    """Substitute ${ENV_VAR} references, failing clearly if one is unset."""
    def replace(match):
        variable = match.group(1)
        if variable not in os.environ:
            raise ValueError(f"Required environment variable '{variable}' is not set.")
        return os.environ[variable]

    return ENV_PATTERN.sub(replace, text)
