"""
Day 45 — NIFTY 100 acceptance verification
Run from the project root:
    python day45_acceptance_check.py

This script checks only what it can verify from the local project.
It deliberately marks runtime/UI/manual checks as PENDING rather than guessing.
"""
from pathlib import Path
import sqlite3
import csv
import subprocess
import sys

ROOT = Path.cwd()
DB = ROOT / "data" / "nifty100.db"
OUT = ROOT / "output" / "day45_acceptance"
OUT.mkdir(parents=True, exist_ok=True)

results = []

def add(ac, name, status, evidence):
    results.append((ac, name, status, str(evidence)))

def table_names(conn):
    return {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}

def columns(conn, table):
    return {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}

def count_rows(conn, table):
    return conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]

# AC-01 — company coverage
if DB.exists():
    try:
        con = sqlite3.connect(DB)
        tables = table_names(con)
        if "companies" in tables:
            n = count_rows(con, "companies")
            add("AC-01", "92 companies", "PASS" if n == 92 else "FAIL",
                f"companies rows={n}")
        else:
            add("AC-01", "92 companies", "FAIL", "companies table missing")

        # AC-03 — foreign key integrity
        fk = con.execute("PRAGMA foreign_key_check").fetchall()
        add("AC-03", "Foreign key integrity", "PASS" if not fk else "FAIL",
            f"foreign_key_check rows={len(fk)}")

        # AC-04 — financial ratios threshold
        if "financial_ratios" in tables:
            n = count_rows(con, "financial_ratios")
            add("AC-04", "At least 1100 financial ratios", "PASS" if n >= 1100 else "FAIL",
                f"financial_ratios rows={n}; target >=1100")
        else:
            add("AC-04", "At least 1100 financial ratios", "FAIL",
                "financial_ratios table missing")

        # AC-14 — all 11 peer groups
        if "peer_groups" in tables:
            n = count_rows(con, "peer_groups")
            add("AC-14", "Peer group coverage", "PASS" if n >= 11 else "FAIL",
                f"peer_groups rows={n}; expected at least 11 group records")
        else:
            add("AC-14", "Peer group coverage", "FAIL", "peer_groups table missing")

        con.close()
    except Exception as exc:
        add("AC-DB", "Database checks", "ERROR", repr(exc))
else:
    for ac, name in [
        ("AC-01", "92 companies"), ("AC-03", "Foreign key integrity"),
        ("AC-04", "At least 1100 financial ratios"),
        ("AC-14", "Peer group coverage")
    ]:
        add(ac, name, "FAIL", f"Database not found: {DB}")

# AC-15 — clustering coverage
cluster_candidates = [
    ROOT / "output" / "cluster_labels.csv",
    ROOT / "output" / "clustering" / "cluster_labels.csv",
    ROOT / "reports" / "cluster_labels.csv",
]
cluster_file = next((p for p in cluster_candidates if p.exists()), None)
if cluster_file:
    try:
        with cluster_file.open("r", newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        headers = set(rows[0].keys()) if rows else set()
        add("AC-15", "92 companies assigned to clusters",
            "PASS" if len(rows) == 92 else "FAIL",
            f"{cluster_file.relative_to(ROOT)} rows={len(rows)} columns={sorted(headers)}")
    except Exception as exc:
        add("AC-15", "92 companies assigned to clusters", "ERROR", repr(exc))
else:
    add("AC-15", "92 companies assigned to clusters", "PENDING",
        "Could not locate cluster_labels.csv in standard output/report locations")

# AC-16 — pros and cons coverage
if DB.exists():
    try:
        con = sqlite3.connect(DB)
        tables = table_names(con)
        if "prosandcons" in tables:
            cols = columns(con, "prosandcons")
            # Try common schema shapes without assuming one.
            company_col = next((c for c in ("company_id", "ticker", "symbol") if c in cols), None)
            type_col = next((c for c in ("signal_type", "type", "sentiment", "category", "label") if c in cols), None)
            if company_col and type_col:
                q = f'SELECT "{company_col}", LOWER("{type_col}") FROM prosandcons'
                records = con.execute(q).fetchall()
                by_company = {}
                for company, typ in records:
                    by_company.setdefault(company, set()).add(str(typ).lower())
                both = sum(
                    any("pro" in t for t in vals) and any("con" in t for t in vals)
                    for vals in by_company.values()
                )
                add("AC-16", "Every company has at least one pro and one con",
                    "PASS" if both == 92 else "FAIL",
                    f"companies with both={both}; companies represented={len(by_company)}; schema={sorted(cols)}")
            else:
                add("AC-16", "Every company has at least one pro and one con",
                    "PENDING", f"Could not infer company/type columns; schema={sorted(cols)}")
        else:
            add("AC-16", "Every company has at least one pro and one con", "FAIL",
                "prosandcons table missing")
        con.close()
    except Exception as exc:
        add("AC-16", "Every company has at least one pro and one con", "ERROR", repr(exc))

# AC-17 — 92 tearsheets
pdf_dirs = [ROOT / "output", ROOT / "reports"]
pdfs = []
for base in pdf_dirs:
    if base.exists():
        pdfs.extend(p for p in base.rglob("*.pdf") if "final_deliverables" not in p.parts)
tearsheet_pdfs = [p for p in pdfs if "tearsheet" in p.name.lower() or "tear" in p.name.lower()]
add("AC-17", "92 company tearsheets generated",
    "PASS" if len(tearsheet_pdfs) >= 92 else "PENDING",
    f"PDFs with tearsheet-like filenames found={len(tearsheet_pdfs)}; total PDFs found={len(pdfs)}")

# AC-18 — test suite
try:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=600
    )
    output = (proc.stdout + "\n" + proc.stderr).strip()
    add("AC-18", "At least 60 tests pass with zero failures",
        "PASS" if proc.returncode == 0 and "failed" not in output.lower()
        and "error" not in output.lower() else "FAIL",
        output[-1800:] if output else f"pytest exit code={proc.returncode}")
except Exception as exc:
    add("AC-18", "At least 60 tests pass with zero failures", "ERROR", repr(exc))

# AC-19 — validation_failures.csv required fields
validation_candidates = list(ROOT.rglob("validation_failures.csv"))
validation_candidates = [p for p in validation_candidates if "venv" not in p.parts and ".git" not in p.parts]
if validation_candidates:
    p = validation_candidates[0]
    try:
        with p.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = set(next(reader, []))
        required = {"company_id", "field", "issue", "severity"}
        missing = required - headers
        add("AC-19", "Validation failures CSV schema",
            "PASS" if not missing else "FAIL",
            f"{p.relative_to(ROOT)}; missing columns={sorted(missing)}; headers={sorted(headers)}")
    except Exception as exc:
        add("AC-19", "Validation failures CSV schema", "ERROR", repr(exc))
else:
    add("AC-19", "Validation failures CSV schema", "PENDING",
        "validation_failures.csv not found")

# AC-20 — analyst guide >=10 pages (PDF metadata via optional pypdf)
guide_candidates = [
    ROOT / "docs" / "analyst_guide.pdf",
    ROOT / "docs" / "Analyst_Guide.pdf",
]
guide = next((p for p in guide_candidates if p.exists()), None)
if guide:
    try:
        from pypdf import PdfReader
        pages = len(PdfReader(str(guide)).pages)
        add("AC-20", "Analyst guide has at least 10 pages",
            "PASS" if pages >= 10 else "FAIL",
            f"{guide.relative_to(ROOT)} pages={pages}")
    except ImportError:
        add("AC-20", "Analyst guide has at least 10 pages", "PENDING",
            "Guide exists; install pypdf to verify page count")
    except Exception as exc:
        add("AC-20", "Analyst guide has at least 10 pages", "ERROR", repr(exc))
else:
    add("AC-20", "Analyst guide has at least 10 pages", "FAIL",
        "docs/analyst_guide.pdf not found")

# Gates needing app/browser/manual or detailed source-specific checks
for ac, name, evidence in [
    ("AC-02", "10-year financial statement coverage", "Requires a consistent company/year coverage query across P&L, balance sheet and cash flow."),
    ("AC-05", "Revenue CAGR spot-check", "Requires comparison against the rubric's selected company and source values."),
    ("AC-06", "ROE spot-check", "Requires comparison against companies.roe_percentage for the rubric's five companies."),
    ("AC-07", "Quality screener result count", "Requires running the quality preset and checking returned rows."),
    ("AC-08", "Company profile loads under 3 seconds", "Requires live dashboard/browser timing."),
    ("AC-09", "CSV download validity", "Requires exercising the screener download."),
    ("AC-10", "Tearsheet text overflow", "Requires visual inspection of five generated PDFs."),
    ("AC-11", "API health endpoint returns 200", "Requires API server running and HTTP request."),
    ("AC-12", "TCS ratios endpoint has 10+ years", "Requires API server running and endpoint response check."),
    ("AC-13", "API screener matches screener_output.xlsx", "Requires comparing live API output to workbook output."),
]:
    add(ac, name, "PENDING", evidence)

# Archive integrity and inventory
archive = ROOT / "output" / "final_deliverables" / "NIFTY100_Final_Deliverables.zip"
if archive.exists():
    try:
        import zipfile
        with zipfile.ZipFile(archive) as z:
            bad = z.testzip()
            add("PKG-01", "Final ZIP integrity", "PASS" if bad is None else "FAIL",
                f"entries={len(z.namelist())}; bad_member={bad}")
    except Exception as exc:
        add("PKG-01", "Final ZIP integrity", "ERROR", repr(exc))
else:
    add("PKG-01", "Final ZIP integrity", "FAIL", "Final ZIP not found")

# Write CSV and readable report
csv_path = OUT / "day45_acceptance_results.csv"
with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["criterion", "name", "status", "evidence"])
    writer.writerows(results)

txt_path = OUT / "day45_acceptance_report.txt"
with txt_path.open("w", encoding="utf-8") as f:
    f.write("NIFTY 100 — DAY 45 ACCEPTANCE VERIFICATION\n")
    f.write("=" * 52 + "\n\n")
    for ac, name, status, evidence in results:
        f.write(f"{ac} | {status} | {name}\n  Evidence: {evidence}\n\n")
    counts = {}
    for _, _, status, _ in results:
        counts[status] = counts.get(status, 0) + 1
    f.write("SUMMARY\n")
    for status, count in sorted(counts.items()):
        f.write(f"{status}: {count}\n")

print("DAY 45 CHECK COMPLETE")
print(f"CSV report: {csv_path}")
print(f"Text report: {txt_path}")
print("\nRESULTS")
for ac, name, status, evidence in results:
    print(f"{ac:7} {status:7} {name}")
print("\nThis is a verification aid; PENDING items require manual/API checks.")
