import json
from urllib.parse import urljoin
from pathlib import Path

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
AXE = (HERE / "axe.min.js").read_text(encoding="utf-8")
REPORTS = HERE.parent.parent / "reports"

RUN_AXE = """
const done = arguments[arguments.length - 1];
axe.run(document, {runOnly: {type: 'tag', values: arguments[0]}})
  .then(r => done(r))
  .catch(e => done({error: String(e)}));
"""


def load_wcag_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(config.get("base_url"), str):
        raise ValueError("WCAG config requires a base_url.")
    if not isinstance(config.get("axe_tags"), list) or not config["axe_tags"]:
        raise ValueError("WCAG config requires a non-empty axe_tags list.")
    if not isinstance(config.get("pages"), list) or not config["pages"]:
        raise ValueError("WCAG config requires a non-empty pages list.")
    return config


def audit(driver, page, tags):
    """Uruchamia axe na otwartej stronie, zapisuje JSON i zwraca listę naruszeń."""
    driver.set_script_timeout(30)
    driver.execute_script(AXE)
    result = driver.execute_async_script(RUN_AXE, tags)
    assert "error" not in result, result.get("error")
    violations = result["violations"]

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"wcag_{page}.json").write_text(
        json.dumps(violations, ensure_ascii=False, indent=2), encoding="utf-8")
    for v in violations:
        print(f"[{v['impact']}] {v['id']}: {v['help']} (elementów: {len(v['nodes'])})")
    return violations


def open_configured_page(driver, page, config):
    if page["type"] == "local":
        driver.get((ROOT / page["path"]).resolve().as_uri())
        return
    if page["type"] != "web":
        raise ValueError(f"Unsupported page type: {page['type']}")

    driver.get(urljoin(config["base_url"], page["path"]))
    if page.get("login_required"):
        login = config["login"]
        for key in ("username_locator", "password_locator", "submit_locator"):
            locator = login[key]
            if locator.get("by") != "id":
                raise ValueError(f"Unsupported login locator type: {locator.get('by')}")
        driver.find_element(By.ID, login["username_locator"]["value"]).send_keys(
            login["username"]
        )
        driver.find_element(By.ID, login["password_locator"]["value"]).send_keys(
            login["password"]
        )
        driver.find_element(By.ID, login["submit_locator"]["value"]).click()
        WebDriverWait(driver, config["browser"]["timeout_seconds"]).until(
            EC.url_contains(login["success_url_contains"])
        )


def pytest_generate_tests(metafunc):
    if "wcag_page" not in metafunc.fixturenames:
        return
    config_path = metafunc.config.getoption("--wcag-config")
    config = load_wcag_config(config_path)
    metafunc.parametrize(
        "wcag_page",
        config["pages"],
        ids=[page["name"] for page in config["pages"]],
    )


def test_audyt_wcag(driver, record_property, wcag_page, request):
    config = load_wcag_config(request.config.getoption("--wcag-config"))
    open_configured_page(driver, wcag_page, config)
    violations = audit(driver, wcag_page["id"], config["axe_tags"])
    record_property("violations", len(violations))
    found = {violation["id"] for violation in violations}
    expected = set(wcag_page["expected_violation_ids"])
    if expected:
        assert expected <= found, f"Expected WCAG violations {expected}, found {found}."
    else:
        assert not violations, f"Znaleziono naruszeń WCAG: {len(violations)}"