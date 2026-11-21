"""FastAPI application for the local Spotipyt service.

Run with::

    poetry run uvicorn src.api.server:app --reload
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import downloads, playlists, stats, tracks

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = PROJECT_ROOT / "static"

app = FastAPI(
    title="Spotipyt",
    description="A local service to mirror your Spotify playlists and download them.",
    version="2.0.0",
)

app.include_router(playlists.router)
app.include_router(tracks.router)
app.include_router(downloads.router)
app.include_router(stats.router)

# Resolved from the file location rather than the process cwd, and created if
# missing: the previous `StaticFiles(directory="static")` blew up at import time
# because the directory did not exist.
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="frontend not built yet")
    return FileResponse(index_file)

