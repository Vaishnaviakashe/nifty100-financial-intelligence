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

page_header("⚖️ Peer Comparison", "Benchmark companies against their assigned peer group.")
groups_df = load_peer_groups()
if groups_df.empty:
    st.warning("No peer groups are available in the database.")
    st.stop()
group_names = groups_df["peer_group_name"].dropna().tolist()
c1, c2 = st.columns([3, 1])
with c1:
    group = st.selectbox("Peer group", group_names, key="peer_group_selector")
with c2:
    year = st.selectbox("Financial Year", list(range(2024, 2018, -1)), key="peer_year")
data = load_peer_group(group, year).copy()
metric_cols = [
    "return_on_equity_pct", "return_on_capital_employed_pct",
    "net_profit_margin_pct", "operating_profit_margin_pct",
    "debt_to_equity", "interest_coverage", "free_cash_flow_cr",
    "fcf_conversion_pct"
]
data = numeric(data, metric_cols)
if data.empty:
    st.info("No companies are mapped to this peer group.")
    st.stop()

st.metric("Companies in peer group", data["company_id"].nunique())
st.subheader("Peer Group Members")
st.dataframe(
    data[["company_name", "broad_sector", "is_benchmark"]].rename(columns={
        "company_name":"Company", "broad_sector":"Sector", "is_benchmark":"Benchmark"
    }),
    width="stretch", hide_index=True
)

available = [c for c in metric_cols if data[c].notna().any()]
labels = {
    "return_on_equity_pct":"ROE (%)", "return_on_capital_employed_pct":"ROCE (%)",
    "net_profit_margin_pct":"NPM (%)", "operating_profit_margin_pct":"OPM (%)",
    "debt_to_equity":"Debt / Equity", "interest_coverage":"Interest Coverage",
    "free_cash_flow_cr":"FCF (₹ Cr)", "fcf_conversion_pct":"FCF Conversion (%)"
}
if available:
    chosen = st.multiselect(
        "Metrics to compare (select up to 8)", available, default=available[:5],
        format_func=lambda x: labels[x], max_selections=8, key="peer_metrics"
    )
    if chosen:
        comparison = data[["company_name"] + chosen].set_index("company_name")
        fig = go.Figure()
        for company_name, row in comparison.iterrows():
            fig.add_trace(go.Scatterpolar(
                r=[row[c] for c in chosen], theta=[labels[c] for c in chosen],
                fill="toself", name=company_name
            ))
        fig.update_layout(
            title="Peer Financial Profile — Radar Comparison",
            polar=dict(radialaxis=dict(visible=True)),
            showlegend=True
        )
        st.plotly_chart(chart_theme(fig, 500), width="stretch")

        st.subheader("Peer Benchmark Statistics")
        stats = data[chosen].agg(["median", "mean", "min", "max"]).T.reset_index()
        stats.columns = ["Metric", "Median", "Mean", "Minimum", "Maximum"]
        stats["Metric"] = stats["Metric"].map(labels)
        st.dataframe(stats.round(2), width="stretch", hide_index=True)

        st.subheader("Percentile Rankings")
        percentile = data[["company_name"] + chosen].copy()
        for col in chosen:
            ascending = col == "debt_to_equity"
            percentile[col] = percentile[col].rank(pct=True, ascending=ascending) * 100
        percentile = percentile.rename(columns={"company_name":"Company", **{c:labels[c]+" percentile" for c in chosen}})
        st.dataframe(percentile.round(1), width="stretch", hide_index=True)
else:
    st.info("No comparable financial metrics are available for this peer group.")
