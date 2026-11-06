
"""Sprint 5 - Two-page Company Financial Tearsheet Generator."""

import sqlite3
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.platypus import Image as PDFImage

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "nifty100.db"
OUTPUT_DIR = ROOT / "reports" / "tearsheets"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NAVY = colors.HexColor("#17365D")
BLUE = colors.HexColor("#DCE6F1")
LIGHT = colors.HexColor("#F3F6FA")
GREY = colors.HexColor("#666666")
GREEN = colors.HexColor("#E2F0D9")
RED = colors.HexColor("#FCE4D6")


def load_table(conn, table, ticker):
    """Load records for one company."""
    return pd.read_sql_query(
        f"SELECT * FROM {table} WHERE company_id = ?",
        conn,
        params=[ticker],
    )


def safe_value(value, suffix=""):
    """Format missing and numeric values safely."""
    if pd.isna(value):
        return "N/A"

    if isinstance(value, (int, float)):
        return f"{value:,.2f}{suffix}"

    return str(value)


def make_table(data, widths, header=True, font_size=8):
    """Create consistently styled PDF tables."""
    table = Table(
        data,
        colWidths=widths,
        repeatRows=1 if header else 0,
        hAlign="LEFT",
    )

    commands = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#222222")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E1F2")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]

    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])

    if len(data) > 1:
        commands.append(
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT])
        )

    table.setStyle(TableStyle(commands))
    return table


def section(title, styles):
    return Paragraph(title, styles["Section"])


def get_pros_cons(ticker):
    """Read generated pros and cons, if available."""
    path = ROOT / "output" / "pros_cons_generated.csv"

    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)
    if "company_id" not in df.columns:
        return pd.DataFrame()

    return df[df["company_id"].astype(str) == ticker].copy()



def generate_financial_charts(ticker, pnl, cashflow):
    """Generate compact financial charts for the two-page tearsheet."""

    chart_dir = ROOT / "reports" / "radar_charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    if not pnl.empty and {"year", "sales", "net_profit"}.issubset(pnl.columns):
        data = pnl.sort_values("year").tail(8).copy()
        data["sales"] = pd.to_numeric(data["sales"], errors="coerce")
        data["net_profit"] = pd.to_numeric(data["net_profit"], errors="coerce")
        data = data.dropna(subset=["sales", "net_profit"])

        if not data.empty:
            fig, ax = plt.subplots(figsize=(7.2, 2.0))
            ax.plot(data["year"].astype(str), data["sales"], marker="o",
                    linewidth=1.8, label="Revenue")
            ax.plot(data["year"].astype(str), data["net_profit"], marker="s",
                    linewidth=1.8, label="Net Profit")
            ax.set_title(f"{ticker} | Revenue and Net Profit", fontsize=10)
            ax.set_ylabel("₹ Crore", fontsize=8)
            ax.tick_params(axis="both", labelsize=7)
            ax.legend(fontsize=7, frameon=False, ncol=2)
            ax.grid(axis="y", alpha=0.25)
            plt.xticks(rotation=25, ha="right")
            fig.tight_layout()
            paths["performance"] = chart_dir / f"{ticker}_performance.png"
            fig.savefig(paths["performance"], dpi=150, bbox_inches="tight")
            plt.close(fig)

    required_cf = {
        "year", "operating_activity", "investing_activity",
        "financing_activity"
    }
    if not cashflow.empty and required_cf.issubset(cashflow.columns):
        data = cashflow.sort_values("year").tail(8).copy()
        for col in ["operating_activity", "investing_activity",
                    "financing_activity"]:
            data[col] = pd.to_numeric(data[col], errors="coerce")
        data = data.dropna(
            subset=["operating_activity", "investing_activity",
                    "financing_activity"]
        )

        if not data.empty:
            fig, ax = plt.subplots(figsize=(7.2, 2.0))
            ax.plot(data["year"].astype(str), data["operating_activity"],
                    marker="o", linewidth=1.6, label="Operating")
            ax.plot(data["year"].astype(str), data["investing_activity"],
                    marker="s", linewidth=1.6, label="Investing")
            ax.plot(data["year"].astype(str), data["financing_activity"],
                    marker="^", linewidth=1.6, label="Financing")
            ax.axhline(0, linewidth=0.8, color="#555555")
            ax.set_title(f"{ticker} | Cash Flow Trends", fontsize=10)
            ax.set_ylabel("₹ Crore", fontsize=8)
            ax.tick_params(axis="both", labelsize=7)
            ax.legend(fontsize=7, frameon=False, ncol=3)
            ax.grid(axis="y", alpha=0.25)
            plt.xticks(rotation=25, ha="right")
            fig.tight_layout()
            paths["cashflow"] = chart_dir / f"{ticker}_cashflow.png"
            fig.savefig(paths["cashflow"], dpi=150, bbox_inches="tight")
            plt.close(fig)

    return paths


def generate_tearsheet(ticker):
    """Generate a two-page financial tearsheet for one company."""

    with sqlite3.connect(DB_PATH) as conn:
        company_df = pd.read_sql_query(
            "SELECT * FROM companies WHERE id = ?",
            conn,
            params=[ticker],
        )

        if company_df.empty:
            raise ValueError(f"Company {ticker} not found in database.")

        company = company_df.iloc[0]

        sector_df = pd.read_sql_query(
            "SELECT * FROM sectors WHERE company_id = ?",
            conn,
            params=[ticker],
        )

        pnl = load_table(conn, "profitandloss", ticker)
        ratios = load_table(conn, "financial_ratios", ticker)
        cashflow = load_table(conn, "cashflow", ticker)
        market = load_table(conn, "market_cap", ticker)
        balance = load_table(conn, "balancesheet", ticker)

    for df in [pnl, ratios, cashflow, market, balance]:
        if not df.empty and "year" in df.columns:
            df.sort_values("year", inplace=True)

    company_name = company.get("company_name", ticker)
    sector = (
        sector_df.iloc[0].get("broad_sector", "N/A")
        if not sector_df.empty else "N/A"
    )
    sub_sector = (
        sector_df.iloc[0].get("sub_sector", "N/A")
        if not sector_df.empty else "N/A"
    )

    latest_ratio = ratios.iloc[-1] if not ratios.empty else {}
    latest_market = market.iloc[-1] if not market.empty else {}
    latest_balance = balance.iloc[-1] if not balance.empty else {}
    latest_cash = cashflow.iloc[-1] if not cashflow.empty else {}

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="MainTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=23,
        textColor=NAVY,
        alignment=TA_LEFT,
        spaceAfter=5,
    ))

    styles.add(ParagraphStyle(
        name="Section",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=NAVY,
        spaceBefore=5,
        spaceAfter=3,
    ))

    styles.add(ParagraphStyle(
        name="Small",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9,
        textColor=GREY,
    ))

    styles.add(ParagraphStyle(
        name="BodySmall",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9,
    ))

    filename = OUTPUT_DIR / f"{ticker}_tearsheet.pdf"

    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=13 * mm,
        bottomMargin=13 * mm,
        title=f"{company_name} Financial Tearsheet",
        author="NIFTY 100 Financial Intelligence Platform",
    )

    story = []
    charts = generate_financial_charts(ticker, pnl, cashflow)

    # --------------------------------------------------
    # PAGE 1 - COMPANY AND FINANCIAL OVERVIEW
    # --------------------------------------------------

    story.append(Paragraph("NIFTY 100 FINANCIAL INTELLIGENCE", styles["Small"]))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(str(company_name), styles["MainTitle"]))

    story.append(Paragraph(
        f"Ticker: {ticker} | Sector: {sector} | "
        f"Sub-sector: {sub_sector}",
        styles["BodySmall"],
    ))

    story.append(Spacer(1, 3 * mm))

    story.append(section("1. Company Financial Snapshot", styles))

    snapshot = [
        ["Metric", "Latest Value", "Metric", "Latest Value"],
        [
            "Market Capitalization",
            safe_value(latest_market.get("market_cap_crore"), " Cr"),
            "Enterprise Value",
            safe_value(latest_market.get("enterprise_value_crore"), " Cr"),
        ],
        [
            "P/E Ratio",
            safe_value(latest_market.get("pe_ratio")),
            "P/B Ratio",
            safe_value(latest_market.get("pb_ratio")),
        ],
        [
            "EV/EBITDA",
            safe_value(latest_market.get("ev_ebitda")),
            "Dividend Yield",
            safe_value(latest_market.get("dividend_yield_pct"), "%"),
        ],
    ]

    story.append(make_table(
        snapshot,
        [39 * mm, 49 * mm, 35 * mm, 57 * mm],
    ))

    story.append(section("2. Financial Performance History", styles))

    if not pnl.empty:
        recent_pnl = pnl.tail(5).sort_values("year", ascending=False)

        data = [["Year", "Sales (Cr)", "Operating Profit (Cr)", "Net Profit (Cr)", "EPS"]]

        for _, row in recent_pnl.iterrows():
            data.append([
                str(row.get("year", "N/A")),
                safe_value(row.get("sales")),
                safe_value(row.get("operating_profit")),
                safe_value(row.get("net_profit")),
                safe_value(row.get("eps")),
            ])

        story.append(make_table(
            data,
            [25 * mm, 37 * mm, 48 * mm, 43 * mm, 27 * mm],
        ))
    else:
        story.append(Paragraph("Profit and loss history unavailable.", styles["Small"]))

    if "performance" in charts:
        story.append(Spacer(1, 2 * mm))
        story.append(PDFImage(
            str(charts["performance"]),
            width=165 * mm,
            height=43 * mm,
        ))

    story.append(section("3. Key Financial Ratios", styles))

    ratio_metrics = [
        ("Net Profit Margin", "net_profit_margin_pct", "%"),
        ("Operating Profit Margin", "operating_profit_margin_pct", "%"),
        ("Return on Equity", "return_on_equity_pct", "%"),
        ("ROCE", "return_on_capital_employed_pct", "%"),
        ("Debt to Equity", "debt_to_equity", ""),
        ("Interest Coverage", "interest_coverage", "x"),
    ]

    ratio_data = [["Ratio", "Value", "Ratio", "Value"]]

    for i in range(0, len(ratio_metrics), 2):
        left = ratio_metrics[i]
        right = ratio_metrics[i + 1]

        ratio_data.append([
            left[0],
            safe_value(latest_ratio.get(left[1]), left[2]),
            right[0],
            safe_value(latest_ratio.get(right[1]), right[2]),
        ])

    story.append(make_table(
        ratio_data,
        [42 * mm, 48 * mm, 42 * mm, 48 * mm],
    ))

    story.append(section("4. Cash Flow Quality", styles))

    cash_data = [
        ["Metric", "Latest Value"],
        ["Cash from Operations", safe_value(latest_cash.get("operating_activity"), " Cr")],
        ["Investing Cash Flow", safe_value(latest_cash.get("investing_activity"), " Cr")],
        ["Financing Cash Flow", safe_value(latest_cash.get("financing_activity"), " Cr")],
        ["Free Cash Flow", safe_value(latest_ratio.get("free_cash_flow_cr"), " Cr")],
        ["CFO Quality Score", safe_value(latest_ratio.get("cfo_quality_score"))],
    ]

    story.append(make_table(
        cash_data,
        [90 * mm, 90 * mm],
    ))

    # --------------------------------------------------
    # PAGE 2 - INVESTMENT INTELLIGENCE
    # --------------------------------------------------

    story.append(PageBreak())

    story.append(Paragraph("INVESTMENT INTELLIGENCE", styles["Small"]))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(str(company_name), styles["MainTitle"]))

    story.append(section("5. Valuation and Balance Sheet", styles))

    balance_data = [
        ["Balance Sheet Metric", "Latest Value"],
        ["Borrowings", safe_value(latest_balance.get("borrowings"), " Cr")],
        ["Reserves", safe_value(latest_balance.get("reserves"), " Cr")],
        ["Fixed Assets", safe_value(latest_balance.get("fixed_assets"), " Cr")],
        ["Total Assets", safe_value(latest_balance.get("total_assets"), " Cr")],
    ]

    story.append(make_table(
        balance_data,
        [90 * mm, 90 * mm],
    ))

    story.append(section("6. Capital Allocation Pattern", styles))

    allocation_path = OUTPUT_DIR / "capital_allocation.csv"

    if allocation_path.exists():
        allocation = pd.read_csv(allocation_path)
        allocation = allocation[
            allocation["company_id"].astype(str) == ticker
        ].sort_values("year")

        if not allocation.empty:
            latest_allocation = allocation.iloc[-1]

            story.append(Paragraph(
                f"<b>Latest Pattern:</b> {latest_allocation['pattern_label']}",
                styles["BodySmall"],
            ))

            pattern_counts = allocation["pattern_label"].value_counts()

            allocation_data = [["Pattern", "Historical Years"]]

            for pattern, count in pattern_counts.items():
                allocation_data.append([pattern, str(count)])

            story.append(make_table(
                allocation_data,
                [90 * mm, 90 * mm],
            ))
        else:
            story.append(Paragraph(
                "No historical capital allocation records available.",
                styles["Small"],
            ))

    if "cashflow" in charts:
        story.append(Spacer(1, 2 * mm))
        story.append(PDFImage(
            str(charts["cashflow"]),
            width=165 * mm,
            height=40 * mm,
        ))

    story.append(section("7. Generated Pros and Cons", styles))

    pros_cons = get_pros_cons(ticker)

    if not pros_cons.empty:
        # Actual generated CSV schema: company_id, type, rule_id, text, confidence_pct
        required_cols = {"type", "text", "confidence_pct"}
        if required_cols.issubset(pros_cons.columns):
            ordered = pros_cons.sort_values(
                "confidence_pct", ascending=False
            ).head(8)

            for _, row in ordered.iterrows():
                signal_type = escape(str(row.get("type", "Signal")).title())
                signal_text = escape(str(row.get("text", "")))
                confidence = safe_value(row.get("confidence_pct"), "%")

                story.append(Paragraph(
                    f"<b>{signal_type}:</b> {signal_text} "
                    f"<font color='#666666'>(Confidence: {confidence})</font>",
                    styles["BodySmall"],
                ))
                story.append(Spacer(1, 2))
        else:
            story.append(Paragraph(
                "Pros/cons file columns do not match the expected schema.",
                styles["Small"],
            ))
    else:
        story.append(Paragraph(
            "No generated pros and cons available for this company.",
            styles["Small"],
        ))

    story.append(section("8. Risk Indicators and Observations", styles))

    distress_flag = "Not evaluated"
    deleveraging_flag = "Not evaluated"

    intelligence_path = OUTPUT_DIR / "cashflow_intelligence.xlsx"

    if intelligence_path.exists():
        intelligence = pd.read_excel(intelligence_path)
        company_data = intelligence[
            intelligence["company_id"].astype(str) == ticker
        ]

        if not company_data.empty:
            item = company_data.iloc[0]

            if pd.notna(item.get("distress_flag")):
                distress_flag = (
                    "Yes" if item["distress_flag"] else "No"
                )

            if pd.notna(item.get("deleveraging_flag")):
                deleveraging_flag = (
                    "Yes" if item["deleveraging_flag"] else "No"
                )

    risk_data = [
        ["Indicator", "Result"],
        ["Cash Flow Distress Screening", distress_flag],
        ["Deleveraging Screening", deleveraging_flag],
        ["Data Coverage", f"{len(pnl)} P&L records; {len(cashflow)} cash-flow records"],
    ]

    story.append(make_table(
        risk_data,
        [90 * mm, 90 * mm],
    ))

    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph(
        "Disclaimer: This tearsheet is generated from historical financial "
        "data and rule-based analytical signals. It is for research and "
        "educational purposes only and is not investment advice.",
        styles["Small"],
    ))

    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D9E1F2"))
        canvas.line(15 * mm, 10 * mm, 195 * mm, 10 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GREY)
        canvas.drawString(
            15 * mm, 6 * mm,
            "NIFTY 100 Financial Intelligence Platform",
        )
        canvas.drawRightString(
            195 * mm, 6 * mm,
            f"Page {document.page}",
        )
        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
    )

    print(f"Generated: {filename}")
    print(f"Company: {company_name} ({ticker})")
    print(f"P&L records: {len(pnl)}")
    print(f"Cash flow records: {len(cashflow)}")


if __name__ == "__main__":
    ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "TCS"
    generate_tearsheet(ticker)
