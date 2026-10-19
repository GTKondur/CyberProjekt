from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from webtests.config import resolve_text


BY = {
    "id": By.ID,
    "name": By.NAME,
    "class_name": By.CLASS_NAME,
    "css_selector": By.CSS_SELECTOR,
    "xpath": By.XPATH,
    "tag_name": By.TAG_NAME,
    "link_text": By.LINK_TEXT,
    "partial_link_text": By.PARTIAL_LINK_TEXT,
}


def execute_test(driver, case, base_url, timeout):
    driver.get(base_url)
    wait = WebDriverWait(driver, timeout)

    for index, step in enumerate(case["steps"], start=1):
        action = step["action"]
        locator = (BY[step["by"]], step["value"]) if "by" in step else None
        description = f"{case['name']} — step {index}: {action}"
        print(description, flush=True)

        if action == "click":
            wait.until(EC.element_to_be_clickable(locator)).click()
        elif action == "type":
            element = wait.until(EC.visibility_of_element_located(locator))
            element.send_keys(resolve_text(step["text"]))
        elif action == "clear":
            wait.until(EC.visibility_of_element_located(locator)).clear()
        elif action in {"wait_visible", "assert_visible"}:
            wait.until(EC.visibility_of_element_located(locator))
        elif action == "assert_not_visible":
            wait.until(EC.invisibility_of_element_located(locator))
        elif action == "assert_text_contains":
            expected = resolve_text(step["text"])
            wait.until(EC.text_to_be_present_in_element(locator, expected))
        elif action == "assert_count":
            count_matches = wait.until(
                lambda current_driver: len(current_driver.find_elements(*locator))
                == step["count"]
            )
            assert count_matches
        elif action == "assert_url_contains":
            wait.until(EC.url_contains(step["value"]))
        elif action == "assert_title_contains":
            wait.until(EC.title_contains(step["value"]))
        elif action == "accept_alert":
            wait.until(EC.alert_is_present()).accept()
