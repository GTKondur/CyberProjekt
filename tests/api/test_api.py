import requests

BASE = "https://dummyjson.com"
USER = {"username": "emilys", "password": "emilyspass"}



def test_lista_uzytkownikow():
    r = requests.get(f"{BASE}/users", params={"limit": 5}, timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert len(data["users"]) == 5
    assert "total" in data


def test_pojedynczy_uzytkownik():
    r = requests.get(f"{BASE}/users/1", timeout=10)
    assert r.status_code == 200
    assert r.json()["id"] == 1


def test_nieistniejacy_uzytkownik():
    r = requests.get(f"{BASE}/users/99999", timeout=10)
    assert r.status_code == 404


def test_czas_odpowiedzi():
    r = requests.get(f"{BASE}/users/1", timeout=10)
    assert r.elapsed.total_seconds() < 3


def test_login_zwraca_token():
    r = requests.post(f"{BASE}/auth/login", json=USER, timeout=10)
    assert r.status_code == 200
    assert r.json()["accessToken"]


def test_login_bledne_haslo():
    r = requests.post(f"{BASE}/auth/login",
                      json={**USER, "password": "zle"}, timeout=10)
    assert r.status_code in (400, 401)


def test_me_z_tokenem(token):
    r = requests.get(f"{BASE}/auth/me",
                     headers={"Authorization": f"Bearer {token}"}, timeout=10)
    assert r.status_code == 200
    assert r.json()["username"] == USER["username"]


def test_me_bez_tokena():
    r = requests.get(f"{BASE}/auth/me", timeout=10)
    assert r.status_code in (401, 403)


def test_me_zly_token():
    r = requests.get(f"{BASE}/auth/me",
                     headers={"Authorization": "Bearer to_nie_jest_token"}, timeout=10)
    assert r.status_code in (401, 403)