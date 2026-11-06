
"""Shared cached database utilities for the NIFTY 100 dashboard."""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[3]
DB_PATH = ROOT_DIR / "data" / "nifty100.db"


@st.cache_data(ttl=600)
def _read_query(query, params=()):
    """Execute a SQL query and return results as a DataFrame."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)


@st.cache_data(ttl=600)
def get_companies():
    query = """
        SELECT
            c.id AS company_id,
            c.company_name,
            c.company_logo,
            c.chart_link,
            c.about_company,
            c.website,
            c.nse_profile,
            c.bse_profile,
            c.face_value,
            c.book_value,
            c.roce_percentage,
            c.roe_percentage,
            s.broad_sector,
            s.sub_sector,
            s.index_weight_pct,
            s.market_cap_category
        FROM companies c
        LEFT JOIN sectors s ON s.company_id = c.id
        ORDER BY c.company_name
    """
    return _read_query(query)


@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    query = """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
    """
    params = [ticker.upper()]

    if year is not None:
        query += " AND year = ?"
        params.append(str(year))

    query += " ORDER BY year DESC"
    return _read_query(query, tuple(params))


@st.cache_data(ttl=600)
def get_pl(ticker):
    query = """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year DESC
    """
    return _read_query(query, (ticker.upper(),))


@st.cache_data(ttl=600)
def get_bs(ticker):
    query = """
        SELECT *
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year DESC
    """
    return _read_query(query, (ticker.upper(),))


@st.cache_data(ttl=600)
def get_cf(ticker):
    query = """
        SELECT *
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year DESC
    """
    return _read_query(query, (ticker.upper(),))


@st.cache_data(ttl=600)
def get_sectors():
    query = """
        SELECT
            s.*,
            c.company_name
        FROM sectors s
        LEFT JOIN companies c ON c.id = s.company_id
        ORDER BY s.broad_sector, c.company_name
    """
    return _read_query(query)


@st.cache_data(ttl=600)
def get_peers(group_name):
    query = """
        SELECT
            pg.peer_group_name,
            pg.company_id,
            pg.is_benchmark,
            c.company_name,
            s.broad_sector,
            s.sub_sector
        FROM peer_groups pg
        LEFT JOIN companies c ON c.id = pg.company_id
        LEFT JOIN sectors s ON s.company_id = pg.company_id
        WHERE pg.peer_group_name = ?
        ORDER BY pg.is_benchmark DESC, c.company_name
    """
    return _read_query(query, (group_name,))


@st.cache_data(ttl=600)
def get_valuation(ticker):
    query = """
        SELECT
            m.*,
            c.company_name,
            s.broad_sector,
            s.sub_sector
        FROM market_cap m
        LEFT JOIN companies c ON c.id = m.company_id
        LEFT JOIN sectors s ON s.company_id = m.company_id
        WHERE m.company_id = ?
        ORDER BY m.year DESC
    """
    return _read_query(query, (ticker.upper(),))


@st.cache_data(ttl=600)
def get_home_data(year):
    """Get company financial data available up to the selected year."""

    query = """
        WITH ranked_ratios AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY company_id
                    ORDER BY CAST(year AS INTEGER) DESC
                ) AS rn
            FROM financial_ratios
            WHERE CAST(year AS INTEGER) <= ?
        ),
        ranked_market AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY company_id
                    ORDER BY CAST(year AS INTEGER) DESC
                ) AS rn
            FROM market_cap
            WHERE CAST(year AS INTEGER) <= ?
        ),
        ranked_current_pl AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY company_id
                    ORDER BY CAST(year AS INTEGER) DESC
                ) AS rn
            FROM profitandloss
            WHERE CAST(year AS INTEGER) <= ?
        ),
        ranked_base_pl AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY company_id
                    ORDER BY CAST(year AS INTEGER) DESC
                ) AS rn
            FROM profitandloss
            WHERE CAST(year AS INTEGER) <= ?
        )
        SELECT
            c.id AS company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            r.year AS ratio_year,
            r.return_on_equity_pct,
            r.return_on_capital_employed_pct,
            r.net_profit_margin_pct,
            r.debt_to_equity,
            r.interest_coverage,
            r.free_cash_flow_cr,
            r.total_debt_cr,
            m.pe_ratio,
            m.pb_ratio,
            m.ev_ebitda,
            m.market_cap_crore,
            current_pl.sales AS current_sales,
            base_pl.sales AS base_sales
        FROM companies c
        LEFT JOIN sectors s ON s.company_id = c.id
        LEFT JOIN ranked_ratios r
            ON r.company_id = c.id AND r.rn = 1
        LEFT JOIN ranked_market m
            ON m.company_id = c.id AND m.rn = 1
        LEFT JOIN ranked_current_pl current_pl
            ON current_pl.company_id = c.id AND current_pl.rn = 1
        LEFT JOIN ranked_base_pl base_pl
            ON base_pl.company_id = c.id AND base_pl.rn = 1
        ORDER BY c.company_name
    """

    selected_year = int(year)

    return _read_query(
        query,
        (
            selected_year,
            selected_year,
            selected_year,
            selected_year - 5,
        ),
    )
