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

page_header("📈 Trend Analysis", "Explore historical financial performance for individual NIFTY 100 companies.")
companies = load_company_list()
if companies.empty:
    st.warning("Company records are unavailable.")
    st.stop()
company_map = dict(zip(companies["company_name"] + " (" + companies["company_id"].astype(str) + ")", companies["company_id"]))
selected = st.selectbox("Company", list(company_map), key="trend_company")
company_id = company_map[selected]
ratios, pl, market = load_company_history(company_id)

metric_sources = {
    "Revenue (₹ Cr)": (pl, "sales"),
    "Net Profit (₹ Cr)": (pl, "net_profit"),
    "Operating Profit (₹ Cr)": (pl, "operating_profit"),
    "ROE (%)": (ratios, "return_on_equity_pct"),
    "ROCE (%)": (ratios, "return_on_capital_employed_pct"),
    "Net Profit Margin (%)": (ratios, "net_profit_margin_pct"),
    "Operating Profit Margin (%)": (ratios, "operating_profit_margin_pct"),
    "Debt / Equity": (ratios, "debt_to_equity"),
    "Free Cash Flow (₹ Cr)": (ratios, "free_cash_flow_cr"),
    "P/E": (market, "pe_ratio"),
}
selected_metrics = st.multiselect(
    "Select up to 3 metrics", list(metric_sources),
    default=["Revenue (₹ Cr)", "Net Profit (₹ Cr)"],
    max_selections=3, key="trend_metrics"
)
fig = go.Figure()
summary_rows = []
for label in selected_metrics:
    source, column = metric_sources[label]
    if source.empty or column not in source.columns:
        continue
    temp = source[["year", column]].copy()
    temp[column] = pd.to_numeric(temp[column], errors="coerce")
    temp = temp.dropna(subset=[column]).sort_values("year")
    if temp.empty:
        continue
    fig.add_trace(go.Scatter(
        x=temp["year"], y=temp[column], mode="lines+markers", name=label
    ))
    temp["YoY change (%)"] = temp[column].pct_change() * 100
    latest = temp.iloc[-1]
    summary_rows.append({
        "Metric": label, "Latest year": latest["year"],
        "Latest value": latest[column],
        "Latest YoY change (%)": latest["YoY change (%)"]
    })
if fig.data:
    fig.update_layout(title=f"Historical Trends — {selected}")
    st.plotly_chart(chart_theme(fig, 480), width="stretch")
    st.subheader("Latest Performance")
    st.dataframe(pd.DataFrame(summary_rows).round(2), width="stretch", hide_index=True)
else:
    st.info("Historical data is not available for the selected metrics.")
