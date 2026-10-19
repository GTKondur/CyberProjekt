import json
import subprocess
import sys
import tempfile
import threading
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BASE = Path(__file__).parent
ROOT = BASE.parent
CONFIGS = ROOT / "configs"
RUN_LOCK = threading.Lock()
RUN_STATE = {
    "id": None,
    "running": False,
    "returncode": None,
    "logs": "",
    "error": None,
    "tests": [],
}


def available_configs():
    configs = []
    for path in CONFIGS.glob("*.json"):
        config = json.loads(path.read_text(encoding="utf-8"))
        if config.get("kind", "browser") == "browser":
            configs.append(path.stem)
    return sorted(configs)


def consume_output(process, run_id, results_file):
    try:
        for line in process.stdout:
            with RUN_LOCK:
                if RUN_STATE["id"] == run_id:
                    RUN_STATE["logs"] += line
        returncode = process.wait()
        tests = json.loads(results_file.read_text(encoding="utf-8"))["tests"]
        if not isinstance(tests, list):
            raise ValueError("Pytest report 'tests' field must be a list.")
        with RUN_LOCK:
            if RUN_STATE["id"] == run_id:
                RUN_STATE["running"] = False
                RUN_STATE["returncode"] = returncode
                RUN_STATE["tests"] = tests
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        with RUN_LOCK:
            if RUN_STATE["id"] == run_id:
                RUN_STATE["running"] = False
                RUN_STATE["error"] = f"Could not load this run's pytest report: {exc}"
    finally:
        results_file.unlink(missing_ok=True)


@app.route("/")
def index():
    with RUN_LOCK:
        tests = list(RUN_STATE["tests"])
    total = len(tests)
    passed = sum(1 for t in tests if t["status"] == "passed")
    kpi = {
        "total": total,
        "passed_pct": round(100 * passed / total) if total else 0,
        "failed": total - passed,
        "duration": round(sum(t["duration"] for t in tests), 1),
        "violations": sum(t.get("violations", 0) for t in tests),
    }
    return render_template(
        "index.html",
        kpi=kpi,
        tests=tests,
        configs=available_configs(),
    )


@app.post("/run")
def start_run():
    target = request.form.get("target", "")
    command = [sys.executable, "-m", "pytest", "-q"]
    if target == "api":
        command.extend(
            [
                "tests/api",
                "--api-config",
                str(CONFIGS / "api.json"),
            ]
        )
    elif target == "accessibility":
        command.extend(
            [
                "tests/accessibility",
                "--wcag-config",
                str(CONFIGS / "accessibility.json"),
            ]
        )
    elif target.startswith("config:") and target.removeprefix("config:") in available_configs():
        config_path = CONFIGS / f"{target.removeprefix('config:')}.json"
        command.extend(
            [
                "tests/config_driven/test_configured.py",
                "--webtest-config",
                str(config_path),
            ]
        )
        base_url = request.form.get("base_url", "").strip()
        if base_url:
            command.extend(["--webtest-url", base_url])
    else:
        return jsonify(error="Choose a test suite or configuration from the list."), 400
    with RUN_LOCK:
        if RUN_STATE["running"]:
            return jsonify(error="A test run is already in progress."), 409
        run_id = uuid.uuid4().hex
        results_file = Path(tempfile.gettempdir()) / f"cyberprojekt-dashboard-{run_id}.json"
        command.extend(["--results-file", str(results_file), "-s"])
        RUN_STATE.update(
            id=run_id,
            running=True,
            returncode=None,
            logs="",
            error=None,
            tests=[],
        )

    try:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except OSError as exc:
        with RUN_LOCK:
            RUN_STATE.update(running=False, error=str(exc))
        return jsonify(error=f"Could not start pytest: {exc}"), 500

    thread = threading.Thread(
        target=consume_output,
        args=(process, run_id, results_file),
        daemon=True,
    )
    thread.start()
    return jsonify(run_id=run_id), 202


@app.get("/run/status")
def run_status():
    with RUN_LOCK:
        return jsonify(RUN_STATE.copy())


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=False)