import pytest

# ---------------------------------------------------------
# ROOT AND HEALTH
# ---------------------------------------------------------


def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert "message" in data
    assert data["version"] == "1.0.0"
    assert data["health"] == "/api/v1/health"


def test_health_endpoint(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["total_tables"] >= 1
    assert "table_row_counts" in data
    assert data["uptime_seconds"] >= 0


# ---------------------------------------------------------
# COMPANY ENDPOINTS
# ---------------------------------------------------------


def test_list_companies(client):
    response = client.get("/api/v1/companies")

    assert response.status_code == 200
    data = response.json()

    assert data["total"] > 0
    assert data["count"] > 0
    assert len(data["companies"]) == data["count"]


def test_company_search(client):
    response = client.get("/api/v1/companies", params={"search": "TCS"})

    assert response.status_code == 200
    assert response.json()["count"] >= 1


def test_company_sector_filter(client, sample_sector):
    response = client.get("/api/v1/companies", params={"sector": sample_sector})

    assert response.status_code == 200

    for company in response.json()["companies"]:
        assert company["broad_sector"].lower() == sample_sector.lower()


def test_company_pagination(client):
    response = client.get("/api/v1/companies", params={"limit": 5, "offset": 0})

    assert response.status_code == 200
    assert response.json()["count"] <= 5


def test_company_profile(client, sample_ticker):
    response = client.get(f"/api/v1/companies/{sample_ticker}")

    assert response.status_code == 200
    data = response.json()

    assert data["company"]["id"].upper() == sample_ticker.upper()
    assert "sector" in data


@pytest.mark.parametrize("endpoint", ["pl", "bs", "cashflow", "ratios"])
def test_company_financial_endpoints(client, sample_ticker, endpoint):
    response = client.get(f"/api/v1/companies/{sample_ticker}/{endpoint}")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"].upper() == sample_ticker.upper()
    assert data["record_count"] == len(data["records"])
    assert isinstance(data["records"], list)


def test_company_financial_year_filter(client, sample_ticker):
    response = client.get(
        f"/api/v1/companies/{sample_ticker}/pl", params={"year": "2024-03"}
    )

    assert response.status_code == 200

    data = response.json()

    assert all(record["year"] == "2024-03" for record in data["records"])


def test_company_tearsheet_download(client, sample_ticker_with_tearsheet):
    response = client.get(f"/api/v1/companies/{sample_ticker_with_tearsheet}/tearsheet")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")


# ---------------------------------------------------------
# SCREENER
# ---------------------------------------------------------


@pytest.mark.parametrize(
    "preset",
    [
        "quality",
        "low_debt",
        "cash_generators",
        "high_returns",
        "efficient",
        "balanced",
    ],
)
def test_all_screener_presets(client, preset):
    response = client.get("/api/v1/screener", params={"preset": preset})

    assert response.status_code == 200

    data = response.json()

    assert data["preset"] == preset
    assert data["returned"] == len(data["companies"])
    assert data["total_matches"] >= data["returned"]


def test_screener_invalid_preset(client):
    response = client.get("/api/v1/screener", params={"preset": "invalid"})

    assert response.status_code == 400


def test_screener_limit(client):
    response = client.get("/api/v1/screener", params={"preset": "quality", "limit": 5})

    assert response.status_code == 200
    assert response.json()["returned"] <= 5


# ---------------------------------------------------------
# SECTORS
# ---------------------------------------------------------


def test_get_sectors(client):
    response = client.get("/api/v1/sectors")

    assert response.status_code == 200

    data = response.json()

    assert data["total_sectors"] == len(data["sectors"])
    assert data["total_sectors"] > 0


def test_get_sector_companies(client, sample_sector):
    response = client.get(f"/api/v1/sectors/{sample_sector}/companies")

    assert response.status_code == 200

    data = response.json()

    assert data["company_count"] == len(data["companies"])
    assert data["company_count"] > 0


def test_unknown_sector_returns_404(client):
    response = client.get("/api/v1/sectors/UNKNOWN_SECTOR/companies")

    assert response.status_code == 404


# ---------------------------------------------------------
# PEER ENDPOINTS
# ---------------------------------------------------------


def test_get_peer_group(client, sample_peer_group):
    response = client.get(f"/api/v1/peers/{sample_peer_group}")

    assert response.status_code == 200

    data = response.json()

    assert data["company_count"] == len(data["rankings"])
    assert data["company_count"] > 0


def test_unknown_peer_group_returns_404(client):
    response = client.get("/api/v1/peers/UNKNOWN_GROUP")

    assert response.status_code == 404


def test_compare_company_peers(client, sample_peer_company):
    response = client.get(f"/api/v1/companies/{sample_peer_company}/peers/compare")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"].upper() == sample_peer_company.upper()
    assert data["comparison_count"] == len(data["comparisons"])


# ---------------------------------------------------------
# VALUATION AND MARKET CAP
# ---------------------------------------------------------


def test_market_cap_history(client, sample_ticker):
    response = client.get(f"/api/v1/market-cap/{sample_ticker}")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"].upper() == sample_ticker.upper()
    assert data["record_count"] == len(data["history"])


def test_valuation_summary(client):
    response = client.get("/api/v1/valuation/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["year"] == 2024
    assert data["company_count"] == len(data["valuation_summary"])


def test_valuation_invalid_year(client):
    response = client.get("/api/v1/valuation/summary", params={"year": 2025})

    assert response.status_code == 422


# ---------------------------------------------------------
# PORTFOLIO
# ---------------------------------------------------------


def test_portfolio_statistics(client):
    response = client.get("/api/v1/portfolio/stats")

    assert response.status_code == 200

    data = response.json()

    assert data["metric_count"] == len(data["statistics"])
    assert data["metric_count"] > 0


# ---------------------------------------------------------
# DOCUMENTS
# ---------------------------------------------------------


def test_company_documents(client, sample_ticker):
    response = client.get(f"/api/v1/companies/{sample_ticker}/documents")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"].upper() == sample_ticker.upper()
    assert data["document_count"] == len(data["documents"])


def test_company_documents_year_filter(client, sample_ticker):
    response = client.get(
        f"/api/v1/companies/{sample_ticker}/documents", params={"year": 2024}
    )

    assert response.status_code == 200

    for document in response.json()["documents"]:
        assert str(document["year"]) == "2024"


# ---------------------------------------------------------
# ERROR HANDLING AND INPUT VALIDATION
# ---------------------------------------------------------


def test_unknown_company_returns_404(client):
    response = client.get("/api/v1/companies/UNKNOWN_TICKER")

    assert response.status_code == 404


def test_unknown_company_financial_history_returns_404(client):
    response = client.get("/api/v1/companies/UNKNOWN_TICKER/pl")

    assert response.status_code == 404


def test_unknown_company_market_cap_returns_404(client):
    response = client.get("/api/v1/market-cap/UNKNOWN_TICKER")

    assert response.status_code == 404


def test_invalid_company_limit_returns_422(client):
    response = client.get("/api/v1/companies", params={"limit": 0})

    assert response.status_code == 422


def test_invalid_company_offset_returns_422(client):
    response = client.get("/api/v1/companies", params={"offset": -1})

    assert response.status_code == 422


def test_invalid_document_year_returns_422(client):
    response = client.get("/api/v1/companies/TCS/documents", params={"year": 1999})

    assert response.status_code == 422


# ---------------------------------------------------------
# OPENAPI DOCUMENTATION
# ---------------------------------------------------------


def test_openapi_schema_contains_api_paths(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert len(paths) >= 15
    assert "/api/v1/companies" in paths
    assert "/api/v1/health" in paths
    assert "/api/v1/screener" in paths
