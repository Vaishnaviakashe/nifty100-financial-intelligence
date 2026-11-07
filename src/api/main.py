
import logging
import time
from src.api.routers.companies import router as companies_router

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers.screener import router as screener_router
from src.api.routers.sectors import router as sectors_router
from src.api.routers.peers import router as peers_router
from src.api.routers.valuation import router as valuation_router
from src.api.routers.portfolio import router as portfolio_router
from src.api.routers.documents import router as documents_router

from src.api.database import (
    get_connection,
    get_table_row_counts,
)


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "NIFTY 100 Financial Intelligence API"
VERSION = "1.0.0"

START_TIME = time.time()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("nifty100_api")


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting NIFTY 100 API...")

    # Verify database connectivity during startup.
    with get_connection() as connection:
        connection.execute("SELECT 1").fetchone()

    logger.info("SQLite database connection successful.")

    yield

    logger.info("Shutting down NIFTY 100 API...")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    description=(
        "REST API for NIFTY 100 financial analytics, "
        "screening, valuation and portfolio intelligence."
    ),
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


app.include_router(companies_router)
app.include_router(screener_router)
app.include_router(sectors_router)
app.include_router(peers_router)
app.include_router(valuation_router)
app.include_router(portfolio_router)
app.include_router(documents_router)

# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST LOGGING MIDDLEWARE
# ============================================================

@app.middleware("http")
async def request_logging(request: Request, call_next):

    start = time.time()

    response = await call_next(request)

    duration = (time.time() - start) * 1000

    logger.info(
        "%s %s | Status: %s | %.2f ms",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    return response


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/", tags=["General"])
def root():

    return {
        "message": "Welcome to NIFTY 100 Financial Intelligence API",
        "version": VERSION,
        "documentation": "/docs",
        "health": "/api/v1/health",
    }


# ============================================================
# HEALTH ENDPOINT
# ============================================================

@app.get("/api/v1/health", tags=["Health"])
def health_check():

    try:

        with get_connection() as connection:
            connection.execute("SELECT 1").fetchone()

        row_counts = get_table_row_counts()

        return {
            "status": "healthy",
            "application": APP_NAME,
            "version": VERSION,
            "database": "connected",
            "uptime_seconds": round(
                time.time() - START_TIME, 2
            ),
            "total_tables": len(row_counts),
            "table_row_counts": row_counts,
            "timestamp": time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

    except Exception as error:

        logger.exception("Health check failed")

        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(error),
        }


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
