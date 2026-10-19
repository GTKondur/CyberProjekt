import json
from pathlib import Path

import pytest

from webtests.api_config import api_url, load_api_config

ROOT = Path(__file__).parent.parent.parent


def test_loads_api_suite_from_project_configuration():
    config = load_api_config(ROOT / "configs" / "api.json")

    assert config["base_url"] == "https://dummyjson.com"
    assert api_url(config, "current_user") == "https://dummyjson.com/auth/me"
    assert config["requests"]["user_list_limit"] == 5


def test_api_config_resolves_environment_variable_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("API_TEST_PASSWORD", "provided-at-runtime")
    config = json.loads((ROOT / "configs" / "api.json").read_text(encoding="utf-8"))
    config["credentials"]["password"] = "${API_TEST_PASSWORD}"
    config_path = tmp_path / "api.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    loaded = load_api_config(config_path)

    assert loaded["credentials"]["password"] == "provided-at-runtime"


def test_api_config_rejects_invalid_endpoint(tmp_path):
    config = json.loads((ROOT / "configs" / "api.json").read_text(encoding="utf-8"))
    config["endpoints"]["login"] = "https://another-site.test/login"
    config_path = tmp_path / "api.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(ValueError, match="endpoints.login"):
        load_api_config(config_path)
