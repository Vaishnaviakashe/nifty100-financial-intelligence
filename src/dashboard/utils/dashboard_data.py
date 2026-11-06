"""Shared database access for the NIFTY 100 dashboard pages."""

from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[3]
DB_PATH = ROOT_DIR / "data" / "nifty100.db"


@st.cache_data(ttl=600)
def query_df(sql: str, params=()):
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params)


@st.cache_data(ttl=600)
def load_universe(year=2024):
    """One latest available row per company up to the selected financial year."""
    sql = """
    WITH r AS (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY company_id ORDER BY CAST(year AS INTEGER) DESC
        ) rn
        FROM financial_ratios
        WHERE CAST(year AS INTEGER) <= ?
    ),
    m AS (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY company_id ORDER BY CAST(year AS INTEGER) DESC
        ) rn
        FROM market_cap
        WHERE CAST(year AS INTEGER) <= ?
    ),
    p AS (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY company_id ORDER BY CAST(year AS INTEGER) DESC
        ) rn
        FROM profitandloss
        WHERE CAST(year AS INTEGER) <= ?
    ),
    p5 AS (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY company_id ORDER BY CAST(year AS INTEGER) DESC
        ) rn
        FROM profitandloss
        WHERE CAST(year AS INTEGER) <= ? - 5
    )
    SELECT
        c.id AS company_id,
        c.company_name,
        s.broad_sector,
        s.sub_sector,
        r.year AS ratio_year,
        r.net_profit_margin_pct,
        r.operating_profit_margin_pct,
        r.return_on_equity_pct,
        r.return_on_capital_employed_pct,
        r.debt_to_equity,
        r.interest_coverage,
        r.free_cash_flow_cr,
        r.capex_cr,
        r.cfo_quality_score,
        r.fcf_conversion_pct,
        r.total_debt_cr,
        r.cash_from_operations_cr,
        r.earnings_per_share,
        r.book_value_per_share,
        r.dividend_payout_ratio_pct,
        m.pe_ratio,
        m.pb_ratio,
        m.ev_ebitda,
        m.dividend_yield_pct,
        m.market_cap_crore,
        m.enterprise_value_crore,
        p.year AS pl_year,
        p.sales,
        p.net_profit,
        p.operating_profit,
        p.eps,
        p.dividend_payout,
        p5.sales AS base_sales_5y,
        p5.net_profit AS base_net_profit_5y
    FROM companies c
    LEFT JOIN sectors s ON s.company_id = c.id
    LEFT JOIN r ON r.company_id = c.id AND r.rn = 1
    LEFT JOIN m ON m.company_id = c.id AND m.rn = 1
    LEFT JOIN p ON p.company_id = c.id AND p.rn = 1
    LEFT JOIN p5 ON p5.company_id = c.id AND p5.rn = 1
    ORDER BY c.company_name
    """
    return query_df(sql, (year, year, year, year))


@st.cache_data(ttl=600)
def load_peer_groups():
    return query_df("""
        SELECT DISTINCT peer_group_name
        FROM peer_groups
        WHERE peer_group_name IS NOT NULL
        ORDER BY peer_group_name
    """)


@st.cache_data(ttl=600)
def load_peer_group(group_name, year=2024):
    sql = """
    WITH r AS (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY company_id ORDER BY CAST(year AS INTEGER) DESC
        ) rn
        FROM financial_ratios WHERE CAST(year AS INTEGER) <= ?
    )
    SELECT
        pg.peer_group_name, pg.is_benchmark,
        c.id AS company_id, c.company_name,
        s.broad_sector, r.return_on_equity_pct,
        r.return_on_capital_employed_pct, r.net_profit_margin_pct,
        r.operating_profit_margin_pct, r.debt_to_equity,
        r.interest_coverage, r.free_cash_flow_cr,
        r.fcf_conversion_pct
    FROM peer_groups pg
    JOIN companies c ON c.id = pg.company_id
    LEFT JOIN sectors s ON s.company_id = c.id
    LEFT JOIN r ON r.company_id = c.id AND r.rn = 1
    WHERE pg.peer_group_name = ?
    ORDER BY pg.is_benchmark DESC, c.company_name
    """
    return query_df(sql, (year, group_name))


@st.cache_data(ttl=600)
def load_company_list():
    return query_df("""
        SELECT id AS company_id, company_name
        FROM companies ORDER BY company_name
    """)


@st.cache_data(ttl=600)
def load_company_history(company_id):
    ratios = query_df("""
        SELECT year, return_on_equity_pct, return_on_capital_employed_pct,
               net_profit_margin_pct, operating_profit_margin_pct,
               debt_to_equity, interest_coverage, free_cash_flow_cr,
               total_debt_cr, cash_from_operations_cr, capex_cr,
               fcf_conversion_pct, dividend_payout_ratio_pct
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY CAST(year AS INTEGER)
    """, (company_id,))
    pl = query_df("""
        SELECT year, sales, net_profit, operating_profit, expenses
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY CAST(year AS INTEGER)
    """, (company_id,))
    market = query_df("""
        SELECT year, pe_ratio, pb_ratio, ev_ebitda, market_cap_crore,
               dividend_yield_pct
        FROM market_cap
        WHERE company_id = ?
        ORDER BY CAST(year AS INTEGER)
    """, (company_id,))
    return ratios, pl, market


@st.cache_data(ttl=600)
def load_sector_data(year=2024):
    return load_universe(year)


@st.cache_data(ttl=600)
def load_reports(company_id=None):
    sql = """
        SELECT d.company_id, c.company_name, d.Year AS report_year,
               d.Annual_Report AS report_url
        FROM documents d
        JOIN companies c ON c.id = d.company_id
    """
    params = ()
    if company_id is not None:
        sql += " WHERE d.company_id = ?"
        params = (company_id,)
    sql += " ORDER BY c.company_name, d.Year DESC"
    return query_df(sql, params)
