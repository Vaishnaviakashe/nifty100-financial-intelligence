"""Shared cached database utilities for the NIFTY 100 dashboard."""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[3]
DB_PATH = ROOT_DIR / "data" / "nifty100.db"


def _read_query(query, params=()):
    """Execute a read-only SQL query and return a DataFrame."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)


@st.cache_data(ttl=600)
def get_companies():
    """Return all companies with sector and profile information."""
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
    """Return financial ratios for a company, optionally for one year."""
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
    """Return historical profit and loss statements."""
    query = """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year DESC
    """
    return _read_query(query, (ticker.upper(),))


@st.cache_data(ttl=600)
def get_bs(ticker):
    """Return historical balance sheets."""
    query = """
        SELECT *
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year DESC
    """
    return _read_query(query, (ticker.upper(),))


@st.cache_data(ttl=600)
def get_cf(ticker):
    """Return historical cash flow statements."""
    query = """
        SELECT *
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year DESC
    """
    return _read_query(query, (ticker.upper(),))


@st.cache_data(ttl=600)
def get_sectors():
    """Return all companies grouped by their sector information."""
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
    """Return companies belonging to a selected peer group."""
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
    """Return historical market valuation data for a company."""
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
