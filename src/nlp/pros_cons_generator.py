import sqlite3
from pathlib import Path

import pandas as pd

# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "nifty100.db"
OUTPUT_DIR = ROOT / "output"

OUTPUT_FILE = OUTPUT_DIR / "pros_cons_generated.csv"
COVERAGE_FILE = OUTPUT_DIR / "pros_cons_coverage.csv"

MIN_CONFIDENCE = 60

PRO_TEXT = {
    1: "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
    2: "Strong free cash flow generation over 5 years signals healthy business fundamentals",
    3: "Debt-free balance sheet provides financial flexibility and eliminates interest burden",
    4: "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum",
    5: "Operating profit margin above 25% indicates strong pricing power and cost discipline",
    6: "Net profit compounding at above 20% over 5 years creates significant shareholder value",
    7: "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
    8: "Consistent dividend yield above 2% backed by positive free cash flow",
    9: "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
    10: "Return on equity improving for 3 consecutive years shows strengthening business quality",
    11: "Revenue growing slower than profits shows improving operating leverage and scale benefits",
    12: "Growing asset base funded by internal accruals reflects self-sustaining growth",
}

CON_TEXT = {
    1: "Debt-to-equity ratio of {value:.2f} is elevated for a non-financial company and warrants monitoring",
    2: "Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
    3: "Operating margins declining for 3 consecutive years suggest pricing or cost pressure",
    4: "Company reported a net loss in the most recent financial year",
    5: "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss",
    6: "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
    7: "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
    8: "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
    9: "Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
    10: "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
    11: "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility",
    12: "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
}


# ============================================================
# DATA LOADING
# ============================================================


def load_data():
    conn = sqlite3.connect(DB_PATH)

    try:
        companies = pd.read_sql_query(
            """
            SELECT c.id AS company_id,
                   c.company_name,
                   COALESCE(s.broad_sector, 'Unknown') AS sector
            FROM companies c
            LEFT JOIN sectors s ON c.id = s.company_id
            """,
            conn,
        )

        ratios = pd.read_sql_query(
            "SELECT * FROM financial_ratios",
            conn,
        )

        pnl = pd.read_sql_query(
            "SELECT * FROM profitandloss",
            conn,
        )

        balance = pd.read_sql_query(
            "SELECT * FROM balancesheet",
            conn,
        )

        cashflow = pd.read_sql_query(
            "SELECT * FROM cashflow",
            conn,
        )

        market = pd.read_sql_query(
            "SELECT * FROM market_cap",
            conn,
        )

    finally:
        conn.close()

    for df in [ratios, pnl, balance, cashflow, market]:
        if not df.empty:
            df["year_num"] = pd.to_numeric(
                df["year"].astype(str).str[:4],
                errors="coerce",
            )

            df.sort_values(
                ["company_id", "year_num"],
                inplace=True,
            )

    return companies, ratios, pnl, balance, cashflow, market


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def valid_values(series):
    return pd.to_numeric(series, errors="coerce").dropna()


def latest_value(df, column):
    if df.empty or column not in df.columns:
        return None

    values = valid_values(df[column])

    return None if values.empty else float(values.iloc[-1])


def get_cagr(df, column, years=5):
    """Calculate CAGR using the latest and earliest eligible observations."""

    if df.empty:
        return None

    data = df[["year_num", column]].copy()

    data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna().sort_values("year_num")
    data = data[data[column] > 0]

    if len(data) < 2:
        return None

    latest = data.iloc[-1]
    target_year = latest["year_num"] - years

    candidates = data[data["year_num"] <= target_year + 1]

    if candidates.empty:
        return None

    start = candidates.iloc[-1]
    actual_years = latest["year_num"] - start["year_num"]

    if actual_years < years - 1:
        return None

    return ((latest[column] / start[column]) ** (1 / actual_years) - 1) * 100


def consecutive_values(df, column, count):
    if df.empty or column not in df.columns:
        return []

    data = df.sort_values("year_num").tail(count)

    if len(data) < count:
        return []

    values = valid_values(data[column])

    if len(values) != count:
        return []

    return values.tolist()


def add_signal(signals, company_id, signal_type, rule_id, text, confidence):
    confidence = round(float(confidence), 2)

    if confidence > MIN_CONFIDENCE:
        signals.append(
            {
                "company_id": company_id,
                "type": signal_type,
                "rule_id": rule_id,
                "text": text,
                "confidence_pct": confidence,
            }
        )


def confidence_from_strength(value, threshold, direction="above"):
    """
    Confidence is a deterministic rule-strength score,
    not a statistically calibrated probability.
    """

    if direction == "above":
        ratio = value / threshold if threshold else 1
    else:
        ratio = threshold / value if value > 0 else 1

    return min(95, 70 + max(0, ratio - 1) * 25)


def is_financial_sector(sector):
    text = str(sector).lower()

    keywords = [
        "bank",
        "financial",
        "finance",
        "insurance",
        "nbfc",
        "lending",
    ]

    return any(word in text for word in keywords)


# ============================================================
# GENERATE PROS AND CONS
# ============================================================


def evaluate_company(company, ratios, pnl, balance, cashflow, market):

    company_id = company["company_id"]
    sector = company["sector"]

    r = ratios[ratios["company_id"] == company_id].copy()
    p = pnl[pnl["company_id"] == company_id].copy()
    b = balance[balance["company_id"] == company_id].copy()
    cf = cashflow[cashflow["company_id"] == company_id].copy()
    m = market[market["company_id"] == company_id].copy()

    r = r.sort_values("year_num")
    p = p.sort_values("year_num")
    b = b.sort_values("year_num")
    cf = cf.sort_values("year_num")
    m = m.sort_values("year_num")

    signals = []

    # --------------------------------------------------------
    # PRO 1: ROE > 20% for 3 consecutive years
    # --------------------------------------------------------

    roe = consecutive_values(r, "return_on_equity_pct", 3)

    if len(roe) == 3 and all(v > 20 for v in roe):
        add_signal(signals, company_id, "pro", 1, PRO_TEXT[1], 90)

    # --------------------------------------------------------
    # PRO 2: Positive FCF for 5 consecutive years
    # --------------------------------------------------------

    fcf = consecutive_values(r, "free_cash_flow_cr", 5)

    if len(fcf) == 5 and all(v > 0 for v in fcf):
        add_signal(signals, company_id, "pro", 2, PRO_TEXT[2], 95)

    # --------------------------------------------------------
    # PRO 3: Debt-to-equity = 0
    # --------------------------------------------------------

    de = latest_value(r, "debt_to_equity")

    if de is not None and de == 0:
        add_signal(signals, company_id, "pro", 3, PRO_TEXT[3], 90)

    # --------------------------------------------------------
    # PRO 4: Revenue CAGR > 15%
    # --------------------------------------------------------

    revenue_cagr = get_cagr(p, "sales", 5)

    if revenue_cagr is not None and revenue_cagr > 15:
        add_signal(
            signals,
            company_id,
            "pro",
            4,
            PRO_TEXT[4],
            confidence_from_strength(revenue_cagr, 15),
        )

    # --------------------------------------------------------
    # PRO 5: OPM > 25%
    # --------------------------------------------------------

    opm = latest_value(r, "operating_profit_margin_pct")

    if opm is not None and opm > 25:
        add_signal(
            signals,
            company_id,
            "pro",
            5,
            PRO_TEXT[5],
            confidence_from_strength(opm, 25),
        )

    # --------------------------------------------------------
    # PRO 6: PAT CAGR > 20%
    # --------------------------------------------------------

    pat_cagr = get_cagr(p, "net_profit", 5)

    if pat_cagr is not None and pat_cagr > 20:
        add_signal(
            signals,
            company_id,
            "pro",
            6,
            PRO_TEXT[6],
            confidence_from_strength(pat_cagr, 20),
        )

    # --------------------------------------------------------
    # PRO 7: ICR > 10 or debt-free
    # --------------------------------------------------------

    icr = latest_value(r, "interest_coverage")

    if (icr is not None and icr > 10) or (de is not None and de == 0):
        add_signal(signals, company_id, "pro", 7, PRO_TEXT[7], 90)

    # --------------------------------------------------------
    # PRO 8: Dividend yield > 2% and positive FCF
    # --------------------------------------------------------

    dividend_yield = latest_value(m, "dividend_yield_pct")
    latest_fcf = latest_value(r, "free_cash_flow_cr")

    if (
        dividend_yield is not None
        and dividend_yield > 2
        and latest_fcf is not None
        and latest_fcf > 0
    ):
        add_signal(signals, company_id, "pro", 8, PRO_TEXT[8], 85)

    # --------------------------------------------------------
    # PRO 9: EPS CAGR > 15%
    # --------------------------------------------------------

    eps_cagr = get_cagr(p, "eps", 5)

    if eps_cagr is not None and eps_cagr > 15:
        add_signal(
            signals,
            company_id,
            "pro",
            9,
            PRO_TEXT[9],
            confidence_from_strength(eps_cagr, 15),
        )

    # --------------------------------------------------------
    # PRO 10: ROE improving for 3 consecutive years
    # --------------------------------------------------------

    roe_trend = consecutive_values(r, "return_on_equity_pct", 3)

    if len(roe_trend) == 3 and (roe_trend[0] < roe_trend[1] < roe_trend[2]):
        add_signal(signals, company_id, "pro", 10, PRO_TEXT[10], 85)

    # --------------------------------------------------------
    # PRO 11: Operating leverage
    # PAT CAGR > Revenue CAGR
    # --------------------------------------------------------

    if revenue_cagr is not None and pat_cagr is not None and pat_cagr > revenue_cagr:
        add_signal(signals, company_id, "pro", 11, PRO_TEXT[11], 85)

    # --------------------------------------------------------
    # PRO 12: Assets growing while borrowings decline
    # --------------------------------------------------------

    if not b.empty and len(b) >= 2:
        latest_b = b.iloc[-1]
        previous_b = b.iloc[-2]

        assets_growing = (
            pd.notna(latest_b["total_assets"])
            and pd.notna(previous_b["total_assets"])
            and latest_b["total_assets"] > previous_b["total_assets"]
        )

        debt_declining = (
            pd.notna(latest_b["borrowings"])
            and pd.notna(previous_b["borrowings"])
            and latest_b["borrowings"] < previous_b["borrowings"]
        )

        if assets_growing and debt_declining:
            add_signal(signals, company_id, "pro", 12, PRO_TEXT[12], 85)

    # ========================================================
    # CON RULES
    # ========================================================

    # CON 1: D/E > 2 for non-financial companies

    if not is_financial_sector(sector) and de is not None and de > 2:
        add_signal(
            signals,
            company_id,
            "con",
            1,
            CON_TEXT[1].format(value=de),
            confidence_from_strength(de, 2),
        )

    # CON 2: FCF negative for 3 consecutive years

    fcf3 = consecutive_values(r, "free_cash_flow_cr", 3)

    if len(fcf3) == 3 and all(v < 0 for v in fcf3):
        add_signal(signals, company_id, "con", 2, CON_TEXT[2], 95)

    # CON 3: OPM declining for 3 consecutive years

    opm3 = consecutive_values(r, "operating_profit_margin_pct", 3)

    if len(opm3) == 3 and opm3[0] > opm3[1] > opm3[2]:
        add_signal(signals, company_id, "con", 3, CON_TEXT[3], 90)

    # CON 4: Latest net profit negative

    latest_pat = latest_value(p, "net_profit")

    if latest_pat is not None and latest_pat < 0:
        add_signal(signals, company_id, "con", 4, CON_TEXT[4], 95)

    # CON 5: Revenue declining for 2 consecutive years

    sales3 = consecutive_values(p, "sales", 3)

    if len(sales3) == 3 and sales3[0] > sales3[1] > sales3[2]:
        add_signal(signals, company_id, "con", 5, CON_TEXT[5], 90)

    # CON 6: ICR < 1.5

    if icr is not None and icr < 1.5:
        add_signal(signals, company_id, "con", 6, CON_TEXT[6], 90)

    # CON 7: Dividend payout > 100%

    payout = latest_value(r, "dividend_payout_ratio_pct")

    if payout is not None and payout > 100:
        add_signal(signals, company_id, "con", 7, CON_TEXT[7], 90)

    # CON 8: D/E rising for 3 consecutive years

    de3 = consecutive_values(r, "debt_to_equity", 3)

    if len(de3) == 3 and de3[0] < de3[1] < de3[2]:
        add_signal(signals, company_id, "con", 8, CON_TEXT[8], 85)

    # CON 9: EPS declining for 3 consecutive years

    eps3 = consecutive_values(p, "eps", 3)

    if len(eps3) == 3 and eps3[0] > eps3[1] > eps3[2]:
        add_signal(signals, company_id, "con", 9, CON_TEXT[9], 90)

    # CON 10: ROCE < 10%

    roce = latest_value(r, "return_on_capital_employed_pct")

    if roce is not None and roce < 10:
        add_signal(signals, company_id, "con", 10, CON_TEXT[10], 90)

    # CON 11: Net Debt / EBITDA > 3
    #
    # Current database does not contain a separately identifiable
    # cash balance. Total debt alone is NOT net debt.
    # Therefore this rule is intentionally not triggered.

    # CON 12: Revenue CAGR < 5%

    if revenue_cagr is not None and revenue_cagr < 5:
        add_signal(signals, company_id, "con", 12, CON_TEXT[12], 85)

    return signals


# ============================================================
# MAIN EXECUTION
# ============================================================


def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("NIFTY 100 - PROS AND CONS GENERATOR")
    print("=" * 60)

    companies, ratios, pnl, balance, cashflow, market = load_data()

    print(f"\nCompanies loaded: {len(companies)}")

    all_signals = []

    for _, company in companies.iterrows():

        signals = evaluate_company(
            company,
            ratios,
            pnl,
            balance,
            cashflow,
            market,
        )

        all_signals.extend(signals)

    columns = [
        "company_id",
        "type",
        "rule_id",
        "text",
        "confidence_pct",
    ]

    result = pd.DataFrame(all_signals, columns=columns)

    if not result.empty:
        result = result.drop_duplicates(subset=["company_id", "type", "rule_id"])

        result = result.sort_values(["company_id", "type", "rule_id"])

    result.to_csv(OUTPUT_FILE, index=False)

    # --------------------------------------------------------
    # COVERAGE VALIDATION
    # --------------------------------------------------------

    coverage_rows = []

    for company_id in companies["company_id"]:

        company_result = result[result["company_id"] == company_id]

        pro_count = int((company_result["type"] == "pro").sum())

        con_count = int((company_result["type"] == "con").sum())

        coverage_rows.append(
            {
                "company_id": company_id,
                "pro_count": pro_count,
                "con_count": con_count,
                "has_pro": pro_count >= 1,
                "has_con": con_count >= 1,
                "meets_both_requirements": (pro_count >= 1 and con_count >= 1),
            }
        )

    coverage = pd.DataFrame(coverage_rows)

    coverage.to_csv(COVERAGE_FILE, index=False)

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\nGENERATION SUMMARY")
    print("-" * 40)
    print(f"Total companies: {len(companies)}")
    print(f"Total signals: {len(result)}")

    if not result.empty:
        print(f"Pros generated: {(result['type'] == 'pro').sum()}")
        print(f"Cons generated: {(result['type'] == 'con').sum()}")

        print("\nRULE DISTRIBUTION")
        print(result.groupby(["type", "rule_id"]).size().to_string())

    print("\nCOMPANY COVERAGE")
    print(f"Companies with at least 1 pro: {coverage['has_pro'].sum()}")
    print(f"Companies with at least 1 con: {coverage['has_con'].sum()}")
    print("Companies with both: " f"{coverage['meets_both_requirements'].sum()}")

    print("\nCOMPANIES REQUIRING REVIEW")

    incomplete = coverage[~coverage["meets_both_requirements"]]

    if incomplete.empty:
        print("All companies have at least one pro and one con.")
    else:
        print(incomplete.to_string(index=False))

    print(f"\nSaved: {OUTPUT_FILE}")
    print(f"Saved: {COVERAGE_FILE}")

    print("\nDay 30 generator execution completed.")


if __name__ == "__main__":
    main()
