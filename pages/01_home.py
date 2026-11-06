
"""Home dashboard — NIFTY 100 Financial Intelligence Platform."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.dashboard.utils.db import get_home_data, get_sectors


# --------------------------------------------------
# DESIGN CONSTANTS
# --------------------------------------------------

NAVY = "#123B69"
ORANGE = "#F28C28"
TEXT = "#18324F"
MUTED = "#718096"
LIGHT_GREY = "#F5F7FA"

CHART_COLORS = [
    NAVY,
    ORANGE,
    "#527DA8",
    "#E9A45F",
    "#8DAAC6",
    "#B8C9DA",
    "#D47B32",
    "#A5B8C9",
    "#E8C49F",
    "#385D80",
    "#C7D4E1",
]


# --------------------------------------------------
# CHART THEME
# --------------------------------------------------

def apply_chart_theme(fig, height=380):
    fig.update_layout(
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(
            family="Times New Roman",
            size=14,
            color=TEXT,
        ),
        title_font=dict(
            family="Times New Roman",
            size=19,
            color=NAVY,
        ),
        margin=dict(l=20, r=20, t=65, b=25),
        legend=dict(
            font=dict(
                family="Times New Roman",
                size=12,
                color=TEXT,
            )
        ),
    )

    return fig


# --------------------------------------------------
# HEADER
# --------------------------------------------------


st.title("📊 NIFTY 100 Financial Intelligence")

st.caption(
    "A data-driven view of financial strength, "
    "valuation and business quality."
)


# --------------------------------------------------
# FINANCIAL YEAR SELECTOR
# --------------------------------------------------

selected_year = st.selectbox(
    "Financial Year",
    options=list(range(2024, 2018, -1)),
    index=0,
    format_func=lambda year: f"FY {year}",
    key="home_financial_year_v2",
)

df = get_home_data(selected_year)
sectors = get_sectors()

if df is None or df.empty:
    st.warning(
        f"No financial data is available for FY {selected_year}."
    )
    st.stop()

df = df.copy()


# --------------------------------------------------
# DATA PREPARATION
# --------------------------------------------------

required_columns = [
    "company_id",
    "company_name",
    "broad_sector",
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "interest_coverage",
    "free_cash_flow_cr",
    "total_debt_cr",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "market_cap_crore",
    "current_sales",
    "base_sales",
]

for column in required_columns:
    if column not in df.columns:
        df[column] = np.nan

numeric_columns = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "interest_coverage",
    "free_cash_flow_cr",
    "total_debt_cr",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "market_cap_crore",
    "current_sales",
    "base_sales",
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column], errors="coerce"
    ).replace([np.inf, -np.inf], np.nan)

df["revenue_cagr_5yr"] = np.nan

valid_revenue = (
    (df["current_sales"] > 0)
    & (df["base_sales"] > 0)
)

df.loc[valid_revenue, "revenue_cagr_5yr"] = (
    (
        df.loc[valid_revenue, "current_sales"]
        / df.loc[valid_revenue, "base_sales"]
    ) ** (1 / 5) - 1
) * 100


# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------

def safe_mean(series):
    values = series.dropna()
    return values.mean() if not values.empty else np.nan


def safe_median(series):
    values = series.dropna()
    return values.median() if not values.empty else np.nan


def format_metric(value, suffix="", decimals=2):
    if pd.isna(value):
        return "N/A"

    return f"{value:,.{decimals}f}{suffix}"


average_roe = safe_mean(df["return_on_equity_pct"])
median_pe = safe_median(df["pe_ratio"])
median_de = safe_median(df["debt_to_equity"])
median_revenue_cagr = safe_median(df["revenue_cagr_5yr"])

total_companies = df["company_id"].nunique()

# Only count explicitly reported zero debt.
debt_free_count = int(
    (df["total_debt_cr"] == 0).sum()
)


# --------------------------------------------------
# MARKET OVERVIEW
# --------------------------------------------------

st.subheader("Market Overview")

kpis = [
    ("Average ROE", format_metric(average_roe, "%")),
    ("Median P/E", format_metric(median_pe)),
    ("Median Debt / Equity", format_metric(median_de)),
    ("Companies Covered", str(total_companies)),
    ("Median Revenue CAGR (5Y)", format_metric(median_revenue_cagr, "%")),
    ("Debt-Free Companies", str(debt_free_count)),
]

for start in range(0, len(kpis), 3):
    columns = st.columns(3)

    for column, (label, value) in zip(
        columns, kpis[start:start + 3]
    ):
        with column:
            st.metric(label, value)


st.divider()


# --------------------------------------------------
# SECTOR DISTRIBUTION
# --------------------------------------------------

st.subheader("Sector Distribution")

if (
    sectors is not None
    and not sectors.empty
    and {"broad_sector", "company_id"}.issubset(sectors.columns)
):

    sector_counts = (
        sectors.dropna(subset=["broad_sector"])
        .groupby("broad_sector")["company_id"]
        .nunique()
        .reset_index(name="companies")
        .sort_values("companies", ascending=False)
    )

    if not sector_counts.empty:

        fig_sector = px.pie(
            sector_counts,
            names="broad_sector",
            values="companies",
            hole=0.62,
            color_discrete_sequence=CHART_COLORS,
        )

        fig_sector.update_traces(
            textposition="inside",
            textinfo="percent",
            textfont=dict(
                family="Times New Roman",
                size=13,
                color="white",
            ),
            marker=dict(
                line=dict(color="white", width=2)
            ),
        )

        fig_sector.update_layout(
            title="Company Distribution Across Sectors",
            legend_title="Sector",
        )

        fig_sector = apply_chart_theme(fig_sector, 400)

        st.plotly_chart(
            fig_sector,
            width="stretch",
            key="home_sector_distribution",
        )

        st.caption(
            f"Sector coverage: {sector_counts['broad_sector'].nunique()} "
            f"sectors | {sector_counts['companies'].sum()} companies"
        )

    else:
        st.info("Sector distribution data is unavailable.")

else:
    st.info("Sector distribution data is unavailable.")


st.divider()


# --------------------------------------------------
# COMPOSITE QUALITY SCORE
# --------------------------------------------------

st.subheader("Top 5 Companies — Quality Ranking")

st.caption(
    "Companies are ranked using relative financial performance "
    "across six fundamental indicators."
)

score_columns = {
    "return_on_equity_pct": True,
    "return_on_capital_employed_pct": True,
    "net_profit_margin_pct": True,
    "interest_coverage": True,
    "free_cash_flow_cr": True,
    "debt_to_equity": False,
}

score_parts = pd.DataFrame(index=df.index)

for column, higher_is_better in score_columns.items():

    values = df[column].replace(
        [np.inf, -np.inf], np.nan
    )

    score_parts[column] = values.rank(
        pct=True,
        ascending=higher_is_better,
    ) * 100

df["quality_score"] = score_parts.mean(axis=1)

# At least three available indicators are required.
df["available_score_metrics"] = score_parts.notna().sum(axis=1)

ranked = df[
    (df["available_score_metrics"] >= 3)
    & df["quality_score"].notna()
].copy()

top_five = ranked.sort_values(
    "quality_score",
    ascending=False,
).head(5)


if not top_five.empty:

    display_columns = [
        "company_id",
        "company_name",
        "broad_sector",
        "quality_score",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "debt_to_equity",
    ]

    display_df = top_five[display_columns].rename(
        columns={
            "company_id": "Company ID",
            "company_name": "Company",
            "broad_sector": "Sector",
            "quality_score": "Quality Score",
            "return_on_equity_pct": "ROE (%)",
            "return_on_capital_employed_pct": "ROCE (%)",
            "debt_to_equity": "Debt / Equity",
        }
    )

    display_df["Quality Score"] = (
        display_df["Quality Score"].round(1)
    )

    display_df["ROE (%)"] = display_df["ROE (%)"].round(2)
    display_df["ROCE (%)"] = display_df["ROCE (%)"].round(2)
    display_df["Debt / Equity"] = (
        display_df["Debt / Equity"].round(2)
    )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Company ID": st.column_config.NumberColumn(
                "Company ID",
                format="%d",
            ),
            "Quality Score": st.column_config.ProgressColumn(
                "Quality Score",
                min_value=0,
                max_value=100,
                format="%.1f",
            ),
        },
    )

    st.caption(
        "Quality Score is a relative percentile-based ranking using "
        "ROE, ROCE, net profit margin, interest coverage, free cash flow "
        "and debt-to-equity. Higher scores indicate stronger relative "
        "performance among companies with sufficient available data."
    )

else:
    st.warning(
        "Not enough financial data to calculate reliable quality rankings."
    )


# --------------------------------------------------
# DATA COVERAGE
# --------------------------------------------------

st.divider()

st.caption(
    f"Selected financial year: FY {selected_year} | "
    f"Companies in database: {total_companies} | "
    "Metrics use the latest available records up to the selected year."
)
