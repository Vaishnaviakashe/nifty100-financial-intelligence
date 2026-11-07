
"""KMeans financial clustering for the NIFTY 100 universe."""

import sqlite3
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "nifty100.db"
OUTPUT_DIR = ROOT / "output"
REPORT_DIR = ROOT / "reports"

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

EXPECTED_COMPANIES = 92
N_CLUSTERS = 5
RANDOM_STATE = 42


def load_data():
    """Load company, sector, ratio, P&L and cash-flow data."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        companies = pd.read_sql_query(
            """
            SELECT id AS company_id, company_name, roe_percentage
            FROM companies
            """,
            conn,
        )

        sectors = pd.read_sql_query(
            """
            SELECT company_id, broad_sector, sub_sector
            FROM sectors
            """,
            conn,
        )

        ratios = pd.read_sql_query(
            "SELECT * FROM financial_ratios", conn
        )

        pnl = pd.read_sql_query(
            "SELECT * FROM profitandloss", conn
        )

        cashflow = pd.read_sql_query(
            "SELECT * FROM cashflow", conn
        )

        balance_sheet = pd.read_sql_query(
            "SELECT * FROM balancesheet", conn
        )

    return companies, sectors, ratios, pnl, cashflow, balance_sheet


def normalize_year_column(data):
    """Convert year strings into sortable datetime values."""
    data = data.copy()
    data["year_date"] = pd.to_datetime(
        data["year"], errors="coerce"
    )
    return data


def calculate_historical_cagr(
    data,
    value_column,
    output_name,
    require_positive_history=False,
):
    """
    Calculate approximately five-year CAGR using historical observations.

    Requires positive starting and ending values.
    For FCF, also checks intermediate cash-flow consistency.
    """
    results = {}

    data = normalize_year_column(data)

    data[value_column] = pd.to_numeric(
        data[value_column], errors="coerce"
    )

    for company_id, group in data.groupby("company_id"):
        group = (
            group.dropna(subset=["year_date", value_column])
            .sort_values("year_date")
            .drop_duplicates("year_date", keep="last")
        )

        if len(group) < 2:
            results[company_id] = np.nan
            continue

        latest = group.iloc[-1]
        latest_date = latest["year_date"]

        # Select observations approximately five years apart.
        candidates = group[
            group["year_date"]
            <= latest_date - pd.DateOffset(years=4)
        ]

        if candidates.empty:
            results[company_id] = np.nan
            continue

        target_date = latest_date - pd.DateOffset(years=5)

        earliest = candidates.iloc[
            (candidates["year_date"] - target_date)
            .abs()
            .argmin()
        ]

        start_value = earliest[value_column]
        end_value = latest[value_column]

        years = (
            latest_date - earliest["year_date"]
        ).days / 365.25

        if years < 4 or years > 6:
            results[company_id] = np.nan
            continue

        if pd.isna(start_value) or pd.isna(end_value):
            results[company_id] = np.nan
            continue

        if start_value <= 0 or end_value <= 0:
            results[company_id] = np.nan
            continue

        # Avoid presenting FCF CAGR as meaningful when cash flow
        # repeatedly changes sign during the measurement period.
        if require_positive_history:
            period = group[
                (group["year_date"] >= earliest["year_date"])
                & (group["year_date"] <= latest_date)
            ]

            if len(period) < 5:
                results[company_id] = np.nan
                continue

            if (period[value_column] <= 0).any():
                results[company_id] = np.nan
                continue

        cagr = ((end_value / start_value) ** (1 / years) - 1) * 100

        if np.isfinite(cagr):
            results[company_id] = cagr
        else:
            results[company_id] = np.nan

    return pd.Series(results, name=output_name, dtype=float)


def get_latest_company_data(data):
    """Return the latest available observation for every company."""
    data = normalize_year_column(data)
    data = data.dropna(subset=["year_date"])
    data = data.sort_values("year_date")

    return data.groupby("company_id", as_index=False).tail(1)


def prepare_features():
    """Build the five company-level clustering features."""
    (
        companies,
        sectors,
        ratios,
        pnl,
        cashflow,
        balance_sheet,
    ) = load_data()

    # Latest financial ratios.
    ratios = ratios.copy()
    ratios = get_latest_company_data(ratios)

    latest_ratios = ratios[
        [
            "company_id",
            "year",
            "return_on_equity_pct",
            "debt_to_equity",
            "operating_profit_margin_pct",
        ]
    ].copy()

    # Latest P&L record for revenue CAGR calculation.
    pnl = normalize_year_column(pnl)
    pnl["sales"] = pd.to_numeric(
        pnl["sales"], errors="coerce"
    )

    revenue_cagr = calculate_historical_cagr(
        pnl,
        "sales",
        "revenue_cagr_5yr",
    )

    # FCF proxy = CFO + CFI.
    cashflow["free_cash_flow"] = (
        pd.to_numeric(
            cashflow["operating_activity"], errors="coerce"
        )
        + pd.to_numeric(
            cashflow["investing_activity"], errors="coerce"
        )
    )

    fcf_cagr = calculate_historical_cagr(
        cashflow,
        "free_cash_flow",
        "fcf_cagr_5yr",
        require_positive_history=True,
    )

    # Combine company and sector information.
    features = companies.merge(
        sectors,
        on="company_id",
        how="left",
        validate="one_to_one",
    )

    features = features.merge(
        latest_ratios,
        on="company_id",
        how="left",
        validate="one_to_one",
    )

    features = features.merge(
        revenue_cagr,
        left_on="company_id",
        right_index=True,
        how="left",
    )

    features = features.merge(
        fcf_cagr,
        left_on="company_id",
        right_index=True,
        how="left",
    )

    features[FEATURES] = features[FEATURES].apply(
        pd.to_numeric, errors="coerce"
    )

        # Flag questionable extreme values for investigation.
    features["roe_extreme_flag"] = (
        features["return_on_equity_pct"].abs() > 200
    )

    features["de_extreme_flag"] = (
        features["debt_to_equity"].abs() > 10
    )

    features["opm_extreme_flag"] = (
        features["operating_profit_margin_pct"].abs() > 100
    )

    # Compare latest ratio ROE against company master ROE.
    features["roe_master_difference"] = (
        features["return_on_equity_pct"]
        - features["roe_percentage"]
    )

    # Preserve all original values and quality flags before imputation.
    original = features.copy()

    return features, original


def impute_by_sector(features):
    """Impute missing features using sector medians."""
    features = features.copy()

    missing_report = []

    for column in FEATURES:
        missing_before = features[column].isna()

        for index in features.index[missing_before]:
            missing_report.append({
                "company_id": features.loc[index, "company_id"],
                "broad_sector": features.loc[index, "broad_sector"],
                "feature": column,
                "imputation_method": "sector_median",
            })

        sector_medians = features.groupby(
            "broad_sector"
        )[column].transform("median")

        features[column] = features[column].fillna(
            sector_medians
        )

        # Use global median only when a sector has no valid value.
        if features[column].isna().any():
            global_median = features[column].median()

            if pd.isna(global_median):
                raise ValueError(
                    f"Cannot impute feature: {column}"
                )

            features[column] = features[column].fillna(
                global_median
            )

    missing_df = pd.DataFrame(missing_report)

    missing_df.to_csv(
        OUTPUT_DIR / "clustering_imputation_report.csv",
        index=False,
    )

    return features


def generate_elbow_plot(scaled_data):
    """Generate the elbow curve for K values from 2 to 10."""
    inertias = []
    cluster_range = range(2, 11)

    for k in cluster_range:
        model = KMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=20,
        )

        model.fit(scaled_data)
        inertias.append(model.inertia_)

    plt.figure(figsize=(9, 5))
    plt.plot(
        list(cluster_range),
        inertias,
        marker="o",
    )

    plt.xticks(list(cluster_range))
    plt.xlabel("Number of Clusters (K)")
    plt.ylabel("Inertia")
    plt.title("KMeans Elbow Method - NIFTY 100")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        REPORT_DIR / "elbow_plot.png",
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    return dict(zip(cluster_range, inertias))


def generate_feature_quality_report(original):
    """Export original feature values and quality flags."""
    columns = [
        "company_id",
        "company_name",
        "broad_sector",
        *FEATURES,
        "roe_percentage",
        "roe_extreme_flag",
        "de_extreme_flag",
        "opm_extreme_flag",
        "roe_master_difference",
    ]

    original[columns].to_csv(
        OUTPUT_DIR / "clustering_feature_quality.csv",
        index=False,
    )


def run_clustering():
    """Run preprocessing, KMeans clustering and export results."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    features, original = prepare_features()

    if len(features) != EXPECTED_COMPANIES:
        raise ValueError(
            f"Expected {EXPECTED_COMPANIES} companies, "
            f"found {len(features)}"
        )

    if features["company_id"].nunique() != EXPECTED_COMPANIES:
        raise ValueError("Duplicate or missing company IDs detected")

    if features["broad_sector"].isna().any():
        raise ValueError("Some companies have no broad-sector mapping")

    generate_feature_quality_report(original)

    # Preserve imputed feature data for Day 37 profiling.
    imputed = impute_by_sector(features)

    audit_columns = [
        "company_id",
        "company_name",
        "broad_sector",
        *FEATURES,
    ]

    imputed[audit_columns].to_csv(
        OUTPUT_DIR / "clustering_feature_data.csv",
        index=False,
    )

    # StandardScaler: zero mean and unit variance.
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(imputed[FEATURES])

    # Elbow analysis.
    inertias = generate_elbow_plot(scaled_data)

    # Final five-cluster model.
    model = KMeans(
        n_clusters=N_CLUSTERS,
        random_state=RANDOM_STATE,
        n_init=20,
    )

    cluster_ids = model.fit_predict(scaled_data)

    # Euclidean distance to assigned centroid.
    distances = np.linalg.norm(
        scaled_data - model.cluster_centers_[cluster_ids],
        axis=1,
    )

    results = pd.DataFrame({
        "company_id": imputed["company_id"],
        "cluster_id": cluster_ids,
        "cluster_name": [
            f"Cluster {cluster_id}"
            for cluster_id in cluster_ids
        ],
        "distance_from_centroid": distances,
    })

    output_path = OUTPUT_DIR / "cluster_labels.csv"

    results.to_csv(output_path, index=False)

    # Print validation summary.
    print("\n========== CLUSTERING RESULTS ==========")

    print(f"Companies clustered: {len(results)}")
    print(f"Unique companies: {results['company_id'].nunique()}")
    print(f"Unique clusters: {results['cluster_id'].nunique()}")

    print("\nCluster distribution:")
    print(
        results.groupby("cluster_id").size().to_string()
    )

    print("\nFeature missingness before imputation:")
    print(original[FEATURES].isna().sum().to_string())

    print("\nExtreme-value flags:")
    print(
        original[
            [
                "roe_extreme_flag",
                "de_extreme_flag",
                "opm_extreme_flag",
            ]
        ].sum().to_string()
    )

    print("\nElbow inertia:")
    for k, inertia in inertias.items():
        print(f"K={k}: {inertia:.2f}")

    print("\nGenerated files:")
    print(output_path)
    print(OUTPUT_DIR / "clustering_feature_data.csv")
    print(OUTPUT_DIR / "clustering_feature_quality.csv")
    print(OUTPUT_DIR / "clustering_imputation_report.csv")
    print(REPORT_DIR / "elbow_plot.png")

    # Final assertions.
    assert len(results) == EXPECTED_COMPANIES
    assert results["company_id"].nunique() == EXPECTED_COMPANIES
    assert results["cluster_id"].nunique() == N_CLUSTERS
    assert results["cluster_id"].between(0, 4).all()
    assert results["distance_from_centroid"].notna().all()

    print("\nDAY 36 CLUSTERING VALIDATION PASSED")


if __name__ == "__main__":
    run_clustering()
