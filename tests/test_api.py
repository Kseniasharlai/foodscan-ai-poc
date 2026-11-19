from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_analyze_known_barcode():
    response = client.get("/api/analyze/3017620422003")
    assert response.status_code == 200
    data = response.json()
    assert data["product"]["barcode"] == "3017620422003"
    assert 0 <= data["evaluation"]["health_score"] <= 100
    assert len(data["evaluation"]["cons"]) > 0


def test_analyze_custom_ingredients():
    payload = {
        "product_name": "Вівсяні пластівці цільнозернові",
        "ingredients_text": "Пластівці вівсяні плющені з цільного зерна 100%",
        "sugars_g": 1.2,
        "salt_g": 0.02,
        "saturated_fats_g": 1.1,
        "proteins_g": 12.5,
    }
    response = client.post("/api/analyze-custom", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["evaluation"]["health_score"] >= 70
