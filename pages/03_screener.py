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

page_header("🔎 Financial Screener", "Filter NIFTY 100 companies using fundamental, valuation and dividend metrics.")
year = st.selectbox("Financial Year", list(range(2024, 2018, -1)), key="screener_year")
df = load_universe(year).copy()

metrics = {
    "return_on_equity_pct": "ROE (%)",
    "debt_to_equity": "Debt / Equity",
    "free_cash_flow_cr": "Free Cash Flow (₹ Cr)",
    "pe_ratio": "P/E",
    "pb_ratio": "P/B",
    "dividend_yield_pct": "Dividend Yield (%)",
    "interest_coverage": "Interest Coverage",
    "operating_profit_margin_pct": "OPM (%)",
    "revenue_cagr_5yr": "Revenue CAGR (5Y) (%)",
    "pat_cagr_5yr": "PAT CAGR (5Y) (%)",
}
df = numeric(df, [
    "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
    "pe_ratio", "pb_ratio", "dividend_yield_pct", "interest_coverage",
    "operating_profit_margin_pct", "sales", "net_profit",
    "base_sales_5y", "base_net_profit_5y"
])
df["revenue_cagr_5yr"] = np.nan
df["pat_cagr_5yr"] = np.nan
valid_sales = (df["sales"] > 0) & (df["base_sales_5y"] > 0)
valid_pat = (df["net_profit"] > 0) & (df["base_net_profit_5y"] > 0)
df.loc[valid_sales, "revenue_cagr_5yr"] = (
    (df.loc[valid_sales, "sales"] / df.loc[valid_sales, "base_sales_5y"]) ** (1 / 5) - 1
) * 100
df.loc[valid_pat, "pat_cagr_5yr"] = (
    (df.loc[valid_pat, "net_profit"] / df.loc[valid_pat, "base_net_profit_5y"]) ** (1 / 5) - 1
) * 100

presets = {
    "Custom": {},
    "Quality": {"return_on_equity_pct": (15, None), "debt_to_equity": (None, 1), "interest_coverage": (3, None)},
    "Value": {"pe_ratio": (None, 25), "pb_ratio": (None, 4), "debt_to_equity": (None, 1.5)},
    "Growth": {"revenue_cagr_5yr": (10, None), "pat_cagr_5yr": (10, None)},
    "Dividend": {"dividend_yield_pct": (2, None)},
    "Debt-Free": {"debt_to_equity": (None, 0.1)},
    "Turnaround": {"free_cash_flow_cr": (0, None), "operating_profit_margin_pct": (5, None)},
}
preset = st.selectbox("Screening preset", list(presets), key="screener_preset")
filters = presets[preset].copy()

with st.expander("⚙️ Customize financial filters", expanded=True):
    cols = st.columns(2)
    controls = [
        ("ROE minimum (%)", "return_on_equity_pct", "min", -100.0, 100.0, 1.0),
        ("Debt / Equity maximum", "debt_to_equity", "max", 0.0, 10.0, 0.1),
        ("FCF minimum (₹ Cr)", "free_cash_flow_cr", "min", -50000.0, 50000.0, 100.0),
        ("P/E maximum", "pe_ratio", "max", 0.0, 200.0, 1.0),
        ("P/B maximum", "pb_ratio", "max", 0.0, 50.0, 0.5),
        ("Dividend yield minimum (%)", "dividend_yield_pct", "min", 0.0, 20.0, 0.5),
        ("Interest coverage minimum", "interest_coverage", "min", 0.0, 100.0, 1.0),
        ("OPM minimum (%)", "operating_profit_margin_pct", "min", -100.0, 100.0, 1.0),
        ("Revenue CAGR minimum (%)", "revenue_cagr_5yr", "min", -100.0, 100.0, 1.0),
        ("PAT CAGR minimum (%)", "pat_cagr_5yr", "min", -100.0, 100.0, 1.0),
    ]
    for i, (label, col, mode, lo, hi, step) in enumerate(controls):
        default = filters.get(col, (None, None))[0 if mode == "min" else 1]
        with cols[i % 2]:
            value = st.number_input(
                label, min_value=lo, max_value=hi, value=float(default if default is not None else (lo if mode == "min" else hi)),
                step=step, key=f"screener_{col}_{mode}"
            )
        if mode == "min":
            filters[col] = (value, filters.get(col, (None, None))[1])
        else:
            filters[col] = (filters.get(col, (None, None))[0], value)

result = df.copy()
for col, (minimum, maximum) in filters.items():
    if minimum is not None:
        result = result[result[col].notna() & (result[col] >= minimum)]
    if maximum is not None:
        result = result[result[col].notna() & (result[col] <= maximum)]

st.divider()
a, b = st.columns([1, 3])
a.metric("Matching companies", len(result))
b.caption(f"Showing results for FY {year}. Missing values are excluded when a filter is applied.")
show_cols = ["company_id", "company_name", "broad_sector", "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr", "pe_ratio", "pb_ratio", "dividend_yield_pct", "interest_coverage"]
show_cols = [c for c in show_cols if c in result.columns]
display = result[show_cols].rename(columns={
    "company_id":"Company ID", "company_name":"Company", "broad_sector":"Sector",
    "return_on_equity_pct":"ROE (%)", "debt_to_equity":"Debt / Equity",
    "free_cash_flow_cr":"FCF (₹ Cr)", "pe_ratio":"P/E", "pb_ratio":"P/B",
    "dividend_yield_pct":"Dividend Yield (%)", "interest_coverage":"Interest Coverage"
})
st.dataframe(display.round(2), width="stretch", hide_index=True)
st.download_button(
    "⬇️ Download Screener Results (CSV)",
    data=display.to_csv(index=False).encode("utf-8"),
    file_name=f"nifty100_screener_FY{year}.csv",
    mime="text/csv",
)



# --------------------------------------------------
# VALUATION INTELLIGENCE
# --------------------------------------------------

st.divider()

st.header("💎 Valuation Intelligence")
st.caption(
    "Sector-relative valuation analysis generated by the "
    "NIFTY 100 valuation engine."
)

valuation_path = ROOT_DIR / "output" / "valuation_summary.xlsx"

if valuation_path.exists():

    valuation_df = pd.read_excel(
        valuation_path,
        sheet_name="Valuation Summary"
    )

    valuation_df["P/E"] = pd.to_numeric(
        valuation_df["P/E"], errors="coerce"
    )

    valuation_df["FCF_yield_pct"] = pd.to_numeric(
        valuation_df["FCF_yield_pct"], errors="coerce"
    )

    flag_counts = (
        valuation_df["valuation_flag"]
        .value_counts()
    )

    fair_count = int(flag_counts.get("Fair", 0))
    discount_count = int(flag_counts.get("Discount", 0))
    caution_count = int(flag_counts.get("Caution", 0))

    v1, v2, v3 = st.columns(3)

    v1.metric("Fair Valuation", fair_count)
    v2.metric("Discount", discount_count)
    v3.metric("Caution", caution_count)

    st.subheader("Valuation Distribution")

    chart_data = (
        valuation_df["valuation_flag"]
        .value_counts()
        .rename_axis("Classification")
        .reset_index(name="Companies")
    )

    fig = px.pie(
        chart_data,
        names="Classification",
        values="Companies",
        hole=0.55,
        color="Classification",
        color_discrete_map={
            "Fair": "#123B69",
            "Discount": "#16845B",
            "Caution": "#F28C28",
            "Insufficient Data": "#A0AEC0"
        }
    )

    fig.update_layout(
        height=380,
        font=dict(family="Times New Roman"),
        paper_bgcolor="white",
        plot_bgcolor="white"
    )

    st.plotly_chart(fig, width="stretch")

    st.subheader("Explore Valuation Results")

    flag_options = ["All"] + sorted(
        valuation_df["valuation_flag"].dropna().unique().tolist()
    )

    selected_flag = st.selectbox(
        "Valuation classification",
        flag_options,
        key="valuation_flag_filter"
    )

    sector_options = ["All"] + sorted(
        valuation_df["sector"].dropna().unique().tolist()
    )

    selected_sector = st.selectbox(
        "Sector",
        sector_options,
        key="valuation_sector_filter"
    )

    filtered_valuation = valuation_df.copy()

    if selected_flag != "All":
        filtered_valuation = filtered_valuation[
            filtered_valuation["valuation_flag"] == selected_flag
        ]

    if selected_sector != "All":
        filtered_valuation = filtered_valuation[
            filtered_valuation["sector"] == selected_sector
        ]

    valuation_columns = [
        "company_id",
        "company_name",
        "sector",
        "P/E",
        "P/B",
        "EV/EBITDA",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
        "valuation_flag"
    ]

    valuation_display = filtered_valuation[
        valuation_columns
    ].rename(columns={
        "company_id": "Ticker",
        "company_name": "Company",
        "sector": "Sector",
        "FCF_yield_pct": "FCF Yield (%)",
        "5yr_median_PE": "5Y Median P/E",
        "PE_vs_sector_median_pct": "P/E vs Sector (%)",
        "valuation_flag": "Classification"
    })

    st.dataframe(
        valuation_display.round(2),
        width="stretch",
        hide_index=True
    )

    st.caption(
        f"Displaying {len(filtered_valuation)} of "
        f"{len(valuation_df)} companies."
    )

    d1, d2 = st.columns(2)

    with d1:
        st.download_button(
            "⬇️ Download Valuation Excel",
            data=valuation_path.read_bytes(),
            file_name="valuation_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with d2:
        st.download_button(
            "⬇️ Download Valuation CSV",
            data=valuation_df.to_csv(index=False).encode("utf-8"),
            file_name="valuation_summary.csv",
            mime="text/csv"
        )

else:
    st.warning(
        "Valuation output not found. Run "
        "`python scripts/run_valuation.py` first."
    )
