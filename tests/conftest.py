from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ROOT = Path(__file__).parent.parent
SCREENSHOTS = ROOT / "reports" / "screenshots"


def pytest_addoption(parser):
    parser.addoption("--headless", action="store_true",
                     default=None, help="Uruchom przeglądarkę bez okna")
    parser.addoption(
        "--webtest-config",
        help="JSON file containing configurable browser tests",
    )
    parser.addoption(
        "--webtest-url",
        help="Override the base URL in the web-test configuration",
    )
    parser.addoption(
        "--wcag-config",
        default=str(ROOT / "configs" / "accessibility.json"),
        help="JSON file with WCAG audit settings",
    )
    parser.addoption(
        "--api-config",
        default=str(ROOT / "configs" / "api.json"),
        help="JSON file with API test settings",
    )
    parser.addoption(
        "--results-file",
        default=str(ROOT / "reports" / "results.json"),
        help="Path to the JSON test-results report",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):

    outcome = yield
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)


@pytest.fixture
def driver(request):
    options = Options()
    config_path = request.config.getoption("--webtest-config")
    config_browser = {}
    if config_path:
        from webtests.config import load_config

        config_browser = load_config(config_path)["browser"]
    elif request.node.path.is_relative_to(ROOT / "tests" / "accessibility"):
        import json

        wcag_config_path = Path(request.config.getoption("--wcag-config"))
        wcag_config = json.loads(wcag_config_path.read_text(encoding="utf-8"))
        config_browser = wcag_config["browser"]
    headless = request.config.getoption("--headless")
    if headless is True or (headless is None and config_browser.get("headless", False)):
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
    })
    drv = webdriver.Chrome(options=options)
    try:
        yield drv
    finally:
        try:
            rep = getattr(request.node, "rep_call", None)
            if rep is not None and rep.failed:
                SCREENSHOTS.mkdir(parents=True, exist_ok=True)
                drv.save_screenshot(str(SCREENSHOTS / f"{request.node.name}.png"))
        finally:
            drv.quit()

    
import json

CATEGORIES = {
    "ui": "UI",
    "api": "API",
    "accessibility": "Dostępność",
    "security": "Bezpieczeństwo",
    "config_driven": "Konfigurowalne",
}
_results = []


def pytest_runtest_logreport(report):
    # liczymy test po fazie "call" (właściwy test) albo gdy padło jego przygotowanie
    if report.when == "call" or (report.when == "setup" and report.failed):
        parts = report.nodeid.split("/")
        category = CATEGORIES.get(parts[1], parts[1]) if len(parts) > 2 else "Inne"
        test = {
            "name": report.nodeid.split("::")[-1].replace("test_", "").replace("_", " "),
            "category": category,
            "status": "passed" if report.passed else "failed",
            "duration": round(report.duration, 2),
        }
        violations = dict(report.user_properties).get("violations")
        if violations is not None:
            test["violations"] = violations
        _results.append(test)


def pytest_sessionfinish(session, exitstatus):
    results_file = Path(session.config.getoption("--results-file"))
    results_file.parent.mkdir(parents=True, exist_ok=True)
    results_file.write_text(
        json.dumps({"tests": _results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )