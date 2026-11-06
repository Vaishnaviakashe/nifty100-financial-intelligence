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

page_header("📄 Annual Reports", "Find annual report records available in the project database.")
companies = load_company_list()
if companies.empty:
    st.warning("Company records are unavailable.")
    st.stop()

company_options = {"All companies": None}
company_options.update(dict(zip(
    companies["company_name"] + " (" + companies["company_id"].astype(str) + ")",
    companies["company_id"]
)))
selected_label = st.selectbox(
    "Company", list(company_options), key="reports_company"
)
reports_df = load_reports(company_options[selected_label])

if reports_df.empty:
    st.info("No annual report records were found for this selection.")
    st.stop()

reports_df["report_year"] = reports_df["report_year"].astype(str)
years = sorted(reports_df["report_year"].dropna().unique(), reverse=True)
selected_years = st.multiselect(
    "Filter by financial year", years, default=years[:3],
    key="reports_year_filter"
)
if selected_years:
    reports_df = reports_df[reports_df["report_year"].isin(selected_years)]

st.metric("Report records", len(reports_df))
st.subheader("Available Annual Reports")

for row in reports_df.itertuples(index=False):
    with st.container(border=True):
        left, right = st.columns([4, 1])
        with left:
            st.markdown(f"**{row.company_name}**")
            st.caption(f"Financial year: {row.report_year}")
        with right:
            url = str(row.report_url).strip() if pd.notna(row.report_url) else ""
            if url.startswith(("http://", "https://")):
                st.link_button("Open report ↗", url, width="stretch")
            else:
                st.caption("Link unavailable")

st.caption("Report links are displayed as stored in the source database. Broken or expired external links may need verification.")
