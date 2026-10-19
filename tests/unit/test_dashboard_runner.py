import time
import json
from pathlib import Path

import dashboard.app as dashboard_app


def write_run_report(command):
    results_file = Path(command[command.index("--results-file") + 1])
    results_file.write_text(
        json.dumps(
            {
                "tests": [
                    {
                        "name": "current run",
                        "category": "API",
                        "status": "passed",
                        "duration": 0.1,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def test_dashboard_starts_pytest_and_exposes_live_output(monkeypatch):
    class FakeProcess:
        stdout = iter(["configured test output\n"])

        def wait(self):
            return 0

    commands = []

    def fake_popen(command, **kwargs):
        commands.append((command, kwargs))
        write_run_report(command)
        return FakeProcess()

    monkeypatch.setattr(dashboard_app.subprocess, "Popen", fake_popen)
    monkeypatch.setitem(dashboard_app.RUN_STATE, "running", False)
    monkeypatch.setitem(dashboard_app.RUN_STATE, "tests", [])

    response = dashboard_app.app.test_client().post(
        "/run",
        data={"target": "config:saucedemo", "base_url": "https://example.test"},
    )

    assert response.status_code == 202
    assert "tests/config_driven/test_configured.py" in commands[0][0]
    assert "--webtest-url" in commands[0][0]
    deadline = time.monotonic() + 1
    while dashboard_app.RUN_STATE["running"] and time.monotonic() < deadline:
        time.sleep(0.01)

    status = dashboard_app.app.test_client().get("/run/status").json
    assert status["running"] is False
    assert status["returncode"] == 0
    assert "configured test output" in status["logs"]
    assert status["tests"][0]["name"] == "current run"


def test_dashboard_can_launch_api_suite(monkeypatch):
    commands = []

    class FakeProcess:
        stdout = iter([])

        def wait(self):
            return 0

    def fake_popen(command, **kwargs):
        commands.append(command)
        write_run_report(command)
        return FakeProcess()

    monkeypatch.setattr(dashboard_app.subprocess, "Popen", fake_popen)
    monkeypatch.setitem(dashboard_app.RUN_STATE, "running", False)
    monkeypatch.setitem(dashboard_app.RUN_STATE, "tests", [])

    response = dashboard_app.app.test_client().post(
        "/run",
        data={"target": "api"},
    )

    assert response.status_code == 202
    assert "tests/api" in commands[0]
    assert "--api-config" in commands[0]
    assert any("api.json" in argument for argument in commands[0])


def test_dashboard_can_launch_accessibility_suite(monkeypatch):
    commands = []

    class FakeProcess:
        stdout = iter([])

        def wait(self):
            return 0

    def fake_popen(command, **kwargs):
        commands.append(command)
        write_run_report(command)
        return FakeProcess()

    monkeypatch.setattr(dashboard_app.subprocess, "Popen", fake_popen)
    monkeypatch.setitem(dashboard_app.RUN_STATE, "running", False)
    monkeypatch.setitem(dashboard_app.RUN_STATE, "tests", [])

    response = dashboard_app.app.test_client().post(
        "/run",
        data={"target": "accessibility"},
    )

    assert response.status_code == 202
    assert "tests/accessibility" in commands[0]
    assert "--wcag-config" in commands[0]
    assert any("accessibility.json" in argument for argument in commands[0])


def test_dashboard_starts_with_no_previous_results(monkeypatch):
    monkeypatch.setitem(dashboard_app.RUN_STATE, "tests", [])

    response = dashboard_app.app.test_client().get("/")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "<b>0</b>Liczba testów" in page
    assert "current run" not in page


def test_accessibility_config_is_not_listed_as_browser_config():
    assert dashboard_app.available_configs() == ["saucedemo"]
