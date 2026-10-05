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