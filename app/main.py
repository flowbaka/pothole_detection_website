from pathlib import Path

from fastapi import FastAPI, HTTPException
import psycopg
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import DatabaseConfigError, check_database

# This object receives requests from the future phone page and public map.
app = FastAPI(
    title="Pothole Reporting API",
    description="Backend foundation for the Nepal pothole reporting FYP.",
    version="0.1.0",
)

# Resolve assets relative to this file, independent of the terminal's folder.
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {"message": "Pothole Reporting API is running"}


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    # This checks the API process; /health/database checks PostgreSQL separately.
    return {"status": "ok"}


@app.get("/health/database", tags=["System"])
def database_health() -> dict[str, str]:
    try:
        check_database()
    except (DatabaseConfigError, OSError):
        raise HTTPException(status_code=503, detail="Database is not configured. Run the local database setup.") from None
    except psycopg.Error:
        # Driver errors can include connection details. Do not expose or log them.
        raise HTTPException(status_code=503, detail="Database is unavailable. Check the local connection settings and PostgreSQL service.") from None
    return {"status": "ok", "database": "connected"}


@app.get("/capture", response_class=FileResponse, include_in_schema=False)
def capture_page() -> FileResponse:
    # Refresh the experiment page when testing changes on a phone.
    return FileResponse(STATIC_DIR / "capture.html", headers={"Cache-Control": "no-store"})
