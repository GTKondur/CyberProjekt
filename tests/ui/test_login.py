from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.saucedemo.com/"


def login(driver, user, password):
    driver.get(URL)
    driver.find_element(By.ID, "user-name").send_keys(user)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "login-button").click()


def error_text(driver):
    error = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-test='error']"))
    )
    return error.text


def test_login_poprawne_dane(driver):
    login(driver, "standard_user", "secret_sauce")
    WebDriverWait(driver, 5).until(EC.url_contains("inventory"))
    assert len(driver.find_elements(By.CLASS_NAME, "inventory_item")) > 0


def test_login_bledne_haslo(driver):
    login(driver, "standard_user", "zle_haslo")
    assert "do not match" in error_text(driver)


def test_login_uzytkownik_zablokowany(driver):
    login(driver, "locked_out_user", "secret_sauce")
    assert "locked out" in error_text(driver)


def test_login_puste_pola(driver):
    login(driver, "", "")
    assert "Username is required" in error_text(driver)