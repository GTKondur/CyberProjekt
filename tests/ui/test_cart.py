from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

PRODUCT = "Sauce Labs Backpack"
ADD_BUTTON = "add-to-cart-sauce-labs-backpack"
REMOVE_BUTTON = "remove-sauce-labs-backpack"


def badge(driver):
    return driver.find_elements(By.CLASS_NAME, "shopping_cart_badge")


def test_lista_produktow(logged_in):
    items = logged_in.find_elements(By.CLASS_NAME, "inventory_item")
    assert len(items) == 6


def test_dodanie_do_koszyka_zwieksza_licznik(logged_in):
    logged_in.find_element(By.ID, ADD_BUTTON).click()
    assert badge(logged_in)[0].text == "1"


def test_produkt_widoczny_w_koszyku(logged_in):
    logged_in.find_element(By.ID, ADD_BUTTON).click()
    logged_in.find_element(By.CLASS_NAME, "shopping_cart_link").click()
    WebDriverWait(logged_in, 5).until(EC.url_contains("cart"))
    names = [e.text for e in logged_in.find_elements(By.CLASS_NAME, "inventory_item_name")]
    assert PRODUCT in names


def test_usuniecie_z_koszyka(logged_in):
    logged_in.find_element(By.ID, ADD_BUTTON).click()
    logged_in.find_element(By.ID, REMOVE_BUTTON).click()
    assert badge(logged_in) == []