"""Morning demo proof: run `pytest -s tests/test_search_coverage.py`."""
import csv
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "namaste_icd11_curated.csv"
client = TestClient(app)


def search_codes(payload: dict) -> set[str]:
    return {item["namaste_code"] for item in payload.get("results", [])}


def test_all_50_curated_terms_are_searchable():
    with FIXTURE.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 50, "Curated fixture must remain exactly 50 terms for the demo claim."

    print("\nNAMASTE SEARCH COVERAGE")
    print("CODE  | RESULT | TITLE")
    print("------|--------|------------------------------")
    failures = []
    for row in rows:
        response = client.get("/search", params={"q": row["namaste_code"]})
        payload = response.json()
        match = next((item for item in payload.get("results", []) if item["namaste_code"] == row["namaste_code"]), None)
        passed = (response.status_code == 200 and match is not None and
                  match["icd11_tm2_code"] == row["icd11_tm2_code"] and
                  match["icd11_tm2_title"] == row["icd11_tm2_title"] and
                  match["equivalence"] == row["equivalence"])
        print(f"{row['namaste_code']:<5} | {'PASS' if passed else 'FAIL':<6} | {row['namaste_title_en']}")
        if not passed:
            failures.append(row["namaste_code"])
    print(f"\n{len(rows) - len(failures)}/{len(rows)} pass")
    assert not failures, f"Search failed for: {', '.join(failures)}"
