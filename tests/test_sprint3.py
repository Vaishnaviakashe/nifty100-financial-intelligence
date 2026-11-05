import sqlite3
import pandas as pd

from src.analytics.screener import get_screener_results
from src.analytics.peer_engine import get_peer_rankings


def create_test_db(db_path):
    """Create a small database for Sprint 3 tests."""

    conn = sqlite3.connect(db_path)

    conn.executescript("""
        CREATE TABLE companies (
            id TEXT PRIMARY KEY,
            company_name TEXT
        );

        CREATE TABLE sectors (
            company_id TEXT,
            broad_sector TEXT
        );

        CREATE TABLE financial_ratios (
            id INTEGER PRIMARY KEY,
            company_id TEXT,
            year TEXT,
            net_profit_margin_pct REAL,
            operating_profit_margin_pct REAL,
            return_on_equity_pct REAL,
            return_on_capital_employed_pct REAL,
            debt_to_equity REAL,
            interest_coverage REAL,
            asset_turnover REAL,
            free_cash_flow_cr REAL,
            cfo_quality_score REAL,
            fcf_conversion_pct REAL
        );

        CREATE TABLE peer_groups (
            peer_group_name TEXT,
            company_id TEXT,
            is_benchmark INTEGER
        );
    """)

    companies = [
        ("A", "Company A"),
        ("B", "Company B"),
        ("C", "Company C"),
    ]

    conn.executemany(
        "INSERT INTO companies VALUES (?, ?)", companies
    )

    conn.executemany(
        "INSERT INTO sectors VALUES (?, ?)",
        [(company_id, "Test Sector") for company_id, _ in companies]
    )

    ratios = [
        ("A", "2024-03", 15, 20, 25, 22, 0.3, 5, 0.9, 100, 1.2, 90),
        ("B", "2024-03", 8, 12, 10, 9, 0.8, 2, 0.5, -10, 0.5, 50),
        ("C", "2024-03", 12, 18, 18, 17, 0.4, 4, 0.8, 50, 1.1, 80),
    ]

    conn.executemany("""
        INSERT INTO financial_ratios (
            company_id, year,
            net_profit_margin_pct,
            operating_profit_margin_pct,
            return_on_equity_pct,
            return_on_capital_employed_pct,
            debt_to_equity,
            interest_coverage,
            asset_turnover,
            free_cash_flow_cr,
            cfo_quality_score,
            fcf_conversion_pct
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ratios)

    conn.executemany(
        "INSERT INTO peer_groups VALUES (?, ?, ?)",
        [
            ("Test Group", "A", 1),
            ("Test Group", "B", 0),
            ("Test Group", "C", 0),
        ]
    )

    conn.commit()
    conn.close()


def test_all_screener_presets(tmp_path):
    db_path = tmp_path / "test.db"
    create_test_db(db_path)

    expected = {
        "quality": {"A", "C"},
        "low_debt": {"A", "C"},
        "cash_generators": {"A", "C"},
        "high_returns": {"A"},
        "efficient": {"A", "C"},
        "balanced": {"A", "C"},
    }

    for preset, expected_ids in expected.items():
        result = get_screener_results(db_path, preset)

        assert set(result["company_id"]) == expected_ids


def test_invalid_screener_preset(tmp_path):
    db_path = tmp_path / "test.db"
    create_test_db(db_path)

    try:
        get_screener_results(db_path, "invalid")
        assert False, "Expected ValueError"
    except ValueError:
        assert True


def test_peer_rankings(tmp_path):
    db_path = tmp_path / "test.db"
    create_test_db(db_path)

    result = get_peer_rankings(db_path)

    assert len(result) == 3
    assert result["peer_group_name"].nunique() == 1
    assert "overall_percentile" in result.columns
    assert "overall_rank" in result.columns

    top_company = result.loc[
        result["overall_rank"] == 1, "company_id"
    ].tolist()

    assert top_company == ["A"]


def test_peer_percentiles_are_valid(tmp_path):
    db_path = tmp_path / "test.db"
    create_test_db(db_path)

    result = get_peer_rankings(db_path)

    assert result["overall_percentile"].between(0, 100).all()
    assert result["overall_rank"].notna().all()