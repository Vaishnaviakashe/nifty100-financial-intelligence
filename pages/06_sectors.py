import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.dashboard.utils.dashboard_data import (
    load_universe, load_peer_groups, load_peer_group,
    load_company_list, load_company_history, load_sector_data,
    load_reports, query_df
)

NAVY = "#123B69"
ORANGE = "#F28C28"
TEXT = "#18324F"
MUTED = "#718096"
PALE = "#F5F7FA"
FONT = "Times New Roman"

def page_header(title, subtitle):
    st.markdown(
        f"<h1 style='font-family:{FONT},serif;color:{NAVY};'>{title}</h1>"
        f"<p style='font-family:{FONT},serif;color:{MUTED};font-size:17px;'>{subtitle}</p>",
        unsafe_allow_html=True,
    )

def chart_theme(fig, height=420):
    fig.update_layout(
        height=height, paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family=FONT, color=TEXT, size=13),
        title_font=dict(family=FONT, color=NAVY, size=19),
        margin=dict(l=25, r=25, t=65, b=30),
    )
    fig.update_xaxes(showgrid=False, linecolor="#DCE4ED")
    fig.update_yaxes(gridcolor="#E9EEF4", zerolinecolor="#DCE4ED")
    return fig

def numeric(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

page_header("🏭 Sector Analysis", "Compare financial strength and valuation across NIFTY 100 sectors.")
year = st.selectbox("Financial Year", list(range(2024, 2018, -1)), key="sector_year")
df = load_sector_data(year).copy()
numeric_cols = [
    "return_on_equity_pct", "return_on_capital_employed_pct",
    "net_profit_margin_pct", "debt_to_equity", "sales", "market_cap_crore",
    "pe_ratio", "free_cash_flow_cr"
]
df = numeric(df, numeric_cols)
df = df.dropna(subset=["broad_sector"])
if df.empty:
    st.warning("Sector-level data is unavailable for this year.")
    st.stop()

summary = df.groupby("broad_sector").agg(
    Companies=("company_id", "nunique"),
    Median_ROE=("return_on_equity_pct", "median"),
    Median_ROCE=("return_on_capital_employed_pct", "median"),
    Median_PE=("pe_ratio", "median"),
    Median_DE=("debt_to_equity", "median"),
    Total_Market_Cap=("market_cap_crore", "sum"),
).reset_index()

st.subheader("Sector Overview")
c1, c2, c3 = st.columns(3)
c1.metric("Sectors Covered", summary["broad_sector"].nunique())
c2.metric("Companies Covered", df["company_id"].nunique())
c3.metric("Largest Sector", summary.sort_values("Total_Market_Cap", ascending=False).iloc[0]["broad_sector"])

st.subheader("Sector Financial Strength")
fig = px.bar(
    summary.sort_values("Median_ROE", ascending=False),
    x="broad_sector", y="Median_ROE", color="Median_ROE",
    color_continuous_scale=[NAVY, ORANGE],
    labels={"broad_sector":"Sector", "Median_ROE":"Median ROE (%)"}
)
fig.update_layout(title="Median ROE by Sector")
st.plotly_chart(chart_theme(fig, 430), width="stretch")

st.subheader("Company Revenue vs Return on Equity")
bubble = df.dropna(subset=["sales", "return_on_equity_pct"]).copy()
if not bubble.empty:
    bubble["bubble_size"] = pd.to_numeric(bubble["market_cap_crore"], errors="coerce").fillna(1).clip(lower=1)
    fig = px.scatter(
        bubble, x="sales", y="return_on_equity_pct",
        size="bubble_size", color="broad_sector",
        hover_name="company_name",
        labels={"sales":"Revenue (₹ Cr)", "return_on_equity_pct":"ROE (%)", "broad_sector":"Sector"},
        size_max=35
    )
    fig.update_layout(title="Revenue vs ROE — Bubble Size Represents Market Capitalisation")
    st.plotly_chart(chart_theme(fig, 500), width="stretch")
else:
    st.info("Revenue and ROE data are not sufficiently available for the bubble chart.")

st.subheader("Sector Benchmark Table")
summary = summary.rename(columns={
    "broad_sector":"Sector", "Median_ROE":"Median ROE (%)",
    "Median_ROCE":"Median ROCE (%)", "Median_PE":"Median P/E",
    "Median_DE":"Median Debt / Equity", "Total_Market_Cap":"Total Market Cap (₹ Cr)"
})
st.dataframe(summary.round(2), width="stretch", hide_index=True)
