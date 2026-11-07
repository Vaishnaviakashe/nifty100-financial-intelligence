import sqlite3

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.database import DB_PATH


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def db_connection():
    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row
    yield connection
    connection.close()


@pytest.fixture(scope="session")
def sample_ticker(db_connection):
    row = db_connection.execute(
        """
        SELECT c.id
        FROM companies c
        WHERE EXISTS (
            SELECT 1
            FROM sectors s
            WHERE s.company_id = c.id
        )
        ORDER BY c.id
        LIMIT 1
        """
    ).fetchone()

    assert row is not None, "No company found in database"
    return row["id"]


@pytest.fixture(scope="session")
def sample_sector(db_connection):
    row = db_connection.execute(
        """
        SELECT DISTINCT broad_sector
        FROM sectors
        WHERE broad_sector IS NOT NULL
        ORDER BY broad_sector
        LIMIT 1
        """
    ).fetchone()

    assert row is not None, "No sector found in database"
    return row["broad_sector"]


@pytest.fixture(scope="session")
def sample_peer_group(db_connection):
    row = db_connection.execute(
        """
        SELECT peer_group_name
        FROM peer_groups
        WHERE peer_group_name IS NOT NULL
        GROUP BY peer_group_name
        ORDER BY COUNT(*) DESC, peer_group_name
        LIMIT 1
        """
    ).fetchone()

    assert row is not None, "No peer group found in database"
    return row["peer_group_name"]


@pytest.fixture(scope="session")
def sample_peer_company(db_connection):
    row = db_connection.execute(
        """
        SELECT c.id
        FROM companies c
        INNER JOIN peer_groups p ON p.company_id = c.id
        GROUP BY c.id
        ORDER BY COUNT(*) DESC, c.id
        LIMIT 1
        """
    ).fetchone()

    assert row is not None, "No company with peer groups found"
    return row["id"]


@pytest.fixture(scope="session")
def sample_ticker_with_tearsheet(db_connection):
    from src.api.routers.companies import TEARSHEET_DIR

    if not TEARSHEET_DIR.exists():
        pytest.skip("Tearsheet directory does not exist")

    for pdf in sorted(TEARSHEET_DIR.glob("*_tearsheet.pdf")):
        ticker = pdf.name.replace("_tearsheet.pdf", "").upper()

        row = db_connection.execute(
            "SELECT id FROM companies WHERE UPPER(id) = ?",
            (ticker,),
        ).fetchone()

        if row:
            return row["id"]

    pytest.skip("No company tearsheet PDF found")
