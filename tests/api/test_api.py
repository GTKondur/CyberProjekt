import requests

from webtests.api_config import api_url


def test_lista_uzytkownikow(api_config):
    response = requests.get(
        api_url(api_config, "users"),
        params={"limit": api_config["requests"]["user_list_limit"]},
        timeout=api_config["requests"]["timeout_seconds"],
    )
    assert response.status_code == api_config["expected"]["success_status"]
    data = response.json()
    assert len(data["users"]) == api_config["requests"]["user_list_limit"]
    assert "total" in data


def test_pojedynczy_uzytkownik(api_config):
    response = requests.get(
        api_url(api_config, "user_by_id"),
        timeout=api_config["requests"]["timeout_seconds"],
    )
    assert response.status_code == api_config["expected"]["success_status"]
    assert response.json()["id"] == api_config["expected"]["user_id"]


def test_nieistniejacy_uzytkownik(api_config):
    response = requests.get(
        api_url(api_config, "missing_user"),
        timeout=api_config["requests"]["timeout_seconds"],
    )
    assert response.status_code == api_config["expected"]["not_found_status"]


def test_czas_odpowiedzi(api_config):
    response = requests.get(
        api_url(api_config, "user_by_id"),
        timeout=api_config["requests"]["timeout_seconds"],
    )
    assert response.status_code == api_config["expected"]["success_status"]
    assert response.elapsed.total_seconds() < api_config["requests"]["max_response_seconds"]


def test_login_zwraca_token(api_config):
    response = requests.post(
        api_url(api_config, "login"),
        json=api_config["credentials"],
        timeout=api_config["requests"]["timeout_seconds"],
    )
    assert response.status_code == api_config["expected"]["success_status"]
    assert response.json()["accessToken"]


def test_login_bledne_haslo(api_config):
    credentials = {
        **api_config["credentials"],
        "password": api_config["invalid_password"],
    }
    response = requests.post(
        api_url(api_config, "login"),
        json=credentials,
        timeout=api_config["requests"]["timeout_seconds"],
    )
    assert response.status_code in api_config["expected"]["invalid_login_statuses"]


def test_me_z_tokenem(api_config, token):
    response = requests.get(
        api_url(api_config, "current_user"),
        headers={"Authorization": f"Bearer {token}"},
        timeout=api_config["requests"]["timeout_seconds"],
    )
    assert response.status_code == api_config["expected"]["success_status"]
    assert response.json()["username"] == api_config["expected"]["username"]


def test_me_bez_tokena(api_config):
    response = requests.get(
        api_url(api_config, "current_user"),
        timeout=api_config["requests"]["timeout_seconds"],
    )
    assert response.status_code in api_config["expected"]["unauthorized_statuses"]


def test_me_zly_token(api_config):
    response = requests.get(
        api_url(api_config, "current_user"),
        headers={"Authorization": f"Bearer {api_config['invalid_token']}"},
        timeout=api_config["requests"]["timeout_seconds"],
    )
    assert response.status_code in api_config["expected"]["unauthorized_statuses"]
