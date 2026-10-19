import json

import pytest

from webtests.config import load_config, resolve_text
from webtests.runner import execute_test


def write_config(path, **overrides):
    config = {
        "base_url": "https://example.test",
        "browser": {"headless": True, "timeout_seconds": 2},
        "tests": [{"name": "smoke", "steps": [{"action": "assert_url_contains", "value": "home"}]}],
    }
    config.update(overrides)
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def test_load_config_accepts_valid_config_and_url_override(tmp_path):
    path = write_config(tmp_path / "tests.json")

    config = load_config(path, "https://override.test")

    assert config["base_url"] == "https://override.test"
    assert config["browser"]["timeout_seconds"] == 2.0
    assert config["tests"][0]["name"] == "smoke"


def test_load_config_rejects_unknown_actions(tmp_path):
    path = write_config(
        tmp_path / "tests.json",
        tests=[{"name": "invalid", "steps": [{"action": "run_python"}]}],
    )

    with pytest.raises(ValueError, match="action"):
        load_config(path)


def test_load_config_rejects_non_http_base_url(tmp_path):
    path = write_config(tmp_path / "tests.json", base_url="javascript:alert(1)")

    with pytest.raises(ValueError, match="base_url"):
        load_config(path)


def test_load_config_accepts_alert_action(tmp_path):
    path = write_config(
        tmp_path / "tests.json",
        tests=[{"name": "accept alert", "steps": [{"action": "accept_alert"}]}],
    )

    config = load_config(path)

    assert config["tests"][0]["steps"] == [{"action": "accept_alert"}]


def test_resolve_text_requires_environment_variables(monkeypatch):
    monkeypatch.setenv("WEBTEST_PASSWORD", "example")

    assert resolve_text("secret=${WEBTEST_PASSWORD}") == "secret=example"
    with pytest.raises(ValueError, match="NOT_SET"):
        resolve_text("${WEBTEST_NOT_SET}")


def test_execute_test_navigates_to_configured_base_url(monkeypatch):
    class FakeWait:
        def __init__(self, driver, timeout):
            self.driver = driver

        def until(self, condition):
            assert condition(self.driver)

    class FakeDriver:
        current_url = ""

        def get(self, url):
            self.current_url = url

    from webtests import runner

    driver = FakeDriver()
    monkeypatch.setattr(runner, "WebDriverWait", FakeWait)
    execute_test(
        driver,
        {"name": "smoke", "steps": [{"action": "assert_url_contains", "value": "home"}]},
        "https://example.test/home",
        2,
    )

    assert driver.current_url == "https://example.test/home"


def test_execute_test_accepts_javascript_alert(monkeypatch):
    class FakeAlert:
        accepted = False

        def accept(self):
            self.accepted = True

    class FakeSwitchTo:
        def __init__(self, alert):
            self.alert = alert

    class FakeWait:
        def __init__(self, driver, timeout):
            self.driver = driver

        def until(self, condition):
            return condition(self.driver)

    class FakeDriver:
        def __init__(self, alert):
            self.switch_to = FakeSwitchTo(alert)

        def get(self, url):
            self.url = url

    from webtests import runner

    alert = FakeAlert()
    driver = FakeDriver(alert)
    monkeypatch.setattr(runner, "WebDriverWait", FakeWait)
    execute_test(
        driver,
        {"name": "accept alert", "steps": [{"action": "accept_alert"}]},
        "https://example.test",
        2,
    )

    assert alert.accepted


def test_execute_test_supports_asserting_zero_matching_elements(monkeypatch):
    class FakeWait:
        def __init__(self, driver, timeout):
            self.driver = driver

        def until(self, condition):
            return condition(self.driver)

    class FakeDriver:
        def get(self, url):
            self.url = url

        def find_elements(self, by, value):
            return []

    from webtests import runner

    driver = FakeDriver()
    monkeypatch.setattr(runner, "WebDriverWait", FakeWait)
    execute_test(
        driver,
        {
            "name": "empty cart badge",
            "steps": [
                {"action": "assert_count", "by": "class_name", "value": "badge", "count": 0}
            ],
        },
        "https://example.test",
        2,
    )
