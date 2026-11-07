"""
Sprint 5 - Day 35
Generate sector reports and the NIFTY 100 portfolio summary.

Run from project root:
    python src/reports/final_reports.py

Outputs:
    reports/sector/<SECTOR>_sector_report.pdf
    reports/portfolio/portfolio_summary.pdf
    output/final_report_validation.txt
"""

import re
import sqlite3
import warnings
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

warnings.filterwarnings("ignore", category=UserWarning)

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "nifty100.db"
SECTOR_DIR = ROOT / "reports" / "sector"
PORTFOLIO_DIR = ROOT / "reports" / "portfolio"
CHART_DIR = ROOT / "reports" / "radar_charts"
OUTPUT_DIR = ROOT / "output"

for folder in (SECTOR_DIR, PORTFOLIO_DIR, CHART_DIR, OUTPUT_DIR):
    folder.mkdir(parents=True, exist_ok=True)

NAVY = colors.HexColor("#14243A")
BLUE = colors.HexColor("#2463A6")
LIGHT_BLUE = colors.HexColor("#EAF1F8")
GREY = colors.HexColor("#5B6573")
LIGHT_GREY = colors.HexColor("#F2F4F7")
GREEN = colors.HexColor("#237A57")
RED = colors.HexColor("#B54747")


def clean_filename(value):
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value).strip())
    return value.strip("_") or "sector"


def safe_num(value, digits=2):
    try:
        if pd.isna(value):
            return "N/A"
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "N/A"


def load_table(conn, table):
    try:
        return pd.read_sql_query(f'SELECT * FROM "{table}"', conn)
    except (sqlite3.Error, pd.errors.DatabaseError):
        return pd.DataFrame()


def latest_per_company(df):
    if df.empty or "company_id" not in df.columns:
        return df.copy()
    if "year" in df.columns:
        df = df.sort_values(["company_id", "year"])
    return df.groupby("company_id", as_index=False).tail(1).copy()


def first_existing(df, names):
    for name in names:
        if name in df.columns:
            return name
    return None


def build_data():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    companies = load_table(conn, "companies")
    sectors = load_table(conn, "sectors")
    ratios = load_table(conn, "financial_ratios")
    market = load_table(conn, "market_cap")
    pnl = load_table(conn, "profitandloss")
    cash = load_table(conn, "cashflow")
    conn.close()

    required = {"id", "company_name"}
    if not required.issubset(companies.columns):
        raise ValueError("companies table must contain id and company_name")
    if not {"company_id", "broad_sector"}.issubset(sectors.columns):
        raise ValueError("sectors table must contain company_id and broad_sector")

    base = companies[["id", "company_name"]].rename(columns={"id": "company_id"})
    sector_cols = ["company_id", "broad_sector"]
    for optional in ("sub_sector", "index_weight_pct", "market_cap_category"):
        if optional in sectors.columns:
            sector_cols.append(optional)
    base = base.merge(
        sectors[sector_cols].drop_duplicates("company_id"), on="company_id", how="left"
    )

    def attach_latest(source, prefix, keep):
        nonlocal base
        if source.empty or "company_id" not in source.columns:
            return
        latest = latest_per_company(source)
        selected = ["company_id"] + [c for c in keep if c in latest.columns]
        latest = latest[selected].copy()
        rename = {c: f"{prefix}{c}" for c in selected if c != "company_id"}
        base = base.merge(latest.rename(columns=rename), on="company_id", how="left")

    attach_latest(
        ratios,
        "ratio_",
        [
            "year",
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
            "debt_to_equity",
            "interest_coverage",
            "free_cash_flow_cr",
            "cfo_quality_score",
            "fcf_conversion_pct",
        ],
    )
    attach_latest(
        market,
        "market_",
        [
            "year",
            "market_cap_crore",
            "enterprise_value_crore",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct",
        ],
    )
    attach_latest(pnl, "pnl_", ["year", "sales", "net_profit", "operating_profit"])
    attach_latest(
        cash,
        "cash_",
        [
            "year",
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
        ],
    )

    base["broad_sector"] = base["broad_sector"].fillna("Unclassified")
    return base, ratios, pnl, cash


def make_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubtitleCustom",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=12,
            textColor=GREY,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionCustom",
            parent=styles["Heading2"],
            fontSize=11,
            leading=14,
            textColor=BLUE,
            spaceBefore=8,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallCustom",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=10,
            textColor=GREY,
        )
    )
    return styles


STYLES = make_styles()


def make_table(data, widths=None, font_size=7.5):
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("LEADING", (0, 0), (-1, -1), font_size + 2),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6DCE4")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def metric_summary(frame, column):
    if column not in frame.columns:
        return "N/A"
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        return "N/A"
    return safe_num(values.mean())


def save_sector_chart(sector, frame):
    metrics = [
        ("Revenue", "pnl_sales"),
        ("Net profit", "pnl_net_profit"),
    ]
    available = [(label, col) for label, col in metrics if col in frame.columns]
    if not available:
        return None

    fig, ax = plt.subplots(figsize=(7.2, 2.5))
    labels, values = [], []
    for label, col in available:
        vals = pd.to_numeric(frame[col], errors="coerce").dropna()
        if not vals.empty:
            labels.append(label)
            values.append(vals.sum())
    if not values:
        plt.close(fig)
        return None
    ax.bar(labels, values)
    ax.set_title(f"{sector}: latest reported aggregate (₹ crore)", fontsize=10)
    ax.set_ylabel("₹ crore")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    path = CHART_DIR / f"{clean_filename(sector)}_sector_summary.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def generate_sector_report(sector, frame):
    path = SECTOR_DIR / f"{clean_filename(sector)}_sector_report.pdf"
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=13 * mm,
        bottomMargin=13 * mm,
    )
    story = [
        Paragraph(f"{sector} — Sector Intelligence Report", STYLES["ReportTitle"]),
        Paragraph(
            "NIFTY 100 Financial Intelligence Platform | Latest available company-level observations",
            STYLES["SubtitleCustom"],
        ),
    ]

    count = len(frame)
    story.append(Paragraph("Sector Snapshot", STYLES["SectionCustom"]))
    snapshot = [
        ["Metric", "Value", "Metric", "Value"],
        [
            "Companies covered",
            str(count),
            "Avg. ROE (%)",
            metric_summary(frame, "ratio_return_on_equity_pct"),
        ],
        [
            "Avg. net margin (%)",
            metric_summary(frame, "ratio_net_profit_margin_pct"),
            "Avg. operating margin (%)",
            metric_summary(frame, "ratio_operating_profit_margin_pct"),
        ],
        [
            "Avg. P/E",
            metric_summary(frame, "market_pe_ratio"),
            "Avg. debt/equity",
            metric_summary(frame, "ratio_debt_to_equity"),
        ],
        [
            "Avg. interest coverage",
            metric_summary(frame, "ratio_interest_coverage"),
            "Avg. FCF conversion (%)",
            metric_summary(frame, "ratio_fcf_conversion_pct"),
        ],
    ]
    story.append(make_table(snapshot, [42 * mm, 30 * mm, 42 * mm, 30 * mm]))
    story.append(Spacer(1, 5 * mm))

    chart = save_sector_chart(sector, frame)
    if chart:
        story.append(Paragraph("Latest Financial Scale", STYLES["SectionCustom"]))
        story.append(Image(str(chart), width=170 * mm, height=59 * mm))
        story.append(Spacer(1, 2 * mm))

    story.append(Paragraph("Company Coverage", STYLES["SectionCustom"]))
    display_cols = [
        ("company_name", "Company"),
        ("market_market_cap_crore", "Market cap (₹ Cr)"),
        ("ratio_return_on_equity_pct", "ROE (%)"),
        ("ratio_net_profit_margin_pct", "Net margin (%)"),
        ("market_pe_ratio", "P/E"),
    ]
    available = [(col, label) for col, label in display_cols if col in frame.columns]
    rows = [[label for _, label in available]]
    ordered = frame.copy()
    if "market_market_cap_crore" in ordered.columns:
        ordered["market_market_cap_crore"] = pd.to_numeric(
            ordered["market_market_cap_crore"], errors="coerce"
        )
        ordered = ordered.sort_values(
            "market_market_cap_crore", ascending=False, na_position="last"
        )
    for _, row in ordered.head(20).iterrows():
        rows.append(
            [
                str(row[col])[:38] if col == "company_name" else safe_num(row[col])
                for col, _ in available
            ]
        )
    widths = [65 * mm] + ([25 * mm] * (len(available) - 1))
    story.append(make_table(rows, widths, 7))
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            "Methodology: latest available observation per company is used for cross-sectional "
            "metrics. Averages exclude missing values. Figures are database-derived and are not "
            "investment recommendations. Financial-sector ratios require sector-specific interpretation.",
            STYLES["SmallCustom"],
        )
    )
    doc.build(story)
    return path


def generate_portfolio_summary(base):
    path = PORTFOLIO_DIR / "portfolio_summary.pdf"
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=13 * mm,
        bottomMargin=13 * mm,
    )
    story = [
        Paragraph("NIFTY 100 — Portfolio Intelligence Summary", STYLES["ReportTitle"]),
        Paragraph(
            "Sprint 5 consolidated report | Company, sector, valuation and cash-flow overview",
            STYLES["SubtitleCustom"],
        ),
        Paragraph("Portfolio Coverage", STYLES["SectionCustom"]),
    ]

    sectors = (
        base.groupby("broad_sector")["company_id"]
        .nunique()
        .sort_values(ascending=False)
    )
    total_companies = base["company_id"].nunique()
    total_sectors = base.loc[
        base["broad_sector"] != "Unclassified", "broad_sector"
    ].nunique()
    total_mcap = pd.to_numeric(
        base.get("market_market_cap_crore"), errors="coerce"
    ).sum()
    overview = [
        ["Portfolio metric", "Value", "Portfolio metric", "Value"],
        [
            "Companies in master",
            str(total_companies),
            "Distinct sectors",
            str(total_sectors),
        ],
        [
            "Companies with market-cap data",
            str(
                pd.to_numeric(base.get("market_market_cap_crore"), errors="coerce")
                .notna()
                .sum()
            ),
            "Aggregate latest market cap (₹ Cr)",
            safe_num(total_mcap, 0),
        ],
        [
            "Avg. ROE (%)",
            metric_summary(base, "ratio_return_on_equity_pct"),
            "Avg. net margin (%)",
            metric_summary(base, "ratio_net_profit_margin_pct"),
        ],
        [
            "Avg. P/E",
            metric_summary(base, "market_pe_ratio"),
            "Avg. debt/equity",
            metric_summary(base, "ratio_debt_to_equity"),
        ],
    ]
    story.append(make_table(overview, [42 * mm, 35 * mm, 42 * mm, 35 * mm]))
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("Sector Distribution", STYLES["SectionCustom"]))
    sector_rows = [["Sector", "Companies", "Share of covered universe"]]
    for sector, count in sectors.items():
        sector_rows.append(
            [str(sector), str(int(count)), f"{count / total_companies * 100:.1f}%"]
        )
    story.append(make_table(sector_rows, [80 * mm, 35 * mm, 45 * mm]))

    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    sectors.sort_values().plot(kind="barh", ax=ax)
    ax.set_title("NIFTY 100 company coverage by sector", fontsize=10)
    ax.set_xlabel("Number of companies")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    chart_path = CHART_DIR / "portfolio_sector_distribution.png"
    fig.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    story.append(Spacer(1, 4 * mm))
    story.append(Image(str(chart_path), width=165 * mm, height=69 * mm))

    story.append(PageBreak())
    story.append(Paragraph("Portfolio Quality Indicators", STYLES["SectionCustom"]))
    quality_rows = [["Indicator", "Available companies", "Portfolio average"]]
    for label, col in [
        ("Return on equity (%)", "ratio_return_on_equity_pct"),
        ("Return on capital employed (%)", "ratio_return_on_capital_employed_pct"),
        ("Net profit margin (%)", "ratio_net_profit_margin_pct"),
        ("Operating profit margin (%)", "ratio_operating_profit_margin_pct"),
        ("Interest coverage", "ratio_interest_coverage"),
        ("FCF conversion (%)", "ratio_fcf_conversion_pct"),
    ]:
        vals = (
            pd.to_numeric(base[col], errors="coerce").dropna()
            if col in base
            else pd.Series(dtype=float)
        )
        quality_rows.append(
            [label, str(len(vals)), safe_num(vals.mean()) if len(vals) else "N/A"]
        )
    story.append(make_table(quality_rows, [75 * mm, 45 * mm, 40 * mm]))

    story.append(
        Paragraph(
            "Largest Companies by Latest Market Capitalisation", STYLES["SectionCustom"]
        )
    )
    top = base.copy()
    if "market_market_cap_crore" in top.columns:
        top["market_market_cap_crore"] = pd.to_numeric(
            top["market_market_cap_crore"], errors="coerce"
        )
        top = top.sort_values(
            "market_market_cap_crore", ascending=False, na_position="last"
        )
    top_rows = [["Company", "Sector", "Market cap (₹ Cr)", "P/E"]]
    for _, row in top.head(15).iterrows():
        top_rows.append(
            [
                str(row["company_name"])[:35],
                str(row["broad_sector"])[:25],
                safe_num(row.get("market_market_cap_crore"), 0),
                safe_num(row.get("market_pe_ratio")),
            ]
        )
    story.append(make_table(top_rows, [55 * mm, 55 * mm, 30 * mm, 20 * mm], 7))

    story.append(
        Paragraph("Interpretation & Data Limitations", STYLES["SectionCustom"])
    )
    notes = [
        "This report is a quantitative screening summary, not a buy/sell recommendation.",
        "Metrics use the latest available observation per company; reporting periods may differ.",
        "Missing observations are retained as missing and are not treated as zero.",
        (
            "Cash-flow patterns and leverage ratios should be interpreted differently for banks, "
            "insurers and other financial institutions."
        ),
        "The sector universe reflects the distinct sector labels present in the project database.",
    ]
    for note in notes:
        story.append(Paragraph(f"• {note}", STYLES["SmallCustom"]))
        story.append(Spacer(1, 2))
    doc.build(story)
    return path


def main():
    print("=" * 62)
    print("SPRINT 5 - DAY 35: FINAL REPORT GENERATION")
    print("=" * 62)

    base, *_ = build_data()
    sector_names = sorted(
        s for s in base["broad_sector"].dropna().unique() if s != "Unclassified"
    )
    generated = []
    failed = []

    for index, sector in enumerate(sector_names, start=1):
        frame = base[base["broad_sector"] == sector].copy()
        try:
            report_path = generate_sector_report(sector, frame)
            size_kb = report_path.stat().st_size / 1024
            generated.append(report_path)
            print(
                f"[{index}/{len(sector_names)}] {sector}: {len(frame)} companies | {size_kb:.1f} KB"
            )
        except Exception as exc:  # noqa: BLE001
            failed.append((sector, str(exc)))
            print(f"[{index}/{len(sector_names)}] FAILED: {sector} -> {exc}")

    portfolio_path = None
    try:
        portfolio_path = generate_portfolio_summary(base)
        print(
            f"Portfolio summary: {portfolio_path} ({portfolio_path.stat().st_size/1024:.1f} KB)"
        )
    except Exception as exc:  # noqa: BLE001
        failed.append(("PORTFOLIO_SUMMARY", str(exc)))
        print(f"Portfolio summary FAILED: {exc}")

    validation_lines = [
        "SPRINT 5 DAY 35 - FINAL REPORT VALIDATION",
        f"Companies in master: {base['company_id'].nunique()}",
        f"Distinct sectors in database: {len(sector_names)}",
        f"Sector PDFs generated: {len(generated)}",
        f"Sector PDF failures: {len(failed)}",
        f"Portfolio summary generated: {'YES' if portfolio_path else 'NO'}",
        "",
        "SECTOR REPORTS:",
    ]
    for path in generated:
        validation_lines.append(f"{path.name} | {path.stat().st_size/1024:.1f} KB")
    if failed:
        validation_lines += ["", "FAILURES:"] + [
            f"{name}: {error}" for name, error in failed
        ]

    validation_path = OUTPUT_DIR / "final_report_validation.txt"
    validation_path.write_text("\n".join(validation_lines), encoding="utf-8")

    print("-" * 62)
    print(f"Companies: {base['company_id'].nunique()}")
    print(f"Sectors: {len(sector_names)}")
    print(f"Sector PDFs generated: {len(generated)}")
    print(f"Failures: {len(failed)}")
    print(f"Portfolio summary: {'Generated' if portfolio_path else 'FAILED'}")
    print(f"Validation: {validation_path}")
    print("=" * 62)

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
