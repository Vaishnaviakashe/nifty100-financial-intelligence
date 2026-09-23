# Nifty 100 Financial Intelligence Platform

Production-grade financial intelligence platform for 92 Nifty 100 companies.

## Sprint 1 — Data Foundation

Sprint 1 builds the ETL foundation:

- Excel ingestion
- Data normalization
- Data quality validation
- SQLite database
- ETL unit tests

## Tech Stack

- Python
- Pandas
- NumPy
- SQLite
- OpenPyXL
- Pytest

## Project Structure

- `data/raw/` — core source datasets
- `data/supporting/` — supplementary datasets
- `src/etl/` — ingestion and normalization
- `src/analytics/` — analytics modules
- `tests/` — automated tests
- `db/` — database schema
- `output/` — generated CSV outputs