import pytest
import requests


@pytest.fixture(scope="session")
def api_config(request):
    from webtests.api_config import load_api_config

    return load_api_config(request.config.getoption("--api-config"))


@pytest.fixture(scope="session")
def token(api_config):
    from webtests.api_config import api_url

    response = requests.post(
        api_url(api_config, "login"),
        json=api_config["credentials"],
        timeout=api_config["requests"]["timeout_seconds"],
    )
    assert response.status_code == api_config["expected"]["success_status"], (
        f"Logowanie nie powiodło się: HTTP {response.status_code}."
    )
    return response.json()["accessToken"]
