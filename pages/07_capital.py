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

page_header("💰 Capital Allocation", "Understand how companies generate, deploy and distribute capital.")
year = st.selectbox("Financial Year", list(range(2024, 2018, -1)), key="capital_year")
df = load_universe(year).copy()
df = numeric(df, [
    "return_on_equity_pct", "return_on_capital_employed_pct",
    "debt_to_equity", "free_cash_flow_cr", "capex_cr",
    "dividend_payout_ratio_pct", "cash_from_operations_cr",
    "fcf_conversion_pct", "total_debt_cr"
])

def classify(row):
    roe, roce = row.get("return_on_equity_pct"), row.get("return_on_capital_employed_pct")
    debt, fcf = row.get("debt_to_equity"), row.get("free_cash_flow_cr")
    capex, payout = row.get("capex_cr"), row.get("dividend_payout_ratio_pct")
    cfo, conversion = row.get("cash_from_operations_cr"), row.get("fcf_conversion_pct")
    if pd.notna(debt) and debt <= 0.1 and pd.notna(roe) and roe >= 15:
        return "Debt-light compounders"
    if pd.notna(fcf) and fcf > 0 and pd.notna(cfo) and cfo > 0 and pd.notna(conversion) and conversion >= 70:
        return "Cash generators"
    if pd.notna(payout) and payout >= 40:
        return "Dividend distributors"
    if pd.notna(capex) and capex > 0 and pd.notna(roce) and roce >= 15:
        return "Productive reinvestors"
    if pd.notna(debt) and debt >= 2:
        return "Highly leveraged"
    if pd.notna(fcf) and fcf < 0:
        return "FCF-consuming businesses"
    if pd.notna(roe) and roe >= 15:
        return "High-return businesses"
    return "Mixed / insufficient signals"

df["capital_pattern"] = df.apply(classify, axis=1)
counts = df["capital_pattern"].value_counts().rename_axis("Pattern").reset_index(name="Companies")

a, b = st.columns(2)
a.metric("Companies classified", int(df["capital_pattern"].notna().sum()))
b.metric("Capital allocation patterns", counts["Pattern"].nunique())

st.subheader("Capital Allocation Patterns")
fig = px.treemap(
    counts, path=["Pattern"], values="Companies",
    color="Companies", color_continuous_scale=[NAVY, ORANGE]
)
fig.update_layout(title="NIFTY 100 Companies by Capital Allocation Pattern")
st.plotly_chart(chart_theme(fig, 500), width="stretch")

st.subheader("Pattern Distribution")
st.dataframe(counts, width="stretch", hide_index=True)

selected_pattern = st.selectbox(
    "Explore companies by pattern", counts["Pattern"].tolist(),
    key="capital_pattern_selector"
)
company_view = df[df["capital_pattern"] == selected_pattern]
columns = [
    "company_name", "broad_sector", "return_on_equity_pct",
    "return_on_capital_employed_pct", "debt_to_equity",
    "free_cash_flow_cr", "dividend_payout_ratio_pct"
]
columns = [c for c in columns if c in company_view.columns]
st.dataframe(
    company_view[columns].rename(columns={
        "company_name":"Company", "broad_sector":"Sector",
        "return_on_equity_pct":"ROE (%)",
        "return_on_capital_employed_pct":"ROCE (%)",
        "debt_to_equity":"Debt / Equity",
        "free_cash_flow_cr":"FCF (₹ Cr)",
        "dividend_payout_ratio_pct":"Dividend Payout (%)"
    }).round(2),
    width="stretch", hide_index=True
)
st.caption("Pattern labels are rule-based classifications from available financial indicators, not audited management-use-of-funds disclosures. Companies with incomplete data may be classified as Mixed / insufficient signals.")
