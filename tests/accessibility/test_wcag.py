import json
from pathlib import Path

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

HERE = Path(__file__).parent
AXE = (HERE / "axe.min.js").read_text(encoding="utf-8")
BROKEN_PAGE = (HERE / "zepsuta.html").as_uri()
REPORTS = HERE.parent.parent / "reports"
URL = "https://www.saucedemo.com/"
TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]

RUN_AXE = """
const done = arguments[arguments.length - 1];
axe.run(document, {runOnly: {type: 'tag', values: arguments[0]}})
  .then(r => done(r))
  .catch(e => done({error: String(e)}));
"""


def audit(driver, page):
    """Uruchamia axe na otwartej stronie, zapisuje JSON i zwraca listę naruszeń."""
    driver.set_script_timeout(30)
    driver.execute_script(AXE)
    result = driver.execute_async_script(RUN_AXE, TAGS)
    assert "error" not in result, result.get("error")
    violations = result["violations"]

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"wcag_{page}.json").write_text(
        json.dumps(violations, ensure_ascii=False, indent=2), encoding="utf-8")
    for v in violations:
        print(f"[{v['impact']}] {v['id']}: {v['help']} (elementów: {len(v['nodes'])})")
    return violations


def open_login(driver):
    driver.get(URL)


def open_inventory(driver):
    driver.get(URL)
    driver.find_element(By.ID, "user-name").send_keys("standard_user")
    driver.find_element(By.ID, "password").send_keys("secret_sauce")
    driver.find_element(By.ID, "login-button").click()
    WebDriverWait(driver, 5).until(EC.url_contains("inventory"))


@pytest.mark.parametrize("opener", [
    pytest.param(open_login, id="strona-logowania"),
    pytest.param(open_inventory, id="lista-produktow"),
])
def test_audyt_wcag(driver, record_property, opener, request):
    opener(driver)
    violations = audit(driver, request.node.callspec.id)
    record_property("violations", len(violations))
    assert not violations, f"Znaleziono naruszeń WCAG: {len(violations)}"


def test_audyt_wykrywa_bledy_na_zepsutej_stronie(driver):
   
    driver.get(BROKEN_PAGE)
    violations = audit(driver, "zepsuta-strona")
    found = {v["id"] for v in violations}
    assert {"image-alt", "button-name"} <= found