"""Generate all NIFTY 100 company tearsheets."""

import sqlite3
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.reports.tearsheet import generate_tearsheet

DB_PATH = ROOT / "data" / "nifty100.db"
OUTPUT_DIR = ROOT / "reports" / "tearsheets"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    companies = conn.execute(
        "SELECT id FROM companies ORDER BY id"
    ).fetchall()

    conn.close()

    successful = []
    failed = []

    print("=" * 55)
    print("SPRINT 5 - BATCH TEARSHEET GENERATION")
    print("=" * 55)

    for index, (ticker,) in enumerate(companies, start=1):
        try:
            generate_tearsheet(ticker)

            pdf_path = OUTPUT_DIR / f"{ticker}_tearsheet.pdf"

            if not pdf_path.exists():
                raise FileNotFoundError("PDF was not generated")

            reader = PdfReader(str(pdf_path))
            pages = len(reader.pages)
            size_kb = pdf_path.stat().st_size / 1024

            successful.append({
                "ticker": ticker,
                "pages": pages,
                "size_kb": round(size_kb, 2)
            })

            print(
                f"[{index}/{len(companies)}] "
                f"{ticker}: {pages} pages, {size_kb:.2f} KB"
            )

        except Exception as error:
            failed.append((ticker, str(error)))
            print(f"[{index}/{len(companies)}] FAILED: {ticker} - {error}")

    print("\n" + "=" * 55)
    print("BATCH GENERATION SUMMARY")
    print("=" * 55)

    print(f"Total companies : {len(companies)}")
    print(f"Generated       : {len(successful)}")
    print(f"Failed          : {len(failed)}")

    two_page = sum(x["pages"] == 2 for x in successful)
    under_30kb = sum(x["size_kb"] < 30 for x in successful)

    print(f"Exactly 2 pages : {two_page}")
    print(f"Below 30 KB     : {under_30kb}")

    if failed:
        print("\nFAILED COMPANIES:")
        for ticker, error in failed:
            print(ticker, "-", error)

    print("\nAll generated PDFs are saved in:")
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()