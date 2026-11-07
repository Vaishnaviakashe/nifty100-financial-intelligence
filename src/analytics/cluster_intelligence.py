import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "data" / "nifty100.db"
OUTPUT_DIR = ROOT / "output"
REPORT_DIR = ROOT / "reports"

CLUSTER_FILE = OUTPUT_DIR / "cluster_labels.csv"
FEATURE_FILE = OUTPUT_DIR / "clustering_feature_data.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Five features used in Day 36 clustering
CLUSTER_FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

# Ten KPIs used for correlation, outlier detection and portfolio stats
KPI_COLUMNS = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "free_cash_flow_cr",
    "cfo_quality_score",
    "fcf_conversion_pct",
]


# ============================================================
# DATA LOADING
# ============================================================


def load_data():
    """Load company, sector and financial ratio data."""

    with sqlite3.connect(DB_PATH) as conn:
        companies = pd.read_sql_query(
            "SELECT id AS company_id, company_name FROM companies",
            conn,
        )

        sectors = pd.read_sql_query(
            """
            SELECT company_id, broad_sector
            FROM sectors
            """,
            conn,
        )

        ratios = pd.read_sql_query(
            "SELECT * FROM financial_ratios",
            conn,
        )

    required = ["company_id", "year"] + KPI_COLUMNS

    missing = [col for col in required if col not in ratios.columns]

    if missing:
        raise ValueError(f"Missing required financial_ratios columns: {missing}")

    ratios["year_date"] = pd.to_datetime(
        ratios["year"].astype(str),
        errors="coerce",
    )

    ratios = ratios.dropna(subset=["year_date"])

    # Latest financial ratio record for each company
    latest = ratios.sort_values("year_date").groupby("company_id").tail(1).copy()

    latest = latest[["company_id", "year"] + KPI_COLUMNS]

    data = companies.merge(sectors, on="company_id", how="left").merge(
        latest, on="company_id", how="left"
    )

    return data


# ============================================================
# DAY 37 - TASK 1: CLUSTER PROFILES
# ============================================================


def generate_cluster_profiles():

    labels = pd.read_csv(CLUSTER_FILE)
    features = pd.read_csv(FEATURE_FILE)

    required = ["company_id", "cluster_id"]
    missing = [col for col in required if col not in labels.columns]

    if missing:
        raise ValueError(f"Missing cluster label columns: {missing}")

    missing_features = [col for col in CLUSTER_FEATURES if col not in features.columns]

    if missing_features:
        raise ValueError(f"Missing clustering features: {missing_features}")

    data = labels.merge(
        features[["company_id"] + CLUSTER_FEATURES],
        on="company_id",
        how="left",
        validate="one_to_one",
    )

    grouped = data.groupby("cluster_id")

    profiles = grouped[CLUSTER_FEATURES].agg(["mean", "median"])

    profiles.columns = [f"{feature}_{stat}" for feature, stat in profiles.columns]

    profiles.insert(
        0,
        "company_count",
        grouped.size(),
    )

    profiles = profiles.reset_index()

    profiles.to_csv(
        OUTPUT_DIR / "cluster_profiles.csv",
        index=False,
    )

    print("\nCLUSTER PROFILES")
    print(profiles.round(2).to_string(index=False))

    return profiles


# ============================================================
# DAY 37 - TASK 2: KPI CORRELATION HEATMAP
# ============================================================


def generate_correlation_heatmap(data):

    correlation = data[KPI_COLUMNS].corr(
        method="pearson",
        min_periods=3,
    )

    fig, ax = plt.subplots(figsize=(13, 10))

    image = ax.imshow(
        correlation,
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        aspect="auto",
    )

    ax.set_xticks(range(len(KPI_COLUMNS)))
    ax.set_yticks(range(len(KPI_COLUMNS)))

    ax.set_xticklabels(
        KPI_COLUMNS,
        rotation=45,
        ha="right",
    )

    ax.set_yticklabels(KPI_COLUMNS)

    # Display correlation values
    for i in range(len(KPI_COLUMNS)):
        for j in range(len(KPI_COLUMNS)):
            value = correlation.iloc[i, j]

            if pd.notna(value):
                ax.text(
                    j,
                    i,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    fontsize=8,
                )

    ax.set_title(
        "NIFTY 100 - Financial KPI Correlation Heatmap",
        fontsize=14,
        pad=20,
    )

    fig.colorbar(
        image,
        ax=ax,
        label="Pearson Correlation",
    )

    fig.tight_layout()

    output_path = REPORT_DIR / "correlation_heatmap.png"

    fig.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"\nCorrelation heatmap saved: {output_path}")

    correlation.to_csv(OUTPUT_DIR / "kpi_correlation_matrix.csv")

    return correlation


# ============================================================
# DAY 37 - TASK 3: SECTOR-WISE OUTLIER DETECTION
# ============================================================


def generate_outlier_report(data):

    records = []

    for kpi in KPI_COLUMNS:

        # Calculate Z-score separately within each sector
        sector_groups = data.groupby("broad_sector")[kpi]

        sector_mean = sector_groups.transform("mean")
        sector_std = sector_groups.transform("std")
        sector_count = sector_groups.transform("count")

        z_scores = (data[kpi] - sector_mean) / sector_std

        mask = z_scores.abs().gt(3) & sector_count.ge(3) & z_scores.notna()

        outliers = data.loc[
            mask,
            [
                "company_id",
                "company_name",
                "broad_sector",
                kpi,
            ],
        ].copy()

        for index, row in outliers.iterrows():

            records.append(
                {
                    "company_id": row["company_id"],
                    "company_name": row["company_name"],
                    "broad_sector": row["broad_sector"],
                    "kpi": kpi,
                    "value": row[kpi],
                    "z_score": z_scores.loc[index],
                    "severity": ("High" if abs(z_scores.loc[index]) > 4 else "Outlier"),
                }
            )

    columns = [
        "company_id",
        "company_name",
        "broad_sector",
        "kpi",
        "value",
        "z_score",
        "severity",
    ]

    report = pd.DataFrame(
        records,
        columns=columns,
    )

    report.to_csv(
        OUTPUT_DIR / "outlier_report.csv",
        index=False,
    )

    print("\nSECTOR-WISE OUTLIER REPORT")
    print(f"Total outlier records: {len(report)}")

    if not report.empty:
        print(report.to_string(index=False))
    else:
        print("No outliers detected using the selected criteria.")

    return report


# ============================================================
# DAY 37 - TASK 4: PORTFOLIO STATISTICS
# ============================================================


def generate_portfolio_stats(data):

    statistics = []

    for kpi in KPI_COLUMNS:

        values = data[kpi].dropna()

        statistics.append(
            {
                "metric": kpi,
                "company_count": len(values),
                "missing_count": data[kpi].isna().sum(),
                "P10": values.quantile(0.10),
                "P25": values.quantile(0.25),
                "P50": values.quantile(0.50),
                "P75": values.quantile(0.75),
                "P90": values.quantile(0.90),
                "mean": values.mean(),
                "std": values.std(),
            }
        )

    stats = pd.DataFrame(statistics)

    stats.to_csv(
        OUTPUT_DIR / "portfolio_stats.csv",
        index=False,
    )

    print("\nPORTFOLIO STATISTICS")
    print(stats.round(2).to_string(index=False))

    return stats


# ============================================================
# MAIN EXECUTION
# ============================================================


def main():

    print("=" * 65)
    print("DAY 37 - CLUSTER INTELLIGENCE")
    print("=" * 65)

    print("\nLoading financial data...")

    data = load_data()

    print(f"Companies loaded: {len(data)}")
    print(
        "Companies with financial ratios:",
        data[KPI_COLUMNS].notna().any(axis=1).sum(),
    )

    print("\n1. Generating cluster profiles...")
    profiles = generate_cluster_profiles()

    print("\n2. Generating KPI correlation heatmap...")
    correlation = generate_correlation_heatmap(data)

    print("\n3. Detecting sector-wise outliers...")
    generate_outlier_report(data)

    print("\n4. Generating portfolio statistics...")
    stats = generate_portfolio_stats(data)

    # Final validation
    labels = pd.read_csv(CLUSTER_FILE)

    assert labels["company_id"].nunique() == 92
    assert len(profiles) == 5
    assert len(stats) == 10
    assert correlation.shape == (10, 10)

    expected_files = [
        OUTPUT_DIR / "cluster_profiles.csv",
        OUTPUT_DIR / "outlier_report.csv",
        OUTPUT_DIR / "portfolio_stats.csv",
        OUTPUT_DIR / "kpi_correlation_matrix.csv",
        REPORT_DIR / "correlation_heatmap.png",
    ]

    assert all(path.exists() for path in expected_files)

    print("\n" + "=" * 65)
    print("DAY 37 VALIDATION PASSED")
    print("=" * 65)

    print("\nGenerated files:")

    for path in expected_files:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
