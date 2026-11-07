import pandas as pd

from src.etl.loader import load_excel


def test_load_core_excel_uses_header_one(monkeypatch, tmp_path):
    captured = {}

    def fake_read_excel(path, header):
        captured["header"] = header
        return pd.DataFrame({"company_id": ["tcs"], "year": ["Mar-23"]})

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)

    result = load_excel(tmp_path / "companies.xlsx", core=True)

    assert captured["header"] == 1
    assert result.loc[0, "company_id"] == "TCS"
    assert result.loc[0, "year"] == "2023-03"


def test_load_non_core_excel_uses_header_zero(monkeypatch, tmp_path):
    captured = {}

    def fake_read_excel(path, header):
        captured["header"] = header
        return pd.DataFrame({"company_id": ["infy"]})

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)

    result = load_excel(tmp_path / "other.xlsx", core=False)

    assert captured["header"] == 0
    assert result.loc[0, "company_id"] == "INFY"


def test_load_excel_without_normalizable_columns(monkeypatch, tmp_path):
    def fake_read_excel(path, header):
        return pd.DataFrame({"sales": [100], "profit": [20]})

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)

    result = load_excel(tmp_path / "financial.xlsx")

    assert list(result.columns) == ["sales", "profit"]
    assert result.loc[0, "sales"] == 100


def test_load_excel_normalizes_invalid_values(monkeypatch, tmp_path):
    def fake_read_excel(path, header):
        return pd.DataFrame({"company_id": [None], "year": ["invalid"]})

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)

    result = load_excel(tmp_path / "financial.xlsx")

    assert result.loc[0, "company_id"] == "PARSE_ERROR"
    assert result.loc[0, "year"] == "PARSE_ERROR"
    # '@ | Set-Content tests/etl/test_loader.py -Encoding UTF8
