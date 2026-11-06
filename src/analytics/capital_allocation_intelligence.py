
"""Sprint 5 - Day 32: Capital Allocation Intelligence."""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "nifty100.db"
INPUT_PATH = ROOT / "output" / "capital_allocation.csv"
OUTPUT_DIR = ROOT / "output"

OUTPUT_DIR.mkdir(exist_ok=True)


def load_data():
    """Load annual capital allocation and company-sector information."""

    allocation = pd.read_csv(INPUT_PATH)

    required = {
        "company_id", "year", "CFO_sign",
        "CFI_sign", "CFF_sign", "pattern_label"
    }

    missing = required - set(allocation.columns)
    if missing:
        raise ValueError(f"Missing allocation columns: {missing}")

    allocation["year"] = pd.to_datetime(
        allocation["year"], errors="coerce"
    )

    allocation = allocation.dropna(subset=["year"])
    allocation = allocation.sort_values(["company_id", "year"])

    with sqlite3.connect(DB_PATH) as conn:
        companies = pd.read_sql_query(
            "SELECT id, company_name FROM companies", conn
        )
        sectors = pd.read_sql_query(
            "SELECT company_id, broad_sector, sub_sector FROM sectors",
            conn,
        )

    master = companies.rename(columns={"id": "company_id"})

    master = master.merge(
        sectors.drop_duplicates("company_id"),
        on="company_id",
        how="left",
    )

    allocation = allocation.merge(
        master,
        on="company_id",
        how="left",
    )

    return allocation, master


def build_company_summary(allocation, master):
    """Create one capital allocation intelligence record per company."""

    records = []

    for company_id, group in allocation.groupby("company_id"):
        group = group.sort_values("year")

        counts = group["pattern_label"].value_counts()
        dominant_pattern = counts.index[0]
        dominant_count = counts.iloc[0]

        total_years = len(group)
        consistency_pct = dominant_count / total_years * 100

        if consistency_pct >= 70:
            consistency = "Consistent"
        elif consistency_pct >= 50:
            consistency = "Moderately Consistent"
        else:
            consistency = "Variable"

        latest = group.iloc[-1]
        previous = group.iloc[-2] if len(group) >= 2 else None

        distress_years = int(
            (group["pattern_label"] == "Distress").sum()
        )

        row = {
            "company_id": company_id,
            "company_name": latest.get("company_name"),
            "broad_sector": latest.get("broad_sector"),
            "sub_sector": latest.get("sub_sector"),
            "years_analyzed": total_years,
            "first_year": group["year"].min().strftime("%Y-%m"),
            "latest_year": latest["year"].strftime("%Y-%m"),
            "latest_pattern": latest["pattern_label"],
            "previous_pattern": (
                previous["pattern_label"]
                if previous is not None else None
            ),
            "dominant_pattern": dominant_pattern,
            "dominant_pattern_years": int(dominant_count),
            "pattern_consistency_pct": round(consistency_pct, 2),
            "consistency_label": consistency,
            "distinct_patterns": int(
                group["pattern_label"].nunique()
            ),
            "distress_years": distress_years,
            "distress_history_pct": round(
                distress_years / total_years * 100, 2
            ),
            "pattern_changes": int(
                group["pattern_label"].ne(
                    group["pattern_label"].shift()
                ).sum() - 1
            ),
        }

        for pattern in sorted(group["pattern_label"].dropna().unique()):
            row[f"{pattern.lower().replace(' ', '_')}_years"] = int(
                (group["pattern_label"] == pattern).sum()
            )

        records.append(row)

    summary = pd.DataFrame(records)

    # Preserve all 92 companies, including companies without allocation history.
    summary = master.merge(
        summary,
        on=[
            "company_id", "company_name",
            "broad_sector", "sub_sector"
        ],
        how="left",
    )

    summary["years_analyzed"] = (
        summary["years_analyzed"].fillna(0).astype(int)
    )

    return summary


def build_transitions(allocation):
    """Identify year-to-year capital allocation pattern changes."""

    df = allocation.sort_values(["company_id", "year"]).copy()

    df["previous_pattern"] = (
        df.groupby("company_id")["pattern_label"].shift(1)
    )

    df["previous_year"] = (
        df.groupby("company_id")["year"].shift(1)
    )

    transitions = df[df["previous_pattern"].notna()].copy()

    transitions["transition"] = (
        transitions["previous_pattern"].astype(str)
        + " -> "
        + transitions["pattern_label"].astype(str)
    )

    transitions["year"] = transitions["year"].dt.strftime("%Y-%m")
    transitions["previous_year"] = (
        transitions["previous_year"].dt.strftime("%Y-%m")
    )

    columns = [
        "company_id", "company_name", "broad_sector",
        "previous_year", "year", "previous_pattern",
        "pattern_label", "transition",
    ]

    return transitions[columns]


def build_sector_summary(summary):
    """Summarize latest allocation patterns by sector."""

    valid = summary[
        summary["latest_pattern"].notna()
        & summary["broad_sector"].notna()
    ].copy()

    counts = pd.crosstab(
        valid["broad_sector"],
        valid["latest_pattern"],
    )

    percentages = counts.div(
        counts.sum(axis=1), axis=0
    ) * 100

    counts.columns = [
        f"{col.lower().replace(' ', '_')}_companies"
        for col in counts.columns
    ]

    percentages.columns = [
        f"{col.lower().replace(' ', '_')}_pct"
        for col in percentages.columns
    ]

    sector_summary = counts.join(percentages).reset_index()

    sector_summary["companies_analyzed"] = (
        counts.sum(axis=1).values
    )

    return sector_summary


def main():
    print("\nDAY 32 - CAPITAL ALLOCATION INTELLIGENCE")
    print("=" * 50)

    allocation, master = load_data()

    summary = build_company_summary(allocation, master)
    transitions = build_transitions(allocation)
    sector_summary = build_sector_summary(summary)

    # Export individual deliverables.
    summary.to_csv(
        OUTPUT_DIR / "capital_allocation_summary.csv",
        index=False,
    )

    transitions.to_csv(
        OUTPUT_DIR / "capital_allocation_transitions.csv",
        index=False,
    )

    sector_summary.to_csv(
        OUTPUT_DIR / "sector_capital_allocation.csv",
        index=False,
    )

    # Multi-sheet intelligence workbook.
    annual_history = allocation.copy()
    annual_history["year"] = (
        annual_history["year"].dt.strftime("%Y-%m")
    )

    with pd.ExcelWriter(
        OUTPUT_DIR / "capital_allocation_intelligence.xlsx",
        engine="openpyxl",
    ) as writer:
        summary.to_excel(
            writer, sheet_name="Company Intelligence", index=False
        )

        annual_history.to_excel(
            writer, sheet_name="Annual History", index=False
        )

        transitions.to_excel(
            writer, sheet_name="Pattern Transitions", index=False
        )

        sector_summary.to_excel(
            writer, sheet_name="Sector Summary", index=False
        )

    print(f"\nMaster companies: {len(master)}")
    print(f"Annual allocation records: {len(allocation)}")
    print(f"Companies in intelligence: {len(summary)}")
    print(f"Companies with allocation history: {summary['latest_pattern'].notna().sum()}")
    print(f"Pattern transitions: {len(transitions)}")

    print("\nLatest capital allocation patterns:")
    print(summary["latest_pattern"].value_counts(dropna=False))

    print("\nConsistency classification:")
    print(summary["consistency_label"].value_counts(dropna=False))

    print("\nSector summary:")
    print(sector_summary.to_string(index=False))

    print("\nGenerated deliverables:")
    print("output/capital_allocation_intelligence.xlsx")
    print("output/capital_allocation_summary.csv")
    print("output/capital_allocation_transitions.csv")
    print("output/sector_capital_allocation.csv")


if __name__ == "__main__":
    main()
