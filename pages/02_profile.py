"""Company Profile page — NIFTY 100 Financial Intelligence Platform."""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "nifty100.db"

NAVY = "#123B69"
ORANGE = "#F28C28"
GREY = "#718096"


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

@st.cache_data(ttl=600)
def load_companies():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT
                id,
                company_name,
                company_logo,
                about_company,
                website,
                nse_profile,
                bse_profile,
                face_value,
                book_value,
                roce_percentage,
                roe_percentage
            FROM companies
            ORDER BY company_name
            """,
            conn,
        )


@st.cache_data(ttl=600)
def load_company_data(company_id):
    with sqlite3.connect(DB_PATH) as conn:
        ratios = pd.read_sql_query(
            """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
            """,
            conn,
            params=(company_id,),
        )

        profit_loss = pd.read_sql_query(
            """
            SELECT *
            FROM profitandloss
            WHERE company_id = ?
            """,
            conn,
            params=(company_id,),
        )

        sectors = pd.read_sql_query(
            """
            SELECT *
            FROM sectors
            WHERE company_id = ?
            """,
            conn,
            params=(company_id,),
        )

        pros_cons = pd.read_sql_query(
            """
            SELECT pros, cons
            FROM prosandcons
            WHERE company_id = ?
            """,
            conn,
            params=(company_id,),
        )

    return ratios, profit_loss, sectors, pros_cons


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def latest_value(data, column):
    if data.empty or column not in data.columns:
        return None

    values = pd.to_numeric(data[column], errors="coerce").dropna()

    if values.empty:
        return None

    return values.iloc[-1]


def format_number(value, suffix="", decimals=2):
    if value is None or pd.isna(value):
        return "N/A"

    return f"{value:,.{decimals}f}{suffix}"


def calculate_revenue_cagr(data):
    if data.empty or len(data) < 2:
        return None

    history = data[["year", "sales"]].copy()
    history["sales"] = pd.to_numeric(history["sales"], errors="coerce")
    history["date"] = pd.to_datetime(history["year"], errors="coerce")

    history = history.dropna(subset=["sales", "date"])
    history = history.sort_values("date")

    if len(history) < 2:
        return None

    latest = history.iloc[-1]
    target_date = latest["date"] - pd.DateOffset(years=5)

    base_candidates = history[history["date"] <= target_date]

    if base_candidates.empty:
        return None

    base = base_candidates.iloc[-1]
    years = (latest["date"] - base["date"]).days / 365.25

    if years <= 0 or base["sales"] <= 0 or latest["sales"] <= 0:
        return None

    return ((latest["sales"] / base["sales"]) ** (1 / years) - 1) * 100


def make_chart_layout(fig, height=350):
    fig.update_layout(
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(
            family="Times New Roman",
            color=NAVY,
            size=13,
        ),
        margin=dict(l=20, r=20, t=45, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor="#DCE4ED",
    )

    fig.update_yaxes(
        gridcolor="#E9EEF4",
        zerolinecolor="#DCE4ED",
    )

    return fig


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("🏢 Company Profile")

st.caption(
    "Explore company fundamentals, financial performance "
    "and business quality."
)

st.divider()


# --------------------------------------------------
# COMPANY SEARCH
# --------------------------------------------------

if not DB_PATH.exists():
    st.error(f"Database not found: {DB_PATH}")
    st.stop()

companies = load_companies()

if companies.empty:
    st.warning("No company records were found.")
    st.stop()

company_options = {
    f"{row.company_name} ({row.id})": row.id
    for row in companies.itertuples()
}

selected_company = st.selectbox(
    "Search or select a company",
    options=list(company_options.keys()),
    key="profile_company_selector",
)

company_id = company_options[selected_company]

company = companies.loc[
    companies["id"] == company_id
].iloc[0]

ratios, profit_loss, sectors, pros_cons = load_company_data(company_id)

if not ratios.empty:
    ratios = ratios.copy()
    ratios["year_date"] = pd.to_datetime(
        ratios["year"], errors="coerce"
    )
    ratios = ratios.sort_values("year_date")

if not profit_loss.empty:
    profit_loss = profit_loss.copy()
    profit_loss["year_date"] = pd.to_datetime(
        profit_loss["year"], errors="coerce"
    )
    profit_loss = profit_loss.sort_values("year_date")


# --------------------------------------------------
# COMPANY OVERVIEW
# --------------------------------------------------

st.subheader("Company Overview")

overview_left, overview_right = st.columns([4, 1])

with overview_left:
    st.markdown(
        f"""
        <h2 style="
            color: {NAVY};
            font-family: 'Times New Roman', serif;
            margin-bottom: 4px;
        ">{company['company_name']}</h2>
        <p style="color: {GREY}; font-size: 15px;">
            Company ID: <b>{company_id}</b>
        </p>
        """,
        unsafe_allow_html=True,
    )

    description = company["about_company"]

    if pd.notna(description) and str(description).strip():
        st.write(description)
    else:
        st.caption("Company description is not available.")

with overview_right:
    logo = company["company_logo"]

    if pd.notna(logo) and str(logo).startswith("http"):
        st.image(logo, width=100)

sector_name = "Not available"
sub_sector = ""

if not sectors.empty:
    sector_name = sectors.iloc[0]["broad_sector"]
    sub_sector = sectors.iloc[0]["sub_sector"]

st.markdown(
    f"""
    <div style="
        background: #F5F7FA;
        border-left: 4px solid {ORANGE};
        padding: 12px 16px;
        border-radius: 8px;
        margin: 12px 0 20px 0;
        font-family: 'Times New Roman', serif;
    ">
        <b>Sector:</b> {sector_name}
        &nbsp;&nbsp; | &nbsp;&nbsp;
        <b>Industry:</b> {sub_sector or "Not available"}
    </div>
    """,
    unsafe_allow_html=True,
)

link_columns = st.columns(3)

for col, label, url in [
    (link_columns[0], "Company Website", company["website"]),
    (link_columns[1], "NSE Profile", company["nse_profile"]),
    (link_columns[2], "BSE Profile", company["bse_profile"]),
]:
    if pd.notna(url) and str(url).startswith("http"):
        col.link_button(label, url, width="stretch")


# --------------------------------------------------
# FINANCIAL KPIs
# --------------------------------------------------

st.divider()
st.subheader("Financial Performance")

latest_ratio = ratios.iloc[-1] if not ratios.empty else None

roe = (
    latest_value(ratios, "return_on_equity_pct")
    if latest_ratio is not None else None
)

roce = (
    latest_value(ratios, "return_on_capital_employed_pct")
    if latest_ratio is not None else None
)

npm = (
    latest_value(ratios, "net_profit_margin_pct")
    if latest_ratio is not None else None
)

debt_equity = (
    latest_value(ratios, "debt_to_equity")
    if latest_ratio is not None else None
)

fcf = (
    latest_value(ratios, "free_cash_flow_cr")
    if latest_ratio is not None else None
)

revenue_cagr = calculate_revenue_cagr(profit_loss)

kpi_values = [
    ("Return on Equity", format_number(roe, "%")),
    ("Return on Capital Employed", format_number(roce, "%")),
    ("Net Profit Margin", format_number(npm, "%")),
    ("Debt / Equity", format_number(debt_equity)),
    ("Revenue CAGR (5Y)", format_number(revenue_cagr, "%")),
    ("Latest Free Cash Flow", format_number(fcf, " Cr")),
]

kpi_columns = st.columns(3)

for index, (label, value) in enumerate(kpi_values):
    with kpi_columns[index % 3]:
        st.metric(label, value)


# --------------------------------------------------
# HISTORICAL REVENUE AND PROFIT
# --------------------------------------------------

st.divider()
st.subheader("Historical Financials")

if not profit_loss.empty:
    chart_data = profit_loss.copy()

    chart_data["sales"] = pd.to_numeric(
        chart_data["sales"], errors="coerce"
    )
    chart_data["net_profit"] = pd.to_numeric(
        chart_data["net_profit"], errors="coerce"
    )

    chart_data = chart_data.dropna(
        subset=["sales", "net_profit", "year_date"]
    ).tail(10)

    if not chart_data.empty:
        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=chart_data["year"],
                y=chart_data["sales"],
                name="Revenue",
                marker_color=NAVY,
            )
        )

        fig.add_trace(
            go.Bar(
                x=chart_data["year"],
                y=chart_data["net_profit"],
                name="Net Profit",
                marker_color=ORANGE,
            )
        )

        fig.update_layout(
            title="Revenue vs Net Profit (₹ Crore)",
            barmode="group",
            xaxis_title="Financial Year",
            yaxis_title="Amount (₹ Crore)",
        )

        st.plotly_chart(
            make_chart_layout(fig),
            width="stretch",
        )
    else:
        st.info("Historical revenue and profit data is unavailable.")
else:
    st.info("No profit and loss records are available for this company.")


# --------------------------------------------------
# ROE AND ROCE TREND
# --------------------------------------------------

st.divider()
st.subheader("Return Ratios Trend")

if not ratios.empty:
    trend_data = ratios[
        [
            "year",
            "year_date",
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
        ]
    ].copy()

    trend_data = trend_data.dropna(subset=["year_date"]).tail(10)

    trend_data["return_on_equity_pct"] = pd.to_numeric(
        trend_data["return_on_equity_pct"], errors="coerce"
    )

    trend_data["return_on_capital_employed_pct"] = pd.to_numeric(
        trend_data["return_on_capital_employed_pct"], errors="coerce"
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=trend_data["year"],
            y=trend_data["return_on_equity_pct"],
            name="ROE",
            mode="lines+markers",
            line=dict(color=NAVY, width=3),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=trend_data["year"],
            y=trend_data["return_on_capital_employed_pct"],
            name="ROCE",
            mode="lines+markers",
            line=dict(color=ORANGE, width=3),
        )
    )

    fig.update_layout(
        title="ROE and ROCE over time",
        xaxis_title="Financial Year",
        yaxis_title="Percentage (%)",
    )

    st.plotly_chart(
        make_chart_layout(fig),
        width="stretch",
    )
else:
    st.info("Return ratio history is unavailable.")


# --------------------------------------------------
# PROS AND CONS
# --------------------------------------------------

st.divider()
st.subheader("Business Strengths & Risks")

if not pros_cons.empty:
    pros_col, cons_col = st.columns(2)

    with pros_col:
        st.markdown(
            f"<h4 style='color:{NAVY};'>✓ Strengths</h4>",
            unsafe_allow_html=True,
        )

        for item in pros_cons["pros"].dropna():
            st.success(str(item))

    with cons_col:
        st.markdown(
            f"<h4 style='color:{NAVY};'>⚠ Risks</h4>",
            unsafe_allow_html=True,
        )

        for item in pros_cons["cons"].dropna():
            st.warning(str(item))
else:
    st.info(
        "Pros and cons have not been populated for this company yet."
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "NIFTY 100 Financial Intelligence Platform | "
    "Company financial data sourced from the project database."
)