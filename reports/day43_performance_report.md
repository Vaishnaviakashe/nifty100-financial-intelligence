# Day 43 - Performance Benchmark Report

Generated: 2026-11-07T08:05:34

## Test Configuration
- Sequential iterations per endpoint: 20
- Concurrent workers: 5
- Concurrent requests per endpoint: 10
- SQLite iterations per query: 100

## API Benchmark Results
| Endpoint | Test | Requests | Avg (ms) | Median (ms) | P95 (ms) | Max (ms) | Failed |
|---|---|---:|---:|---:|---:|---:|---:|
| Health | Sequential | 20 | 12.415 | 7.562 | 36.144 | 36.144 | 0 |
| Company List | Sequential | 20 | 16.364 | 13.664 | 33.66 | 33.66 | 0 |
| TCS Profile | Sequential | 20 | 10.685 | 8.081 | 37.948 | 37.948 | 0 |
| TCS Ratios | Sequential | 20 | 11.134 | 9.941 | 23.743 | 23.743 | 0 |
| Screener | Sequential | 20 | 107.089 | 57.365 | 409.596 | 409.596 | 0 |
| Sectors | Sequential | 20 | 11.401 | 8.02 | 29.62 | 29.62 | 0 |
| Valuation | Sequential | 20 | 11.886 | 9.252 | 34.316 | 34.316 | 0 |
| Portfolio Stats | Sequential | 20 | 16.761 | 14.365 | 37.497 | 37.497 | 0 |
| Health | Concurrent | 10 | 43.59 | 48.352 | 88.035 | 88.035 | 0 |
| Company List | Concurrent | 10 | 78.566 | 68.803 | 134.228 | 134.228 | 0 |
| TCS Profile | Concurrent | 10 | 27.234 | 25.386 | 43.594 | 43.594 | 0 |
| TCS Ratios | Concurrent | 10 | 31.604 | 29.106 | 47.642 | 47.642 | 0 |
| Screener | Concurrent | 10 | 49.239 | 47.707 | 64.506 | 64.506 | 0 |
| Sectors | Concurrent | 10 | 15.521 | 13.396 | 29.341 | 29.341 | 0 |
| Valuation | Concurrent | 10 | 112.889 | 114.402 | 160.464 | 160.464 | 0 |
| Portfolio Stats | Concurrent | 10 | 87.391 | 90.013 | 159.412 | 159.412 | 0 |

## Database Benchmark Results
| Query | Iterations | Avg (ms) | Median (ms) | Max (ms) |
|---|---:|---:|---:|---:|
| Company Count | 100 | 0.026 | 0.016 | 0.693 |
| Financial Ratios Count | 100 | 0.026 | 0.022 | 0.2 |
| TCS Financial Ratios | 100 | 0.066 | 0.053 | 0.744 |
| Sector Count | 100 | 0.057 | 0.026 | 0.886 |

## Overall Summary
- Total API benchmark requests: 240
- Failed API requests: 0
- Successful API requests: 240

Note: Results are from a local development server. They are not production capacity or external-network benchmarks.

Concurrent requests are measured individually; this is a basic concurrency benchmark, not a full stress test.