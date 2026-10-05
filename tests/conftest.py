from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

SCREENSHOTS = Path(__file__).parent.parent / "reports" / "screenshots"


def pytest_addoption(parser):
    parser.addoption("--headless", action="store_true",
                     help="Uruchom przeglądarkę bez okna")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):

    outcome = yield
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)


@pytest.fixture
def driver(request):
    options = Options()
    if request.config.getoption("--headless"):
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
    })
    drv = webdriver.Chrome(options=options)
    yield drv  

    
    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        SCREENSHOTS.mkdir(parents=True, exist_ok=True)
        drv.save_screenshot(str(SCREENSHOTS / f"{request.node.name}.png"))
    drv.quit()

    
import json

RESULTS_FILE = Path(__file__).parent.parent / "reports" / "results.json"
CATEGORIES = {
    "ui": "UI",
    "api": "API",
    "accessibility": "Dostępność",
    "security": "Bezpieczeństwo",
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
    if _results:
        RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        RESULTS_FILE.write_text(
            json.dumps({"tests": _results}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )