from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_pros_cons_endpoint_returns_valid_response():
    response = client.get("/api/v1/companies/TCS/pros-cons")

    assert response.status_code == 200
    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["total_signals"] == data["pros_count"] + data["cons_count"]
    assert isinstance(data["pros"], list)
    assert isinstance(data["cons"], list)


def test_pros_cons_filter_pro():
    response = client.get("/api/v1/companies/TCS/pros-cons?type=pro")

    assert response.status_code == 200
    data = response.json()
    assert data["cons_count"] == 0
    assert all(item["type"] == "pro" for item in data["pros"])


def test_pros_cons_filter_con():
    response = client.get("/api/v1/companies/TCS/pros-cons?type=con")

    assert response.status_code == 200
    data = response.json()
    assert data["pros_count"] == 0
    assert all(item["type"] == "con" for item in data["cons"])


def test_pros_cons_invalid_filter():
    response = client.get("/api/v1/companies/TCS/pros-cons?type=invalid")
    assert response.status_code == 400


def test_pros_cons_unknown_company():
    response = client.get("/api/v1/companies/UNKNOWN_TICKER/pros-cons")
    assert response.status_code == 404
