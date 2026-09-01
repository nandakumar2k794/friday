from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_codesystem_is_fhir_shape():
    response = client.get("/CodeSystem/namaste")
    assert response.status_code == 200
    body = response.json()
    assert body["resourceType"] == "CodeSystem"
    assert body["url"].startswith("https://")


def test_single_conceptmap_is_fhir_shape():
    response = client.get("/ConceptMap/SR11")
    assert response.status_code == 200
    body = response.json()
    assert body["resourceType"] == "ConceptMap"
    assert body["group"][0]["element"][0]["target"][0]["equivalence"] in {"equivalent", "related"}


def test_condition_has_dual_coding():
    response = client.post("/Condition", json={"patient_id": "Patient/test-001", "namaste_code": "SR11"})
    assert response.status_code == 201
    body = response.json()
    assert body["resourceType"] == "Condition"
    assert len(body["code"]["coding"]) >= 2
    assert body["code"]["coding"][0]["code"] == "SR11"
