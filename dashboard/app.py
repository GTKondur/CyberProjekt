import json
from pathlib import Path

from flask import Flask, render_template

app = Flask(__name__)

BASE = Path(__file__).parent
RESULTS = BASE.parent / "reports" / "results.json"  
SAMPLE = BASE / "sample_results.json"                


def load_results():
    path = RESULTS if RESULTS.exists() else SAMPLE
    return json.loads(path.read_text(encoding="utf-8"))["tests"]


@app.route("/")
def index():
    tests = load_results()
    total = len(tests)
    passed = sum(1 for t in tests if t["status"] == "passed")
    kpi = {
        "total": total,
        "passed_pct": round(100 * passed / total) if total else 0,
        "failed": total - passed,
        "duration": round(sum(t["duration"] for t in tests), 1),
        "violations": sum(t.get("violations", 0) for t in tests),
    }
    return render_template("index.html", kpi=kpi, tests=tests)


if __name__ == "__main__":
    app.run(debug=True)