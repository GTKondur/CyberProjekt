import pytest
import requests

BASE = "https://dummyjson.com"
USER = {"username": "emilys", "password": "emilyspass"}


@pytest.fixture(scope="session")
def token():
    
    r = requests.post(f"{BASE}/auth/login", json=USER, timeout=10)
    assert r.status_code == 200, "Logowanie nie powiodło się, sprawdź dane testowe"
    return r.json()["accessToken"]
