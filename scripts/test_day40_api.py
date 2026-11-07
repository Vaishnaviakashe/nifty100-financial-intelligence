import sqlite3

import requests

BASE = "http://127.0.0.1:8000/api/v1"
DB = "data/nifty100.db"

# Get real sector and peer group names from the database.
with sqlite3.connect(DB) as conn:
    sector = conn.execute("""
        SELECT broad_sector
        FROM sectors
        LIMIT 1
        """).fetchone()[0]

    peer = conn.execute("""
        SELECT peer_group_name
        FROM peer_groups
        LIMIT 1
        """).fetchone()[0]

    peer_company = conn.execute("""
        SELECT company_id
        FROM peer_groups
        LIMIT 1
        """).fetchone()[0]

tests = [
    ("Screener", f"{BASE}/screener?preset=quality"),
    ("Sectors", f"{BASE}/sectors"),
    ("Sector companies", f"{BASE}/sectors/{sector}/companies"),
    ("Peer group", f"{BASE}/peers/{peer}"),
    (
        "Peer comparison",
        f"{BASE}/companies/{peer_company}/peers/compare",
    ),
    ("Market cap", f"{BASE}/market-cap/TCS"),
    ("Valuation summary", f"{BASE}/valuation/summary?year=2024"),
    ("Portfolio stats", f"{BASE}/portfolio/stats"),
    ("Company documents", f"{BASE}/companies/ABB/documents"),
]

print("\n========== DAY 40 API TESTS ==========")

failed = []

for name, url in tests:
    try:
        response = requests.get(url, timeout=30)

        passed = response.status_code == 200

        print(
            f"{name:22} | HTTP {response.status_code} | "
            f"{'PASS' if passed else 'FAIL'}"
        )

        if not passed:
            print(response.text[:1000])
            failed.append(name)

    except requests.RequestException as error:
        print(f"{name:22} | ERROR | {error}")
        failed.append(name)

print("\nFailed tests:", failed)

if not failed:
    print("\nALL DAY 40 API TESTS PASSED")
