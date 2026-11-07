
import pandas as pd
import pytest

from src.etl.validator import (
    validate_company_pk,
    validate_annual_pk,
    validate_fk,
    validate_balance_sheet,
    validate_opm,
    validate_positive_sales,
    validate_year_format,
    validate_ticker_format,
    validate_net_cash,
    validate_fixed_assets,
    validate_tax_rate,
    validate_dividend_payout,
    validate_annual_report_url,
    validate_eps_sign,
    validate_balance_equality,
    validate_coverage,
    collect_failures,
    deduplicate_annual_data,
    get_duplicate_rows,
)


def test_validate_company_pk_detects_duplicates():
    df = pd.DataFrame({"id": ["TCS", "INFY", "TCS"]})
    result = validate_company_pk(df)

    assert len(result) == 2
    assert set(result["rule_id"]) == {"DQ-01"}
    assert set(result["severity"]) == {"CRITICAL"}


def test_validate_company_pk_passes_unique_ids():
    df = pd.DataFrame({"id": ["TCS", "INFY"]})
    assert validate_company_pk(df).empty


def test_validate_annual_pk_detects_duplicate_company_year():
    df = pd.DataFrame({
        "company_id": ["TCS", "TCS", "INFY"],
        "year": ["2024-03", "2024-03", "2024-03"]
    })

    result = validate_annual_pk(df)

    assert len(result) == 2
    assert set(result["rule_id"]) == {"DQ-02"}


def test_validate_fk_detects_orphan_company():
    data = pd.DataFrame({"company_id": ["TCS", "UNKNOWN"]})
    companies = pd.DataFrame({"id": ["TCS", "INFY"]})

    result = validate_fk(data, companies)

    assert len(result) == 1
    assert result.iloc[0]["company_id"] == "UNKNOWN"
    assert result.iloc[0]["rule_id"] == "DQ-03"


def test_validate_balance_sheet_detects_imbalance():
    df = pd.DataFrame({
        "total_assets": [1000.0],
        "total_liabilities": [900.0]
    })

    result = validate_balance_sheet(df)

    assert len(result) == 1
    assert result.iloc[0]["rule_id"] == "DQ-04"


def test_validate_opm_detects_difference():
    df = pd.DataFrame({
        "operating_profit": [200.0],
        "sales": [1000.0],
        "opm_percentage": [25.0]
    })

    result = validate_opm(df)

    assert len(result) == 1
    assert result.iloc[0]["rule_id"] == "DQ-05"


def test_validate_positive_sales_detects_zero_and_negative():
    df = pd.DataFrame({"sales": [100.0, 0.0, -10.0]})

    result = validate_positive_sales(df)

    assert len(result) == 2
    assert result["sales"].tolist() == [0.0, -10.0]


def test_validate_year_format_detects_invalid_year():
    df = pd.DataFrame({"year": ["2024-03", "invalid", "2023"]})

    result = validate_year_format(df)

    assert len(result) == 2
    assert set(result["rule_id"]) == {"DQ-07"}


def test_validate_ticker_format_detects_invalid_tickers():
    df = pd.DataFrame({
        "company_id": ["TCS", "tcs", " TCS ", "A", "THISISWAYTOOLONG"]
    })

    result = validate_ticker_format(df)

    assert len(result) == 4
    assert set(result["rule_id"]) == {"DQ-08"}


def test_validate_net_cash_detects_difference_over_10():
    df = pd.DataFrame({
        "operating_activity": [100.0],
        "investing_activity": [-40.0],
        "financing_activity": [-20.0],
        "net_cash_flow": [100.0]
    })

    result = validate_net_cash(df)

    assert len(result) == 1
    assert result.iloc[0]["rule_id"] == "DQ-09"


def test_validate_fixed_assets_detects_negative_values():
    df = pd.DataFrame({"fixed_assets": [100.0, -5.0]})

    result = validate_fixed_assets(df)

    assert len(result) == 1
    assert result.iloc[0]["fixed_assets"] == -5.0


def test_validate_tax_rate_detects_out_of_range_values():
    df = pd.DataFrame({"tax_percentage": [20.0, -1.0, 65.0]})

    result = validate_tax_rate(df)

    assert len(result) == 2
    assert set(result["rule_id"]) == {"DQ-11"}


def test_validate_dividend_payout_detects_above_200():
    df = pd.DataFrame({"dividend_payout": [50.0, 200.0, 250.0]})

    result = validate_dividend_payout(df)

    assert len(result) == 1
    assert result.iloc[0]["rule_id"] == "DQ-12"


def test_validate_annual_report_url_uses_mocked_http(monkeypatch):
    class MockResponse:
        status_code = 200

    def fake_head(url, timeout, allow_redirects):
        return MockResponse()

    monkeypatch.setattr(
        "src.etl.validator.requests.head",
        fake_head
    )

    df = pd.DataFrame({"Annual_Report": ["https://example.com/report.pdf"]})

    assert validate_annual_report_url(df).empty


def test_validate_annual_report_url_detects_http_failure(monkeypatch):
    class MockResponse:
        status_code = 404

    monkeypatch.setattr(
        "src.etl.validator.requests.head",
        lambda *args, **kwargs: MockResponse()
    )

    df = pd.DataFrame({"Annual_Report": ["https://example.com/missing.pdf"]})

    result = validate_annual_report_url(df)

    assert len(result) == 1
    assert result.iloc[0]["rule_id"] == "DQ-13"


def test_validate_eps_sign_detects_inconsistent_eps():
    df = pd.DataFrame({
        "net_profit": [100.0, -50.0],
        "eps": [-2.0, -1.0]
    })

    result = validate_eps_sign(df)

    assert len(result) == 1
    assert result.iloc[0]["rule_id"] == "DQ-14"


def test_validate_balance_equality_detects_mismatch():
    df = pd.DataFrame({
        "total_assets": [1000.0, 500.0],
        "total_liabilities": [1000.0, 490.0]
    })

    result = validate_balance_equality(df)

    assert len(result) == 1
    assert result.iloc[0]["rule_id"] == "DQ-15"


def test_validate_coverage_detects_insufficient_history():
    pnl = pd.DataFrame({
        "company_id": ["TCS", "TCS"],
        "year": ["2023-03", "2024-03"]
    })
    bs = pd.DataFrame({
        "company_id": ["INFY"] * 5,
        "year": ["2020-03", "2021-03", "2022-03", "2023-03", "2024-03"]
    })
    cf = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2024-03"]
    })

    result = validate_coverage(pnl, bs, cf)

    assert len(result) == 2
    assert set(result["field"]) == {"profitandloss", "cashflow"}
    assert set(result["rule_id"]) == {"DQ-16"}


def test_collect_failures_combines_results():
    first = pd.DataFrame({"rule_id": ["DQ-01"]})
    second = pd.DataFrame()
    third = pd.DataFrame({"rule_id": ["DQ-02"]})

    result = collect_failures(first, second, third)

    assert len(result) == 2
    assert result["rule_id"].tolist() == ["DQ-01", "DQ-02"]


def test_collect_failures_returns_expected_empty_columns():
    result = collect_failures(pd.DataFrame())

    assert result.empty
    assert "company_id" in result.columns
    assert "rule_id" in result.columns


def test_deduplicate_annual_data_keeps_last_valid_row():
    df = pd.DataFrame({
        "company_id": ["TCS", "TCS", "INFY"],
        "year": ["2024-03", "2024-03", "PARSE_ERROR"],
        "sales": [100, 120, 50]
    })

    result = deduplicate_annual_data(df)

    tcs = result[result["company_id"] == "TCS"]

    assert len(tcs) == 1
    assert tcs.iloc[0]["sales"] == 120
    assert len(result[result["year"] == "PARSE_ERROR"]) == 1


def test_get_duplicate_rows_returns_all_duplicate_records():
    df = pd.DataFrame({
        "company_id": ["TCS", "TCS", "INFY"],
        "year": ["2024-03", "2024-03", "2024-03"]
    })

    result = get_duplicate_rows(df)

    assert len(result) == 2
    assert (result["company_id"] == "TCS").all()


def test_get_duplicate_rows_ignores_parse_errors():
    df = pd.DataFrame({
        "company_id": ["TCS", "TCS"],
        "year": ["PARSE_ERROR", "PARSE_ERROR"]
    })

    assert get_duplicate_rows(df).empty
# '@ | Set-Content tests/etl/test_validator.py -Encoding UTF8