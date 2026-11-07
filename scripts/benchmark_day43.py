import csv
import json
import sqlite3
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "nifty100.db"
OUTPUT_DIR = ROOT / "output"
REPORT_DIR = ROOT / "reports"

OUTPUT_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

SEQUENTIAL_ITERATIONS = 20
CONCURRENT_WORKERS = 5
CONCURRENT_ITERATIONS = 10

ENDPOINTS = {
    "Health": "/api/v1/health",
    "Company List": "/api/v1/companies",
    "TCS Profile": "/api/v1/companies/TCS",
    "TCS Ratios": "/api/v1/companies/TCS/ratios",
    "Screener": "/api/v1/screener?preset=quality",
    "Sectors": "/api/v1/sectors",
    "Valuation": "/api/v1/valuation/summary?year=2024",
    "Portfolio Stats": "/api/v1/portfolio/stats",
}


def make_request(endpoint):
    start = time.perf_counter()
    status = 0
    error = ""

    try:
        request = urllib.request.Request(
            BASE_URL + endpoint,
            headers={"User-Agent": "NIFTY100-Performance-Benchmark/1.0"},
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
            status = response.status

    except urllib.error.HTTPError as exc:
        status = exc.code
        error = str(exc)

    except Exception as exc:  # noqa: BLE001
        error = str(exc)

    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "latency_ms": round(elapsed_ms, 3),
        "status": status,
        "success": 200 <= status < 300,
        "error": error,
    }


def summarize(results):
    latencies = [r["latency_ms"] for r in results]
    ordered = sorted(latencies)

    p95_index = min(int(len(ordered) * 0.95), len(ordered) - 1)

    return {
        "requests": len(results),
        "successful": sum(r["success"] for r in results),
        "failed": sum(not r["success"] for r in results),
        "avg_ms": round(statistics.mean(latencies), 3),
        "median_ms": round(statistics.median(latencies), 3),
        "p95_ms": round(ordered[p95_index], 3),
        "max_ms": round(max(latencies), 3),
        "min_ms": round(min(latencies), 3),
    }


def benchmark_sequential():
    print("\n[1/3] Running sequential API benchmarks...")
    results = []

    for name, endpoint in ENDPOINTS.items():
        for _ in range(2):
            make_request(endpoint)

        endpoint_results = [
            make_request(endpoint) for _ in range(SEQUENTIAL_ITERATIONS)
        ]

        summary = summarize(endpoint_results)
        summary.update({"endpoint": name, "test_type": "Sequential"})
        results.append(summary)

        print(
            f"{name:18} | Avg: {summary['avg_ms']:8.2f} ms"
            f" | P95: {summary['p95_ms']:8.2f} ms"
            f" | Failed: {summary['failed']}"
        )

    return results


def benchmark_concurrent():
    print("\n[2/3] Running concurrent API benchmarks...")
    results = []

    for name, endpoint in ENDPOINTS.items():
        endpoint_results = []

        with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
            futures = [
                executor.submit(make_request, endpoint)
                for _ in range(CONCURRENT_ITERATIONS)
            ]

            for future in as_completed(futures):
                endpoint_results.append(future.result())

        summary = summarize(endpoint_results)
        summary.update({"endpoint": name, "test_type": "Concurrent"})
        results.append(summary)

        print(
            f"{name:18} | Avg: {summary['avg_ms']:8.2f} ms"
            f" | P95: {summary['p95_ms']:8.2f} ms"
            f" | Failed: {summary['failed']}"
        )

    return results


def benchmark_database():
    print("\n[3/3] Running SQLite benchmarks...")

    queries = {
        "Company Count": ("SELECT COUNT(*) FROM companies", ()),
        "Financial Ratios Count": ("SELECT COUNT(*) FROM financial_ratios", ()),
        "TCS Financial Ratios": (
            "SELECT * FROM financial_ratios WHERE company_id = ?",
            ("TCS",),
        ),
        "Sector Count": ("SELECT COUNT(DISTINCT broad_sector) FROM sectors", ()),
    }

    results = []

    connection = sqlite3.connect(
        f"file:{DB_PATH.as_posix()}?mode=ro",
        uri=True,
    )

    try:
        for name, (query, params) in queries.items():
            timings = []

            for _ in range(100):
                start = time.perf_counter()
                connection.execute(query, params).fetchall()
                timings.append((time.perf_counter() - start) * 1000)

            summary = {
                "query": name,
                "iterations": len(timings),
                "avg_ms": round(statistics.mean(timings), 3),
                "median_ms": round(statistics.median(timings), 3),
                "max_ms": round(max(timings), 3),
            }

            results.append(summary)

            print(f"{name:25} | Avg: {summary['avg_ms']:.3f} ms")

    finally:
        connection.close()

    return results


def main():
    print("=" * 65)
    print("NIFTY 100 FINANCIAL INTELLIGENCE - DAY 43")
    print("API AND DATABASE PERFORMANCE BENCHMARK")
    print("=" * 65)

    health = make_request("/api/v1/health")

    if not health["success"]:
        raise SystemExit("API is unavailable. Start Uvicorn in the first terminal.")

    sequential = benchmark_sequential()
    concurrent = benchmark_concurrent()
    database = benchmark_database()

    all_results = sequential + concurrent

    csv_path = OUTPUT_DIR / "day43_api_benchmark.csv"

    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "endpoint",
                "test_type",
                "requests",
                "successful",
                "failed",
                "avg_ms",
                "median_ms",
                "p95_ms",
                "max_ms",
                "min_ms",
            ],
        )
        writer.writeheader()
        writer.writerows(all_results)

    db_csv_path = OUTPUT_DIR / "day43_database_benchmark.csv"

    with open(db_csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "query",
                "iterations",
                "avg_ms",
                "median_ms",
                "max_ms",
            ],
        )
        writer.writeheader()
        writer.writerows(database)

    report = {
        "project": "NIFTY 100 Financial Intelligence Platform",
        "day": "Sprint 6 - Day 43",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "configuration": {
            "sequential_iterations_per_endpoint": SEQUENTIAL_ITERATIONS,
            "concurrent_workers": CONCURRENT_WORKERS,
            "concurrent_iterations_per_endpoint": CONCURRENT_ITERATIONS,
            "database_iterations_per_query": 100,
        },
        "api_results": all_results,
        "database_results": database,
    }

    json_path = OUTPUT_DIR / "day43_performance_summary.json"

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    total_requests = sum(r["requests"] for r in all_results)
    total_failed = sum(r["failed"] for r in all_results)

    report_lines = [
        "# Day 43 - Performance Benchmark Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Test Configuration",
        f"- Sequential iterations per endpoint: {SEQUENTIAL_ITERATIONS}",
        f"- Concurrent workers: {CONCURRENT_WORKERS}",
        f"- Concurrent requests per endpoint: {CONCURRENT_ITERATIONS}",
        "- SQLite iterations per query: 100",
        "",
        "## API Benchmark Results",
        "| Endpoint | Test | Requests | Avg (ms) | Median (ms) | P95 (ms) | Max (ms) | Failed |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for row in all_results:
        report_lines.append(
            f"| {row['endpoint']} | {row['test_type']} "
            f"| {row['requests']} | {row['avg_ms']} "
            f"| {row['median_ms']} | {row['p95_ms']} "
            f"| {row['max_ms']} | {row['failed']} |"
        )

    report_lines += [
        "",
        "## Database Benchmark Results",
        "| Query | Iterations | Avg (ms) | Median (ms) | Max (ms) |",
        "|---|---:|---:|---:|---:|",
    ]

    for row in database:
        report_lines.append(
            f"| {row['query']} | {row['iterations']} "
            f"| {row['avg_ms']} | {row['median_ms']} "
            f"| {row['max_ms']} |"
        )

    report_lines += [
        "",
        "## Overall Summary",
        f"- Total API benchmark requests: {total_requests}",
        f"- Failed API requests: {total_failed}",
        f"- Successful API requests: {total_requests - total_failed}",
        "",
        (
            "Note: Results are from a local development server. "
            "They are not production capacity or external-network benchmarks."
        ),
        "",
        (
            "Concurrent requests are measured individually; this is a "
            "basic concurrency benchmark, not a full stress test."
        ),
    ]

    report_path = REPORT_DIR / "day43_performance_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print("\n" + "=" * 65)
    print("DAY 43 BENCHMARK COMPLETED")
    print("=" * 65)
    print(f"Total API requests: {total_requests}")
    print(f"Failed API requests: {total_failed}")
    print(f"API CSV: {csv_path}")
    print(f"Database CSV: {db_csv_path}")
    print(f"JSON summary: {json_path}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
