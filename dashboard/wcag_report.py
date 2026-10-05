import html
import json
from pathlib import Path

REPORTS = Path(__file__).parent.parent / "reports"
OUT = REPORTS / "wcag_report.html"
COLORS = {"critical": "#b71c1c", "serious": "#e65100",
          "moderate": "#f9a825", "minor": "#546e7a"}


def build():
    sections = []
    for f in sorted(REPORTS.glob("wcag_*.json")):
        page = f.stem.removeprefix("wcag_")
        violations = json.loads(f.read_text(encoding="utf-8"))
        rows = ""
        for v in violations:
            color = COLORS.get(v["impact"], "#546e7a")
            nodes = "".join(
                f"<li><code>{html.escape(n['html'][:150])}</code></li>"
                for n in v["nodes"][:3])
            rows += (
                f"<tr><td style='color:{color};font-weight:bold'>{html.escape(str(v['impact']))}</td>"
                f"<td>{html.escape(v['id'])}</td>"
                f"<td>{html.escape(v['help'])}<br><a href='{html.escape(v['helpUrl'])}'>Opis reguły</a></td>"
                f"<td>{len(v['nodes'])}<ul>{nodes}</ul></td></tr>")
        body = (f"<table><tr><th>Waga</th><th>Reguła</th><th>Problem</th><th>Elementy</th></tr>{rows}</table>"
                if violations else "<p class='ok'>Brak naruszeń.</p>")
        sections.append(f"<h2>{html.escape(page)} (naruszeń: {len(violations)})</h2>{body}")

    page_html = f"""<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><title>Raport dostępności WCAG</title>
<style>
 body {{ font-family: Arial, sans-serif; margin: 2rem; background: #f4f6f8; color: #222; }}
 table {{ width: 100%; border-collapse: collapse; background: #fff; margin-bottom: 2rem; }}
 th, td {{ padding: .6rem; text-align: left; border-bottom: 1px solid #ddd; vertical-align: top; }}
 code {{ font-size: .85rem; }} .ok {{ color: #1a7f37; font-weight: bold; }}
</style></head><body>
<h1>Raport dostępności WCAG</h1>
<p>Zakres: WCAG 2.0 i 2.1, poziomy A i AA (axe-core).</p>
{''.join(sections) or '<p>Brak danych. Uruchom najpierw testy.</p>'}
</body></html>"""
    OUT.write_text(page_html, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    print("Zapisano:", build())