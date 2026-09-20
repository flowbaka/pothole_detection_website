from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
    # This checks the API only; database/model checks come later.
    return {"status": "ok"}


@app.get("/capture", response_class=FileResponse, include_in_schema=False)
def capture_page() -> FileResponse:
    # Refresh the experiment page when testing changes on a phone.
    return FileResponse(STATIC_DIR / "capture.html", headers={"Cache-Control": "no-store"})
