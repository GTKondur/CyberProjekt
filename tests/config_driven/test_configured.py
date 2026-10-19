import pytest

from webtests.config import load_config
from webtests.runner import execute_test


def pytest_generate_tests(metafunc):
    if "configured_case" not in metafunc.fixturenames:
        return
    config_path = metafunc.config.getoption("--webtest-config")
    if not config_path:
        metafunc.parametrize(
            "configured_case",
            [
                pytest.param(
                    None,
                    marks=pytest.mark.skip(
                        reason="Pass --webtest-config to run browser scenarios."
                    ),
                )
            ],
            ids=["configuration-required"],
        )
        return
    config = load_config(
        config_path,
        base_url_override=metafunc.config.getoption("--webtest-url"),
    )
    metafunc.parametrize(
        "configured_case",
        config["tests"],
        ids=[case["name"] for case in config["tests"]],
    )


def test_configured_browser_scenario(driver, configured_case, request):
    config = load_config(
        request.config.getoption("--webtest-config"),
        base_url_override=request.config.getoption("--webtest-url"),
    )
    execute_test(
        driver,
        configured_case,
        config["base_url"],
        config["browser"]["timeout_seconds"],
    )
