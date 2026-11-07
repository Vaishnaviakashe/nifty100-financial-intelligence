import csv
import sqlite3
from pathlib import Path

DB_PATH = Path("data/nifty100.db")
OUTPUT_PATH = Path("output/sector_roce_notes.csv")

FINANCIAL_COMPANIES = {
    "AXISBANK",
    "BANKBARODA",
    "CANBK",
    "HDFCBANK",
    "ICICIBANK",
    "INDUSINDBK",
    "KOTAKBANK",
    "PNB",
    "SBIN",
    "BAJAJFINSV",
    "BAJFINANCE",
    "CHOLAFIN",
    "IRFC",
    "JIOFIN",
    "PFC",
    "RECLTD",
    "SHRIRAMFIN",
}


def main():
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        f.company_id,
        f.year,
        f.return_on_capital_employed_pct AS calculated_roce,
        c.roce_percentage AS source_roce,
        s.sub_sector
    FROM financial_ratios f
    JOIN companies c
        ON f.company_id = c.id
    JOIN sectors s
        ON f.company_id = s.company_id
    WHERE f.company_id IN (
        'AXISBANK','BANKBARODA','CANBK','HDFCBANK',
        'ICICIBANK','INDUSINDBK','KOTAKBANK','PNB','SBIN',
        'BAJAJFINSV','BAJFINANCE','CHOLAFIN','IRFC',
        'JIOFIN','PFC','RECLTD','SHRIRAMFIN'
    )
    AND c.roce_percentage IS NOT NULL
    ORDER BY f.company_id, f.year
    """

    rows = conn.execute(query).fetchall()
    conn.close()

    notes = []

    for company_id, year, calculated, source, sub_sector in rows:

        if calculated is None or source is None:
            continue

        difference = calculated - source

        if abs(difference) > 5:
            status = "Large difference"
        elif abs(difference) > 2:
            status = "Moderate difference"
        else:
            status = "Close"

        notes.append(
            {
                "company_id": company_id,
                "year": year,
                "sub_sector": sub_sector,
                "calculated_roce_pct": round(calculated, 2),
                "source_roce_pct": round(source, 2),
                "difference_pct": round(difference, 2),
                "status": status,
                "note": "Source ROCE differs from year-level calculation; likely methodology/data-basis difference.",
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "company_id",
                "year",
                "sub_sector",
                "calculated_roce_pct",
                "source_roce_pct",
                "difference_pct",
                "status",
                "note",
            ],
        )
        writer.writeheader()
        writer.writerows(notes)

    print("=" * 50)
    print("D13 SECTOR ROCE CROSS-CHECK")
    print("=" * 50)
    print(f"Rows checked : {len(rows)}")
    print(f"Notes saved  : {len(notes)}")
    print(f"Output       : {OUTPUT_PATH}")
    print("=" * 50)


if __name__ == "__main__":
    main()
